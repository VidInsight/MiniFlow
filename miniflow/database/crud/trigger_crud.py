from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Trigger
from ..enums import TriggerType
from .base_crud import BaseCRUD


class TriggerCRUD(BaseCRUD[Trigger]):
    def __init__(self):
        super().__init__(Trigger)
        self.model_fields = {column.name for column in Trigger.__table__.columns}
        self.required_fields = {'workflow_id', 'name', 'trigger_type'}
        self.protected_fields = {'workflow_id', 'trigger_type'}

    def _create(self, session: Session, **kwargs) -> Trigger:
        """Create a new trigger with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate workflow_id
        workflow_id = kwargs['workflow_id']
        kwargs['workflow_id'] = validators._validate_id(workflow_id)
        
        # Validate name and check uniqueness
        name = kwargs['name']
        name = validators._validate_name(name)

        # Validate trigger_type
        trigger_type = kwargs.get('trigger_type')
        if not trigger_type:
            trigger_type = "API"

        if isinstance(trigger_type, str):
            try:
                kwargs['trigger_type'] = TriggerType(trigger_type)
            except ValueError:
                raise ValueError(f"Invalid trigger type: {trigger_type}")
        
        # Validate config is dict (set default if not provided)
        config = kwargs.get('config', {})
        if config is not None and not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")
        kwargs['config'] = config
        
        # Validate input_mapping is dict (set default if not provided)
        input_mapping = kwargs.get("input_mapping", {})
        if input_mapping is not None and not isinstance(input_mapping, dict):
            raise ValueError("Input mapping must be a dictionary")
        kwargs['input_mapping'] = input_mapping
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        trigger = super()._create(session, **kwargs)
        return trigger

    def _update(self, session: Session, record_id: str, **kwargs) -> Trigger:
        """Update trigger with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        existing = self._get_by_id(session, record_id)
        if not existing:
            context = ErrorContext(operation='update', component=self.model_name,additional_info={'record_id': record_id})
            raise ValidationError(f"{self.model_name} with ID {record_id} not found", context=context, severity=ErrorSeverity.MEDIUM)

        # If name is being updated, validate it
        if 'name' in kwargs and kwargs['name']:
            name = kwargs['name']
            kwargs['name'] = validators._validate_name(name)
        
        # Validate config if provided
        if 'config' in kwargs and kwargs['config'] is not None:
            if not isinstance(kwargs['config'], dict):
                raise ValueError("Config must be a dictionary")
        
        # Validate input_mapping if provided
        if 'input_mapping' in kwargs and kwargs['input_mapping'] is not None:
            if not isinstance(kwargs['input_mapping'], dict):
                raise ValueError("Input mapping must be a dictionary")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        trigger = super()._update(session, record_id, **kwargs)
        return trigger

    def _get_by_workflow_id(self, session: Session, workflow_id: str, skip: int = 0, limit: int = None) -> List[Trigger]:
        """Get triggers for a specific workflow with pagination."""
        try:
            # Validate workflow_id
            workflow_id = validators._validate_id(workflow_id)
            
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            # Query triggers filtered by workflow_id
            query = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_workflow_id',component=self.model_name,additional_info={'workflow_id': workflow_id, 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} records by workflow_id: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

    def _count_by_workflow_id(self, session: Session, workflow_id: str) -> int:
        """Get total count of triggers for a specific workflow."""
        try:
            # Validate workflow_id
            workflow_id = validators._validate_id(workflow_id)
            
            # Count triggers filtered by workflow_id
            count = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(operation='count_by_workflow_id',component=self.model_name,additional_info={'workflow_id': workflow_id})
            raise DatabaseQueryError(f"Failed to count {self.model_name} records by workflow_id: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

    def _get_by_type(self, session: Session, trigger_type: TriggerType, skip: int = 0, limit: int = None) -> List[Trigger]:
        """Get triggers by type with pagination."""
        try:
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            # Query triggers filtered by type
            query = session.query(self.model).filter(
                and_(
                    self.model.trigger_type == trigger_type,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_type',component=self.model_name,additional_info={'trigger_type': str(trigger_type), 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} records by type: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

    def _activate(self, session: Session, record_id: str) -> Trigger:
        """Activate a trigger."""
        return self._update(session, record_id, is_enabled=True)

    def _deactivate(self, session: Session, record_id: str) -> Trigger:
        """Deactivate a trigger."""
        return self._update(session, record_id, is_enabled=False)

    def _get_active_triggers(self, session: Session, workflow_id: str = None) -> List[Trigger]:
        """Get all active triggers, optionally filtered by workflow."""
        try:
            query = session.query(self.model).filter(
                and_(
                    self.model.is_enabled == True,
                    self.model.is_deleted == False
                )
            )
            
            if workflow_id:
                workflow_id = validators._validate_id(workflow_id)
                query = query.filter(self.model.workflow_id == workflow_id)
            
            results = query.order_by(self.model.created_at.desc()).all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_active_triggers',component=self.model_name,additional_info={'workflow_id': workflow_id})
            raise DatabaseQueryError(f"Failed to get active {self.model_name} records: {str(e)}",context=context,severity=ErrorSeverity.HIGH)