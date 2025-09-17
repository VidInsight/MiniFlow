from typing import Dict, Any, List
from sqlalchemy.orm import Session
from uuid import uuid4

from miniflow.database.models import Trigger, TriggerType, TriggerStatus
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class TriggerCRUD(BaseCRUD[Trigger]):
    def __init__(self):
        super().__init__(Trigger)

    def _create(self, session: Session, **kwargs):
        """Create trigger with comprehensive validation"""
        
        # ==========================================
        # REQUIRED FIELD VALIDATIONS
        # ==========================================
        
        workflow_id = kwargs.get('workflow_id')
        if not workflow_id:
            raise ValidationError("Trigger must have a workflow_id", severity=ErrorSeverity.HIGH)

        name = kwargs.get('name')
        if not name or not name.strip():
            raise ValidationError("Trigger name cannot be empty", severity=ErrorSeverity.HIGH)

        trigger_type = kwargs.get('trigger_type')
        if not trigger_type:
            raise ValidationError("Trigger type is required", severity=ErrorSeverity.HIGH)
        
        # Validate trigger_type enum
        if trigger_type not in [t.value for t in TriggerType]:
            raise ValidationError(f"Invalid trigger type: {trigger_type}", severity=ErrorSeverity.HIGH)

        # ==========================================
        # UNIQUENESS VALIDATIONS
        # ==========================================
        
        # Name uniqueness per workflow
        name = name.strip()
        existing_name = self._filter(session, filters={"workflow_id": workflow_id, "name": name})
        if existing_name:
            raise ValidationError(f"Trigger with name '{name}' already exists in workflow", severity=ErrorSeverity.HIGH)

        # ==========================================
        # CONFIG VALIDATION & GENERATION
        # ==========================================
        
        config = kwargs.get('config', {})
        if not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary", severity=ErrorSeverity.MEDIUM)
        
        # Trigger type specific config validation
        config = self._validate_and_enhance_config(session, trigger_type, config)
        
        # ==========================================
        # INPUT MAPPING VALIDATION
        # ==========================================
        
        input_mapping = kwargs.get('input_mapping')
        if input_mapping is not None:
            if not isinstance(input_mapping, dict):
                raise ValidationError("Input mapping must be a dictionary", severity=ErrorSeverity.MEDIUM)
        
        # ==========================================
        # SET DEFAULTS & NORMALIZE
        # ==========================================
        
        # Set defaults
        if "status" not in kwargs:
            kwargs["status"] = TriggerStatus.ACTIVE
        
        # Update kwargs with validated values
        kwargs["name"] = name
        kwargs["trigger_type"] = trigger_type
        kwargs["config"] = config
        kwargs["workflow_id"] = workflow_id
        
        return super()._create(session, **kwargs)

    def _update(self, session: Session, record_id: str, **kwargs):
        """Update trigger with validation"""
        
        # Get existing trigger for validation
        existing_trigger = self._get_by_id(session, record_id)
        if not existing_trigger:
            raise ValidationError(f"Trigger {record_id} not found", severity=ErrorSeverity.HIGH)
        
        # ==========================================
        # NAME UNIQUENESS CHECK
        # ==========================================
        
        if "name" in kwargs and kwargs["name"]:
            new_name = kwargs["name"].strip()
            if not new_name:
                raise ValidationError("Trigger name cannot be empty", severity=ErrorSeverity.HIGH)

            # Check uniqueness within workflow (excluding current record)
            existing_name = self._filter(session, filters={
                "workflow_id": existing_trigger.workflow_id, 
                "name": new_name
            })
            if existing_name and existing_name[0].id != record_id:
                raise ValidationError(f"Trigger with name '{new_name}' already exists in workflow", severity=ErrorSeverity.HIGH)

            kwargs["name"] = new_name
        
        # ==========================================
        # CONFIG VALIDATION
        # ==========================================
        
        if "config" in kwargs:
            config = kwargs["config"]
            if not isinstance(config, dict):
                raise ValidationError("Config must be a dictionary", severity=ErrorSeverity.MEDIUM)
            
            # Use existing trigger_type unless it's being updated
            trigger_type = kwargs.get("trigger_type", existing_trigger.trigger_type)
            config = self._validate_and_enhance_config(session, trigger_type, config, exclude_id=record_id)
            kwargs["config"] = config
        
        # ==========================================
        # TRIGGER TYPE CHANGE VALIDATION
        # ==========================================
        
        if "trigger_type" in kwargs:
            new_trigger_type = kwargs["trigger_type"]
            if new_trigger_type not in [t.value for t in TriggerType]:
                raise ValidationError(f"Invalid trigger type: {new_trigger_type}", severity=ErrorSeverity.HIGH)
            
            # If trigger type changed, validate config compatibility
            if new_trigger_type != existing_trigger.trigger_type:
                current_config = kwargs.get("config", existing_trigger.config)
                config = self._validate_and_enhance_config(session, new_trigger_type, current_config, exclude_id=record_id)
                kwargs["config"] = config
        
        # ==========================================
        # INPUT MAPPING VALIDATION
        # ==========================================
        
        if "input_mapping" in kwargs:
            input_mapping = kwargs["input_mapping"]
            if input_mapping is not None and not isinstance(input_mapping, dict):
                raise ValidationError("Input mapping must be a dictionary", severity=ErrorSeverity.MEDIUM)

        return super()._update(session, record_id, **kwargs)

    def _validate_and_enhance_config(self, session: Session, trigger_type: str, config: Dict[str, Any], exclude_id: str = None) -> Dict[str, Any]:
        """Validate and enhance config based on trigger type"""
        
        config = config.copy()  # Don't modify original
        
        if trigger_type == TriggerType.MANUAL.value:
            # Manual triggers don't need specific config
            return config
            
        elif trigger_type == TriggerType.SCHEDULED.value:
            # Validate scheduled trigger config
            if not config.get('cron') and not config.get('interval_seconds'):
                raise ValidationError(
                    "Scheduled trigger must have either 'cron' or 'interval_seconds'", 
                    severity=ErrorSeverity.HIGH
                )
            
            # Basic cron validation
            if config.get('cron'):
                cron_parts = str(config['cron']).split()
                if len(cron_parts) != 5:
                    raise ValidationError(
                        "Invalid cron expression format (must have 5 parts)", 
                        severity=ErrorSeverity.MEDIUM
                    )
            
            # Validate interval_seconds
            if config.get('interval_seconds'):
                try:
                    interval = int(config['interval_seconds'])
                    if interval < 60:  # Minimum 1 minute
                        raise ValidationError(
                            "Interval must be at least 60 seconds", 
                            severity=ErrorSeverity.MEDIUM
                        )
                except (ValueError, TypeError):
                    raise ValidationError(
                        "interval_seconds must be a valid integer", 
                        severity=ErrorSeverity.MEDIUM
                    )
            
            return config
            
        elif trigger_type == TriggerType.WEBHOOK.value:
            # Validate and generate webhook config
            webhook_id = config.get('webhook_id')
            
            if not webhook_id:
                # Auto-generate webhook_id if not provided
                webhook_id = f"webhook-{str(uuid4())[:8]}"
                config['webhook_id'] = webhook_id
            
            # Validate webhook_id uniqueness globally
            existing_webhook = self._find_webhook_by_id(session, webhook_id, exclude_id)
            if existing_webhook:
                raise ValidationError(
                    f"Webhook ID '{webhook_id}' already exists", 
                    severity=ErrorSeverity.HIGH
                )
            
            # Set default content type
            if 'content_type' not in config:
                config['content_type'] = 'application/json'
            
            return config
        
        else:
            raise ValidationError(f"Unknown trigger type: {trigger_type}", severity=ErrorSeverity.HIGH)

    def _find_webhook_by_id(self, session: Session, webhook_id: str, exclude_id: str = None) -> List[Trigger]:
        """Find triggers with the given webhook_id"""
        
        # Get all webhook triggers
        webhook_triggers = self._filter(session, filters={"trigger_type": TriggerType.WEBHOOK.value})
        
        # Check webhook_id in config
        matching_triggers = []
        for trigger in webhook_triggers:
            if exclude_id and trigger.id == exclude_id:
                continue
                
            trigger_webhook_id = trigger.config.get('webhook_id')
            if trigger_webhook_id == webhook_id:
                matching_triggers.append(trigger)
        
        return matching_triggers

    def get_by_webhook_id(self, session: Session, webhook_id: str) -> List[Trigger]:
        """Get triggers by webhook_id (public method for handlers)"""
        return self._find_webhook_by_id(session, webhook_id)

    def get_active_triggers_by_type(self, session: Session, trigger_type: TriggerType) -> List[Trigger]:
        """Get active triggers by type (public method for trigger manager)"""
        return self._filter(session, filters={
            "trigger_type": trigger_type.value,
            "status": TriggerStatus.ACTIVE.value
        })
