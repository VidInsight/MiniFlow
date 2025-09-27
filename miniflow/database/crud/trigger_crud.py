from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from ..models import Trigger, TriggerType, Workflow
from .base_crud import BaseCRUD

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext


class TriggerCRUD(BaseCRUD[Trigger]):
    def __init__(self):
        super().__init__(Trigger)
        self.required_fields = [
            "workflow_id", "name", "trigger_type", "config", "input_mapping"
            ]
        self.protected_fields = [
            'created_at', 'updated_at', 'id', "trigger_type"
        ]
    
    def _validate_workflow_exists(self, session: Session, workflow_id: str) -> Workflow:
        workflow = session.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            context = ErrorContext(operation="validate_workflow_for_node", additional_info={"workflow_id": workflow_id})
            raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.HIGH)
        return workflow

    def _validate_name(self, session: Session, name: str, workflow_id: str, exclude_id: Optional[str] = None) -> str:
        if not name or not name.strip():
            context = ErrorContext(operation="validate_name", additional_info={"field": "name"})
            raise ValidationError("Trigger name cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        name = name.strip()

        if len(name) < 2:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name})
            raise ValidationError(f"Trigger name too short: {len(name)} chars (min 2)", context=context, severity=ErrorSeverity.MEDIUM)

        if len(name) > 100:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name})
            raise ValidationError(f"Trigger name too long: {len(name)} chars (max 100)", context=context, severity=ErrorSeverity.MEDIUM)
        
        existing = session.query(Trigger).filter(and_(Trigger.name == name, Trigger.workflow_id == workflow_id)).first()
        
        if existing and existing.id != exclude_id:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name, "workflow_id": workflow_id, "existing_id": existing.id})
            raise ValidationError(f"Trigger name '{name}' already exists in workflow", context=context, severity=ErrorSeverity.HIGH)
        
        return name

    def _validate_trigger_type(self, trigger_type: str) -> TriggerType:
        try:
            return TriggerType(trigger_type)
        except ValueError:
            raise ValidationError(f"Invalid trigger type: {trigger_type}", severity=ErrorSeverity.HIGH)
    
    def _create(self, session: Session, **kwargs):
        self._validate_required_fields(self.required_fields, kwargs)
        
        workflow_id = kwargs.get('workflow_id')
        self._validate_workflow_exists(session, workflow_id)
        
        name = kwargs.get('name')
        name = self._validate_name(session, name, workflow_id)

        trigger_type = kwargs.get('trigger_type')
        trigger_type = self._validate_trigger_type(trigger_type)

        kwargs["name"] = name
        kwargs["trigger_type"] = trigger_type
        kwargs["workflow_id"] = workflow_id
        
        valid_fields, invalid_fields = self._validate_request_data(kwargs)
        return super()._create(session, **valid_fields)

    def _update(self, session: Session, record_id: str, **kwargs):
        existing_trigger = self._get_by_id(session, record_id)
        if not existing_trigger:
            raise ValidationError(f"Trigger {record_id} not found", severity=ErrorSeverity.HIGH)

        if "name" in kwargs and kwargs["name"]:
            new_name = kwargs["name"].strip()
            kwargs["name"] = self._validate_name(session, new_name, existing_trigger.workflow_id, exclude_id=record_id)
    
        
        valid_fields, invalid_fields = self._validate_request_data(kwargs)
        protected_fields = self._validate_protected_fields(self.protected_fields, valid_fields)
            
        return super()._update(session, record_id, **protected_fields)

    def _delete(self, session, record_id):
        return super()._delete(session, record_id)  
    
    def _get_api_trigger(self, session: Session, trigger_id: str) -> Optional[Trigger]:
        trigger = self._get_by_id(session, trigger_id)
        if trigger and trigger.trigger_type == TriggerType.API:
            return trigger
        return None

    def _get_webhook_trigger(self, session: Session, trigger_id: str) -> Optional[Trigger]:
        trigger = self._get_by_id(session, trigger_id)
        if trigger and trigger.trigger_type == TriggerType.WEBHOOK:
            return trigger
        return None
    
    def _get_scheduled_trigger(self, session: Session, trigger_id: str) -> Optional[Trigger]:
        trigger = self._get_by_id(session, trigger_id)
        if trigger and trigger.trigger_type == TriggerType.SCHEDULED:
            return trigger
        return None
    