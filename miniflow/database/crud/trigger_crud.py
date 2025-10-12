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
        self.required_fields = {'name', 'trigger_type'}
        self.protected_fields = {'trigger_type'}  # workflow_id removed - now managed via WorkflowTrigger

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> Trigger:
        """
        Create a new reusable trigger with validation.
        
        NOTE: This creates only the Trigger. To assign it to workflows,
        use WorkflowTriggerCRUD after creation.
        
        Args:
            session: Database session
            name: Unique trigger name
            trigger_type: Type of trigger (API, SCHEDULED, WEBHOOK)
            config: Trigger configuration (cron, endpoint, etc.)
            input_mapping: Input parameter mapping (optional)
            is_enabled: Whether trigger is active (default: True)
            **kwargs: Additional fields
            
        Returns:
            Trigger: Created trigger instance
        """
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate name and check uniqueness
        name = kwargs['name']
        name = validators._validate_name(name)
        kwargs['name'] = name

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

    def _activate(self, session: Session, record_id: str) -> Trigger:
        """Activate a trigger."""
        return self._update(session, record_id, is_enabled=True)

    def _deactivate(self, session: Session, record_id: str) -> Trigger:
        """Deactivate a trigger."""
        return self._update(session, record_id, is_enabled=False)