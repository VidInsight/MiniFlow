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

    def _get_by_user(self, session: Session, user_id: str, skip: int = 0, limit: int = None) -> List[TJunction]:
        """Get all role assignments for a user."""
        try:
            user_id = validators._validate_id(user_id)
            
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    getattr(self.model, self.user_field) == user_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.granted_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(
                operation='get_by_user',
                component=self.model_name,
                additional_info={self.user_field: user_id, 'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} by user: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_by_resource(self, session: Session, resource_id: str, skip: int = 0, limit: int = None) -> List[TJunction]:
        """Get all users with roles for a resource."""
        try:
            resource_id = validators._validate_id(resource_id)
            
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    getattr(self.model, self.resource_field) == resource_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.granted_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(
                operation='get_by_resource',
                component=self.model_name,
                additional_info={self.resource_field: resource_id, 'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} by resource: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_by_user_and_resource(self, session: Session, user_id: str, resource_id: str) -> Optional[TJunction]:
        """Get role assignment for specific user-resource pair."""
        try:
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
            
        except Exception as e:
            context = ErrorContext(
                operation='get_by_user_and_resource',
                component=self.model_name,
                additional_info={self.user_field: user_id, self.resource_field: resource_id}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} by user and resource: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_by_role(self, session: Session, role: Roles, skip: int = 0, limit: int = None) -> List[TJunction]:
        """Get all assignments for a specific role."""
        try:
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.role == role,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.granted_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(
                operation='get_by_role',
                component=self.model_name,
                additional_info={'role': str(role), 'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} by role: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _count_by_user(self, session: Session, user_id: str) -> int:
        """Count role assignments for a user."""
        try:
            user_id = validators._validate_id(user_id)
            
            count = session.query(self.model).filter(
                and_(
                    getattr(self.model, self.user_field) == user_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(
                operation='count_by_user',
                component=self.model_name,
                additional_info={self.user_field: user_id}
            )
            raise DatabaseQueryError(
                f"Failed to count {self.model_name} by user: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _count_by_resource(self, session: Session, resource_id: str) -> int:
        """Count users with roles for a resource."""
        try:
            resource_id = validators._validate_id(resource_id)
            
            count = session.query(self.model).filter(
                and_(
                    getattr(self.model, self.resource_field) == resource_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(
                operation='count_by_resource',
                component=self.model_name,
                additional_info={self.resource_field: resource_id}
            )
            raise DatabaseQueryError(
                f"Failed to count {self.model_name} by resource: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _revoke_by_user_and_resource(self, session: Session, user_id: str, resource_id: str) -> Optional[TJunction]:
        """Revoke (soft delete) role assignment for user-resource pair."""
        try:
            junction = self._get_by_user_and_resource(session, user_id, resource_id)

            if not junction:
                return None
            
            self._delete(session, junction.id)
            return junction
            
        except Exception as e:
            context = ErrorContext(
                operation='revoke_by_user_and_resource',
                component=self.model_name,
                additional_info={self.user_field: user_id, self.resource_field: resource_id}
            )
            raise DatabaseQueryError(
                f"Failed to revoke {self.model_name}: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _revoke_all_by_user(self, session: Session, user_id: str) -> List[TJunction]:
        """Revoke all role assignments for a user."""
        try:
            assignments = self._get_by_user(session, user_id)
            
            revoked = []
            for assignment in assignments:
                self._delete(session, assignment.id)
                revoked.append(assignment)
            
            return revoked
            
        except Exception as e:
            context = ErrorContext(
                operation='revoke_all_by_user',
                component=self.model_name,
                additional_info={self.user_field: user_id}
            )
            raise DatabaseQueryError(
                f"Failed to revoke all {self.model_name} for user: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _revoke_all_by_resource(self, session: Session, resource_id: str) -> List[TJunction]:
        """Revoke all role assignments for a resource."""
        try:
            assignments = self._get_by_resource(session, resource_id)
            
            revoked = []
            for assignment in assignments:
                self._delete(session, assignment.id)
                revoked.append(assignment)
            
            return revoked
            
        except Exception as e:
            context = ErrorContext(
                operation='revoke_all_by_resource',
                component=self.model_name,
                additional_info={self.resource_field: resource_id}
            )
            raise DatabaseQueryError(
                f"Failed to revoke all {self.model_name} for resource: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

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

