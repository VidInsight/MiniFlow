from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Permission
from ..enums import Roles, Plans
from .base_crud import BaseCRUD


class PermissionCRUD(BaseCRUD[Permission]):
    def __init__(self):
        super().__init__(Permission)
        self.model_fields = {column.name for column in Permission.__table__.columns}
        self.required_fields = {'name', 'required_role', 'required_plan'}
        self.protected_fields = {'name'}  # Permission name shouldn't change

    def _create(self, session: Session, **kwargs) -> Permission:
        """Create a new permission with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate name
        name = kwargs.get('name')
        if name:
            name = self._validate_name(name)
            # Check uniqueness
            self._validate_name_uniqueness(session, name)
            kwargs['name'] = name
        
        # Validate endpoint if provided
        endpoint = kwargs.get('endpoint')
        if endpoint:
            kwargs['endpoint'] = self._validate_endpoint(endpoint)
        
        # Validate action if provided
        action = kwargs.get('action')
        if action:
            kwargs['action'] = self._validate_action(action)
        
        # Validate required_role
        required_role = kwargs.get('required_role')
        if required_role:
            if isinstance(required_role, str):
                try:
                    kwargs['required_role'] = Roles(required_role)
                except ValueError:
                    raise ValueError(f"Invalid role: {required_role}")
        
        # Validate required_plan
        required_plan = kwargs.get('required_plan')
        if required_plan:
            if isinstance(required_plan, str):
                try:
                    kwargs['required_plan'] = Plans(required_plan)
                except ValueError:
                    raise ValueError(f"Invalid plan: {required_plan}")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        permission = super()._create(session, **kwargs)
        return permission

    def _update(self, session: Session, record_id: str, **kwargs) -> Permission:
        """Update permission with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Validate endpoint if being updated
        if 'endpoint' in kwargs and kwargs['endpoint']:
            kwargs['endpoint'] = self._validate_endpoint(kwargs['endpoint'])
        
        # Validate action if being updated
        if 'action' in kwargs and kwargs['action']:
            kwargs['action'] = self._validate_action(kwargs['action'])
        
        # Validate required_role if being updated
        if 'required_role' in kwargs:
            required_role = kwargs['required_role']
            if isinstance(required_role, str):
                try:
                    kwargs['required_role'] = Roles(required_role)
                except ValueError:
                    raise ValueError(f"Invalid role: {required_role}")
        
        # Validate required_plan if being updated
        if 'required_plan' in kwargs:
            required_plan = kwargs['required_plan']
            if isinstance(required_plan, str):
                try:
                    kwargs['required_plan'] = Plans(required_plan)
                except ValueError:
                    raise ValueError(f"Invalid plan: {required_plan}")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        permission = super()._update(session, record_id, **kwargs)
        return permission

    def _validate_name(self, name: str) -> str:
        """Validate permission name format."""
        if not name or not isinstance(name, str):
            raise ValueError("Permission name must be a non-empty string")
        
        name = name.strip()
        
        if len(name) < 3:
            raise ValueError(f"Permission name too short: {len(name)} chars (min 3)")
        
        if len(name) > 100:
            raise ValueError(f"Permission name too long: {len(name)} chars (max 100)")
        
        return name

    def _validate_endpoint(self, endpoint: str) -> str:
        """Validate endpoint format."""
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("Endpoint must be a non-empty string")
        
        endpoint = endpoint.strip()
        
        if len(endpoint) > 100:
            raise ValueError(f"Endpoint too long: {len(endpoint)} chars (max 100)")
        
        # Endpoint should start with /
        if not endpoint.startswith('/'):
            raise ValueError("Endpoint must start with /")
        
        return endpoint

    def _validate_action(self, action: str) -> str:
        """Validate action format."""
        if not action or not isinstance(action, str):
            raise ValueError("Action must be a non-empty string")
        
        action = action.strip().upper()
        
        # Common HTTP methods
        valid_actions = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'CONNECT', 'TRACE'}
        
        if action not in valid_actions:
            raise ValueError(f"Invalid action: {action}. Must be one of {valid_actions}")
        
        return action

    def _validate_name_uniqueness(self, session: Session, name: str):
        """Validate that permission name is unique."""
        existing = session.query(self.model).filter(
            and_(
                self.model.name == name,
                self.model.is_deleted == False
            )
        ).first()
        
        if existing:
            context = ErrorContext(operation='validate_name_uniqueness', component=self.model_name,
                                 additional_info={'name': name, 'existing_id': existing.id})
            raise ValidationError(f"Permission name '{name}' already exists",
                                context=context, severity=ErrorSeverity.HIGH)

    def _get_by_name(self, session: Session, name: str) -> Optional[Permission]:
        """Get permission by name."""
        try:
            name = self._validate_name(name)
            
            permission = session.query(self.model).filter(
                and_(
                    self.model.name == name,
                    self.model.is_deleted == False
                )
            ).first()
            
            return permission
            
        except Exception as e:
            context = ErrorContext(operation='get_by_name', component=self.model_name,
                                 additional_info={'name': name})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by name: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_endpoint(self, session: Session, endpoint: str, skip: int = 0, limit: int = None) -> List[Permission]:
        """Get permissions by endpoint with pagination."""
        try:
            endpoint = self._validate_endpoint(endpoint)
            
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.endpoint == endpoint,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_endpoint', component=self.model_name,
                                 additional_info={'endpoint': endpoint, 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by endpoint: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_endpoint_and_action(self, session: Session, endpoint: str, action: str) -> Optional[Permission]:
        """Get permission by endpoint and action combination."""
        try:
            endpoint = self._validate_endpoint(endpoint)
            action = self._validate_action(action)
            
            permission = session.query(self.model).filter(
                and_(
                    self.model.endpoint == endpoint,
                    self.model.action == action,
                    self.model.is_deleted == False
                )
            ).first()
            
            return permission
            
        except Exception as e:
            context = ErrorContext(operation='get_by_endpoint_and_action', component=self.model_name,
                                 additional_info={'endpoint': endpoint, 'action': action})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by endpoint and action: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_role(self, session: Session, role: Roles, skip: int = 0, limit: int = None) -> List[Permission]:
        """Get permissions by required role with pagination."""
        try:
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.required_role == role,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_role', component=self.model_name,
                                 additional_info={'role': str(role), 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by role: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_plan(self, session: Session, plan: Plans, skip: int = 0, limit: int = None) -> List[Permission]:
        """Get permissions by required plan with pagination."""
        try:
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.required_plan == plan,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_plan', component=self.model_name,
                                 additional_info={'plan': str(plan), 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by plan: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _check_permission(self, session: Session, endpoint: str, action: str, user_role: Roles, user_plan: Plans) -> bool:
        """
        Check if user has permission for endpoint and action.
        
        Args:
            session: Database session
            endpoint: API endpoint
            action: HTTP action (GET, POST, etc.)
            user_role: User's role
            user_plan: User's plan
        
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get permission for endpoint and action
            permission = self._get_by_endpoint_and_action(session, endpoint, action)
            
            if not permission:
                # If no specific permission found, deny by default
                return False
            
            # Check if user's role meets requirement
            # Role hierarchy: OWNER > EDITOR > CONTRIBUTOR > VIEWER
            role_hierarchy = {
                Roles.OWNER: 4,
                Roles.EDITOR: 3,
                Roles.CONTRIBUTOR: 2,
                Roles.VIEWER: 1
            }
            
            user_role_level = role_hierarchy.get(user_role, 0)
            required_role_level = role_hierarchy.get(permission.required_role, 99)
            
            if user_role_level < required_role_level:
                return False
            
            # Check if user's plan meets requirement
            # Plan hierarchy: ENTERPRISE > PRO > FREE
            plan_hierarchy = {
                Plans.ENTERPRISE: 3,
                Plans.PRO: 2,
                Plans.FREE: 1
            }
            
            user_plan_level = plan_hierarchy.get(user_plan, 0)
            required_plan_level = plan_hierarchy.get(permission.required_plan, 99)
            
            if user_plan_level < required_plan_level:
                return False
            
            return True
            
        except Exception as e:
            # Log error but deny by default for security
            return False

