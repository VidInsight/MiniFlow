from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.models import Trigger, TriggerType, TriggerStatus
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity


class TriggerOrchestrator(BaseOrchestrator):
    """Trigger orchestrator for trigger management operations with full CRUD support."""

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        """Return the Trigger CRUD instance."""
        return self.trigger_crud

    # ==========================================
    # CREATE & UPDATE OPERATIONS
    # ==========================================

    @with_session
    def create(self, session: Session, **kwargs) -> Dict[str, Any]:
        """Create a new trigger with comprehensive validation"""
        try:
            result = self.trigger_crud._create(session, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", 
                workflow_id=kwargs.get("workflow_id"), 
                name=kwargs.get("name"),
                trigger_type=kwargs.get("trigger_type")
            )
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, trigger_id: str, **kwargs) -> Dict[str, Any]:
        """Update trigger with validation"""
        if not self.trigger_crud._exists(session, trigger_id):
            self._handle_not_found("Trigger", trigger_id, "update")

        try:
            result = self.trigger_crud._update(session, trigger_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", trigger_id=trigger_id)
            raise OrchestrationError(str(e), context=context) from e

    # ==========================================
    # SPECIALIZED QUERY OPERATIONS  
    # ==========================================

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100, 
                       include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get triggers for a specific workflow"""
        try:
            results = self.trigger_crud._filter(session, 
                filters={"workflow_id": workflow_id}, 
                skip=skip, 
                limit=limit,
                order_by_field="created_at"
            )
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_type(self, session: Session, trigger_type: TriggerType, skip: int = 0, limit: int = 100,
                   include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get triggers by type"""
        try:
            results = self.trigger_crud._filter(session, 
                filters={"trigger_type": trigger_type.value},
                skip=skip,
                limit=limit,
                order_by_field="created_at"
            )
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_type", trigger_type=trigger_type.value)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_active_triggers(self, session: Session, trigger_type: TriggerType = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all active triggers, optionally filtered by type"""
        try:
            filters = {"status": TriggerStatus.ACTIVE.value}
            if trigger_type:
                filters["trigger_type"] = trigger_type.value

            results = self.trigger_crud._filter(session, 
                filters=filters,
                skip=skip,
                limit=limit,
                order_by_field="created_at"
            )
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_active_triggers", trigger_type=trigger_type.value if trigger_type else None)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_webhook_id(self, session: Session, webhook_id: str) -> List[Dict[str, Any]]:
        """Get triggers by webhook_id (can be multiple triggers with same webhook_id)"""
        try:
            triggers = self.trigger_crud.get_by_webhook_id(session, webhook_id)
            return self._serialize_multiple_results(triggers)
        except Exception as e:
            context = self._create_error_context("get_by_webhook_id", webhook_id=webhook_id)
            raise OrchestrationError(str(e), context=context) from e

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================

    @with_session
    def toggle_status(self, session: Session, trigger_id: str) -> Dict[str, Any]:
        """Toggle trigger status between ACTIVE and INACTIVE"""
        trigger = self.trigger_crud._get_by_id(session, trigger_id)
        if not trigger:
            self._handle_not_found("Trigger", trigger_id, "toggle_status")

        try:
            new_status = TriggerStatus.INACTIVE if trigger.status == TriggerStatus.ACTIVE else TriggerStatus.ACTIVE
            result = self.trigger_crud._update(session, trigger_id, status=new_status)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("toggle_status", trigger_id=trigger_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def set_status(self, session: Session, trigger_id: str, status: TriggerStatus) -> Dict[str, Any]:
        """Set trigger status to specific value"""
        if not self.trigger_crud._exists(session, trigger_id):
            self._handle_not_found("Trigger", trigger_id, "set_status")

        try:
            result = self.trigger_crud._update(session, trigger_id, status=status)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("set_status", trigger_id=trigger_id, status=status.value)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def activate_trigger(self, session: Session, trigger_id: str) -> Dict[str, Any]:
        """Activate a trigger (set status to ACTIVE)"""
        return self.set_status(session, trigger_id, TriggerStatus.ACTIVE)

    @with_session
    def deactivate_trigger(self, session: Session, trigger_id: str) -> Dict[str, Any]:
        """Deactivate a trigger (set status to INACTIVE)"""
        return self.set_status(session, trigger_id, TriggerStatus.INACTIVE)

    @with_session
    def mark_error(self, session: Session, trigger_id: str, error_message: str = None) -> Dict[str, Any]:
        """Mark trigger as ERROR status with optional error message"""
        update_data = {"status": TriggerStatus.ERROR}
        if error_message:
            # Note: If you want to store error messages, you might need to add an error_message field to the Trigger model
            # For now, we'll just log it
            self.logger.error(f"Trigger {trigger_id} marked as ERROR: {error_message}")
        
        try:
            result = self.trigger_crud._update(session, trigger_id, **update_data)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("mark_error", trigger_id=trigger_id, error_message=error_message)
            raise OrchestrationError(str(e), context=context) from e

    # ==========================================
    # WORKFLOW INTEGRATION
    # ==========================================

    @with_session
    def get_workflow_triggers_count(self, session: Session, workflow_id: str) -> int:
        """Get count of triggers for a specific workflow"""
        try:
            return self.trigger_crud._count_with_filter(session, filters={"workflow_id": workflow_id})
        except Exception as e:
            context = self._create_error_context("get_workflow_triggers_count", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_workflow_active_triggers_count(self, session: Session, workflow_id: str) -> int:
        """Get count of active triggers for a specific workflow"""
        try:
            return self.trigger_crud._count_with_filter(session, filters={
                "workflow_id": workflow_id, 
                "status": TriggerStatus.ACTIVE.value
            })
        except Exception as e:
            context = self._create_error_context("get_workflow_active_triggers_count", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_workflow_triggers(self, session: Session, workflow_id: str) -> int:
        """Delete all triggers for a workflow (called when workflow is deleted)"""
        try:
            triggers = self.trigger_crud._filter(session, filters={"workflow_id": workflow_id})
            deleted_count = 0
            
            for trigger in triggers:
                self.trigger_crud._delete(session, trigger.id)
                deleted_count += 1
            
            self.logger.info(f"Deleted {deleted_count} triggers for workflow {workflow_id}")
            return deleted_count
            
        except Exception as e:
            context = self._create_error_context("delete_workflow_triggers", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    @with_session
    def validate_trigger_config(self, session: Session, trigger_type: str, config: Dict[str, Any]) -> bool:
        """Validate trigger configuration without creating the trigger"""
        try:
            # Use the TriggerCRUD validation logic
            self.trigger_crud._validate_and_enhance_config(session, trigger_type, config)
            return True
        except ValidationError:
            return False
        except Exception as e:
            self.logger.error(f"Error validating trigger config: {str(e)}")
            return False

    @with_session
    def check_webhook_id_availability(self, session: Session, webhook_id: str, exclude_trigger_id: str = None) -> bool:
        """Check if webhook_id is available (not used by other triggers)"""
        try:
            existing_triggers = self.trigger_crud._find_webhook_by_id(session, webhook_id, exclude_trigger_id)
            return len(existing_triggers) == 0
        except Exception as e:
            context = self._create_error_context("check_webhook_id_availability", webhook_id=webhook_id)
            raise OrchestrationError(str(e), context=context) from e

    # ==========================================
    # STATISTICS & MONITORING  
    # ==========================================

    @with_session
    def get_trigger_statistics(self, session: Session) -> Dict[str, Any]:
        """Get overall trigger statistics"""
        try:
            total_triggers = self.trigger_crud._count(session)
            
            # Count by status
            active_count = self.trigger_crud._count_with_filter(session, {"status": TriggerStatus.ACTIVE.value})
            inactive_count = self.trigger_crud._count_with_filter(session, {"status": TriggerStatus.INACTIVE.value})
            error_count = self.trigger_crud._count_with_filter(session, {"status": TriggerStatus.ERROR.value})
            
            # Count by type
            manual_count = self.trigger_crud._count_with_filter(session, {"trigger_type": TriggerType.MANUAL.value})
            scheduled_count = self.trigger_crud._count_with_filter(session, {"trigger_type": TriggerType.SCHEDULED.value})
            webhook_count = self.trigger_crud._count_with_filter(session, {"trigger_type": TriggerType.WEBHOOK.value})
            
            return {
                "total_triggers": total_triggers,
                "by_status": {
                    "active": active_count,
                    "inactive": inactive_count,
                    "error": error_count
                },
                "by_type": {
                    "manual": manual_count,
                    "scheduled": scheduled_count,
                    "webhook": webhook_count
                }
            }
        except Exception as e:
            context = self._create_error_context("get_trigger_statistics")
            raise OrchestrationError(str(e), context=context) from e
