from typing import Optional, List, TypeVar, Generic, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from miniflow.database.models import BaseModel
from miniflow.database.enums import Roles
from miniflow.database.crud.base_crud import BaseCRUD


TJunction = TypeVar('TJunction', bound=BaseModel)


class BaseJunctionCRUD(BaseCRUD[TJunction], Generic[TJunction]):
    """
    Base CRUD class for junction/association tables (many-to-many relationships).
    
    Junction tables typically have:
    - user_id: FK to users table
    - {resource}_id: FK to resource table (workflow_id, envar_id, etc.)
    - role: Enum field for access control
    - granted_at: Timestamp
    - granted_by: FK to users table
    
    This class provides common operations for all junction tables.
    """
    
    def __init__(self, model: Type[TJunction], user_field: str, resource_field: str):
        """
        Initialize junction CRUD with field names.
        
        Args:
            model: SQLAlchemy model class
            user_field: Name of user FK field (e.g., 'user_id')
            resource_field: Name of resource FK field (e.g., 'workflow_id', 'envar_id')
        """
        super().__init__(model)
        self.user_field = user_field
        self.resource_field = resource_field
        self.model_fields = {column.name for column in model.__table__.columns}
        self.required_fields = {user_field, resource_field, 'role'}
        self.protected_fields = {'granted_at'}

    def _create(self, session: Session, **kwargs) -> TJunction:
        """Create a new role assignment with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate user_id
        user_id = kwargs.get(self.user_field)
        if user_id:
            kwargs[self.user_field] = validators._validate_id(user_id)
        
        # Validate resource_id
        resource_id = kwargs.get(self.resource_field)
        if resource_id:
            kwargs[self.resource_field] = validators._validate_id(resource_id)
        
        # Validate role
        role = kwargs.get('role')
        if role:
            if isinstance(role, str):
                try:
                    kwargs['role'] = Roles(role)
                except ValueError:
                    raise ValueError(f"Invalid role: {role}")
        
        # Validate granted_by if provided
        granted_by = kwargs.get('granted_by')
        if granted_by:
            kwargs['granted_by'] = validators._validate_id(granted_by)
        
        # Check for existing assignment
        self._validate_assignment_uniqueness(
            session,
            kwargs[self.user_field],
            kwargs[self.resource_field]
        )
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        junction = super()._create(session, **kwargs)
        return junction

    def _update(self, session: Session, record_id: str, **kwargs) -> TJunction:
        """Update role assignment with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Validate role if being updated
        if 'role' in kwargs:
            role = kwargs['role']
            if isinstance(role, str):
                try:
                    kwargs['role'] = Roles(role)
                except ValueError:
                    raise ValueError(f"Invalid role: {role}")
        
        # Validate granted_by if being updated
        if 'granted_by' in kwargs and kwargs['granted_by']:
            kwargs['granted_by'] = validators._validate_id(kwargs['granted_by'])
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        junction = super()._update(session, record_id, **kwargs)
        return junction

    def _validate_assignment_uniqueness(self, session: Session, user_id: str, resource_id: str):
        """Validate that user-resource assignment is unique."""
        existing = session.query(self.model).filter(
            and_(
                getattr(self.model, self.user_field) == user_id,
                getattr(self.model, self.resource_field) == resource_id,
                self.model.is_deleted == False
            )
        ).first()
        
        if existing:
            context = ErrorContext(
                operation='validate_assignment_uniqueness',
                component=self.model_name,
                additional_info={
                    self.user_field: user_id,
                    self.resource_field: resource_id,
                    'existing_id': existing.id
                }
            )
            raise ValidationError(
                f"User already has a role for this {self.resource_field.replace('_id', '')}",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )

    def _get_by_user_and_resource(self, session: Session, user_id: str, resource_id: str) -> Optional[TJunction]:
        """Get role assignment for specific user-resource pair."""
        user_id = validators._validate_id(user_id)
        resource_id = validators._validate_id(resource_id)
        
        junction = session.query(self.model).filter(
            and_(
                getattr(self.model, self.user_field) == user_id,
                getattr(self.model, self.resource_field) == resource_id,
                self.model.is_deleted == False
            )
        ).first()
        
        return junction

    def _check_user_has_role(self, session: Session, user_id: str, resource_id: str, required_role: Roles) -> bool:
        """
        Check if user has a specific role or higher for a resource.
        
        Role hierarchy: OWNER > EDITOR > CONTRIBUTOR > VIEWER
        """
        try:
            junction = self._get_by_user_and_resource(session, user_id, resource_id)
            
            if not junction:
                return False
            
            # Role hierarchy
            role_hierarchy = {
                Roles.OWNER: 4,
                Roles.EDITOR: 3,
                Roles.CONTRIBUTOR: 2,
                Roles.VIEWER: 1
            }
            
            user_role_level = role_hierarchy.get(junction.role, 0)
            required_role_level = role_hierarchy.get(required_role, 99)
            
            return user_role_level >= required_role_level
            
        except Exception:
            # For security, return False on any error
            return False

    def _add_user(self, session: Session, resource_id: str, user_id: str, role: Roles, granted_by: str) -> TJunction:
        """
        Add user to resource with specified role.
        Only OWNER can add users.
        """
        resource_id = validators._validate_id(resource_id)
        user_id = validators._validate_id(user_id)
        granted_by = validators._validate_id(granted_by)
        
        has_permission = self._check_user_has_role(session, granted_by, resource_id, Roles.OWNER)
        
        if not has_permission:
            context = ErrorContext(
                operation='add_user',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, 'granted_by': granted_by}
            )
            raise ValidationError(
                "Only resource owners can add users",
                context=context,
                severity=ErrorSeverity.HIGH
            )
        
        return self._create(
            session,
            **{
                self.user_field: user_id,
                self.resource_field: resource_id,
                'role': role,
                'granted_by': granted_by
            }
        )

    def _remove_user(self, session: Session, resource_id: str, user_id: str, removed_by: str) -> bool:
        """
        Remove user from resource.
        Only OWNER can remove users.
        Cannot remove the last owner.
        """
        resource_id = validators._validate_id(resource_id)
        user_id = validators._validate_id(user_id)
        removed_by = validators._validate_id(removed_by)
        
        has_permission = self._check_user_has_role(session, removed_by, resource_id, Roles.OWNER)
        
        if not has_permission:
            context = ErrorContext(
                operation='remove_user',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, 'removed_by': removed_by}
            )
            raise ValidationError(
                "Only resource owners can remove users",
                context=context,
                severity=ErrorSeverity.HIGH
            )
        
        user_role = self._get_by_user_and_resource(session, user_id, resource_id)
        
        if not user_role:
            context = ErrorContext(
                operation='remove_user',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, self.user_field: user_id}
            )
            raise ValidationError(
                f"User does not have access to this resource",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        if user_role.role == Roles.OWNER:
            owner_count = session.query(self.model).filter(
                and_(
                    getattr(self.model, self.resource_field) == resource_id,
                    self.model.role == Roles.OWNER,
                    self.model.is_deleted == False
                )
            ).count()
            
            if owner_count <= 1:
                context = ErrorContext(
                    operation='remove_user',
                    component=self.model_name,
                    additional_info={self.resource_field: resource_id, self.user_field: user_id}
                )
                raise ValidationError(
                    "Cannot remove the last owner. Transfer ownership first.",
                    context=context,
                    severity=ErrorSeverity.HIGH
                )
        
        self._delete(session, user_role.id)
        return True

    def _update_user_role(self, session: Session, resource_id: str, user_id: str, new_role: Roles, updated_by: str) -> TJunction:
        """
        Update user's role for a resource.
        Only OWNER can update roles.
        Cannot change the last owner's role.
        """
        resource_id = validators._validate_id(resource_id)
        user_id = validators._validate_id(user_id)
        updated_by = validators._validate_id(updated_by)
        
        has_permission = self._check_user_has_role(session, updated_by, resource_id, Roles.OWNER)
        
        if not has_permission:
            context = ErrorContext(
                operation='update_user_role',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, 'updated_by': updated_by}
            )
            raise ValidationError(
                "Only resource owners can update user roles",
                context=context,
                severity=ErrorSeverity.HIGH
            )
        
        user_role = self._get_by_user_and_resource(session, user_id, resource_id)
        
        if not user_role:
            context = ErrorContext(
                operation='update_user_role',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, self.user_field: user_id}
            )
            raise ValidationError(
                f"User does not have access to this resource",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        if user_role.role == Roles.OWNER and new_role != Roles.OWNER:
            owner_count = session.query(self.model).filter(
                and_(
                    getattr(self.model, self.resource_field) == resource_id,
                    self.model.role == Roles.OWNER,
                    self.model.is_deleted == False
                )
            ).count()
            
            if owner_count <= 1:
                context = ErrorContext(
                    operation='update_user_role',
                    component=self.model_name,
                    additional_info={self.resource_field: resource_id, self.user_field: user_id}
                )
                raise ValidationError(
                    "Cannot demote the last owner. Transfer ownership first.",
                    context=context,
                    severity=ErrorSeverity.HIGH
                )
        
        return self._update(session, user_role.id, role=new_role, granted_by=updated_by)

    def _transfer_ownership(self, session: Session, resource_id: str, current_owner_id: str, new_owner_id: str) -> dict:
        """
        Transfer ownership from current owner to new owner.
        Only current OWNER can transfer ownership.
        Current owner becomes EDITOR after transfer.
        """
        resource_id = validators._validate_id(resource_id)
        current_owner_id = validators._validate_id(current_owner_id)
        new_owner_id = validators._validate_id(new_owner_id)
        
        current_owner_role = self._get_by_user_and_resource(session, current_owner_id, resource_id)
        
        if not current_owner_role or current_owner_role.role != Roles.OWNER:
            context = ErrorContext(
                operation='transfer_ownership',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, 'current_owner_id': current_owner_id}
            )
            raise ValidationError(
                f"User is not the owner of this resource",
                context=context,
                severity=ErrorSeverity.HIGH
            )
        
        self._update(session, current_owner_role.id, role=Roles.EDITOR, granted_by=current_owner_id)
        
        new_owner_role = self._get_by_user_and_resource(session, new_owner_id, resource_id)
        
        if new_owner_role:
            self._update(session, new_owner_role.id, role=Roles.OWNER, granted_by=current_owner_id)
        else:
            self._create(
                session,
                **{
                    self.user_field: new_owner_id,
                    self.resource_field: resource_id,
                    'role': Roles.OWNER,
                    'granted_by': current_owner_id
                }
            )
        
        return {
            'transferred': True,
            self.resource_field: resource_id,
            'previous_owner': current_owner_id,
            'new_owner': new_owner_id
        }

    def _revoke_all_non_owners(self, session: Session, resource_id: str, revoked_by: str) -> dict:
        """
        Remove all non-owner users from resource.
        Only OWNER can revoke all.
        At least one OWNER must remain.
        """
        resource_id = validators._validate_id(resource_id)
        revoked_by = validators._validate_id(revoked_by)
        
        has_permission = self._check_user_has_role(session, revoked_by, resource_id, Roles.OWNER)
        
        if not has_permission:
            context = ErrorContext(
                operation='revoke_all_non_owners',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, 'revoked_by': revoked_by}
            )
            raise ValidationError(
                "Only resource owners can revoke all users",
                context=context,
                severity=ErrorSeverity.HIGH
            )
        
        owner_count = session.query(self.model).filter(
            and_(
                getattr(self.model, self.resource_field) == resource_id,
                self.model.role == Roles.OWNER,
                self.model.is_deleted == False
            )
        ).count()
        
        if owner_count < 1:
            context = ErrorContext(
                operation='revoke_all_non_owners',
                component=self.model_name,
                additional_info={self.resource_field: resource_id}
            )
            raise ValidationError(
                "No owners found for this resource",
                context=context,
                severity=ErrorSeverity.HIGH
            )
        
        non_owners = session.query(self.model).filter(
            and_(
                getattr(self.model, self.resource_field) == resource_id,
                self.model.role != Roles.OWNER,
                self.model.is_deleted == False
            )
        ).all()
        
        revoked_count = 0
        for assignment in non_owners:
            self._delete(session, assignment.id)
            revoked_count += 1
        
        return {
            'revoked': True,
            self.resource_field: resource_id,
            'revoked_count': revoked_count,
            'remaining_owners': owner_count
        }

