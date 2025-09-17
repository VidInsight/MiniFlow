"""
Trigger Operations

Business logic layer for trigger management and execution.
Provides both standard CRUD operations and trigger-specific functionality.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import ValidationError, ResourceNotFound, OrchestrationError
from miniflow.database.orchestration.trigger_orchestrator import TriggerOrchestrator
from miniflow.triggers import TriggerManager

from ..base_operations import BaseBFFOperations
from .schemas import (
    TriggerCreateRequest, TriggerUpdateRequest, TriggerFilterRequest,
    ManualTriggerRequest, WebhookPayloadRequest
)


class TriggerOperations(BaseBFFOperations[TriggerOrchestrator]):
    """
    Trigger operations class providing both CRUD and execution functionality
    
    Handles:
    - Standard CRUD operations (create, read, update, delete, list, filter)
    - Trigger execution (manual, webhook)
    - Trigger management (start, stop, reload)
    - Webhook information and validation
    - Trigger statistics and monitoring
    """
    
    def __init__(self, orchestrator: TriggerOrchestrator, trigger_manager: TriggerManager):
        super().__init__(orchestrator, "trigger")
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        self.trigger_manager = trigger_manager

    def _simplify_trigger_item(self, item: Dict[str, Any], exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Simplify trigger item for response"""
        base_fields = {
            'id': item.get('id'),
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
            'workflow_id': item.get('workflow_id'),
            'name': item.get('name'),
            'description': item.get('description'),
            'trigger_type': item.get('trigger_type'),
            'status': item.get('status'),
            'config': item.get('config', {}),
            'input_mapping': item.get('input_mapping'),
            'webhook_endpoint': item.get('webhook_endpoint'),
            'is_active': item.get('is_active', False)
        }
        
        # Apply exclude fields
        if exclude_fields:
            for field in exclude_fields:
                base_fields.pop(field, None)
                
        return base_fields

    # ==========================================
    # STANDARD CRUD OPERATIONS
    # ==========================================

    async def create_trigger_record(self, request: TriggerCreateRequest) -> Dict[str, Any]:
        """Create new trigger"""
        try:
            response_from_db = self.orchestrator.create(**request.to_dict())
            
            # Reload trigger in manager if it's active
            if response_from_db.get('status') == 'ACTIVE':
                await self.trigger_manager.reload_trigger(response_from_db['id'])
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Trigger creation successful"
            }
        except Exception as e:
            self.logger.error(f"Failed to create trigger: {str(e)}")
            raise

    async def get_trigger_record(self, record_id: str, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get trigger by ID"""
        response_from_db = self.orchestrator.get_by_id(record_id)
        if not response_from_db:
            return None
        return self._simplify_trigger_item(response_from_db, exclude_fields)

    async def update_trigger_record(self, record_id: str, request: TriggerUpdateRequest) -> Dict[str, Any]:
        """Update trigger"""
        try:
            response_from_db = self.orchestrator.update(record_id, **request.to_dict())
            
            # Reload trigger in manager to apply changes
            await self.trigger_manager.reload_trigger(record_id)
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Trigger update successful"
            }
        except Exception as e:
            self.logger.error(f"Failed to update trigger {record_id}: {str(e)}")
            raise

    async def delete_trigger_record(self, record_id: str) -> Dict[str, Any]:
        """Delete trigger"""
        try:
            # Remove from manager first
            await self.trigger_manager.reload_trigger(record_id)
            
            response_from_db = self.orchestrator.delete(record_id)
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Trigger delete successful"
            }
        except Exception as e:
            self.logger.error(f"Failed to delete trigger {record_id}: {str(e)}")
            raise

    async def list_trigger_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """List all triggers"""
        response_from_db = self.orchestrator.get_all(skip=skip, limit=limit, order_by=order_by)
        
        simplified_items = [
            self._simplify_trigger_item(item, exclude_fields) 
            for item in response_from_db.get('items', [])
        ]
        
        return {
            'items': simplified_items,
            'total': response_from_db.get('total', 0),
            'skip': response_from_db.get('skip', skip),
            'limit': response_from_db.get('limit', limit)
        }

    async def count_trigger_records(self) -> int:
        """Count all triggers"""
        return self.orchestrator.count()

    async def filter_trigger_records(self, request: TriggerFilterRequest) -> Dict[str, Any]:
        """Filter triggers"""
        response_from_db = self.orchestrator.filter(**request.to_dict())
        
        simplified_items = [
            self._simplify_trigger_item(item, request.exclude_fields) 
            for item in response_from_db.get('items', [])
        ]
        
        return {
            'items': simplified_items,
            'total': response_from_db.get('total', 0),
            'skip': response_from_db.get('skip', request.skip),
            'limit': response_from_db.get('limit', request.limit)
        }

    # ==========================================
    # WORKFLOW-SPECIFIC OPERATIONS
    # ==========================================

    async def get_workflow_triggers(self, workflow_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all triggers for a specific workflow"""
        try:
            triggers = self.orchestrator.get_by_workflow(workflow_id, skip=skip, limit=limit)
            
            simplified_items = [
                self._simplify_trigger_item(trigger) 
                for trigger in triggers
            ]
            
            return {
                'items': simplified_items,
                'total': len(simplified_items),
                'skip': skip,
                'limit': limit,
                'workflow_id': workflow_id
            }
        except Exception as e:
            self.logger.error(f"Failed to get triggers for workflow {workflow_id}: {str(e)}")
            raise

    async def get_workflow_triggers_count(self, workflow_id: str) -> int:
        """Get trigger count for workflow"""
        return self.orchestrator.get_workflow_triggers_count(workflow_id)

    async def get_workflow_active_triggers_count(self, workflow_id: str) -> int:
        """Get active trigger count for workflow"""
        return self.orchestrator.get_workflow_active_triggers_count(workflow_id)

    # ==========================================
    # TRIGGER EXECUTION OPERATIONS
    # ==========================================

    async def execute_manual_trigger(self, trigger_id: str, request: ManualTriggerRequest) -> Dict[str, Any]:
        """Execute manual trigger"""
        try:
            execution = await self.trigger_manager.trigger_manual(trigger_id, request.input_data)
            
            return {
                'trigger_id': trigger_id,
                'workflow_id': execution.get('workflow_id'),
                'execution_id': execution.get('id'),
                'execution_status': execution.get('status'),
                'trigger_type': 'MANUAL',
                'triggered_at': datetime.now(timezone.utc).isoformat(),
                'processed_data': execution.get('trigger_data')
            }
        except Exception as e:
            self.logger.error(f"Failed to execute manual trigger {trigger_id}: {str(e)}")
            raise

    async def handle_webhook_request(self, webhook_id: str, payload: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Handle incoming webhook"""
        try:
            execution = await self.trigger_manager.handle_webhook(webhook_id, payload, headers)
            
            # Handle both single execution and multiple executions
            if 'executions' in execution:
                # Multiple triggers for same webhook
                return {
                    'webhook_id': webhook_id,
                    'executions': execution['executions'],
                    'triggered_at': datetime.now(timezone.utc).isoformat()
                }
            else:
                # Single trigger
                return {
                    'trigger_id': execution.get('workflow_id'),  # This might need adjustment based on response structure
                    'workflow_id': execution.get('workflow_id'),
                    'execution_id': execution.get('id'),
                    'execution_status': execution.get('status'),
                    'trigger_type': 'WEBHOOK',
                    'webhook_id': webhook_id,
                    'triggered_at': datetime.now(timezone.utc).isoformat(),
                    'processed_data': execution.get('trigger_data')
                }
        except Exception as e:
            self.logger.error(f"Failed to handle webhook {webhook_id}: {str(e)}")
            raise

    # ==========================================
    # TRIGGER MANAGEMENT OPERATIONS
    # ==========================================

    async def toggle_trigger_status(self, trigger_id: str) -> Dict[str, Any]:
        """Toggle trigger status (ACTIVE ↔ INACTIVE)"""
        try:
            response_from_db = self.orchestrator.toggle_status(trigger_id)
            
            # Reload trigger in manager
            await self.trigger_manager.reload_trigger(trigger_id)
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'new_status': response_from_db['status'],
                'message': f"Trigger status toggled to {response_from_db['status']}"
            }
        except Exception as e:
            self.logger.error(f"Failed to toggle trigger status {trigger_id}: {str(e)}")
            raise

    async def activate_trigger(self, trigger_id: str) -> Dict[str, Any]:
        """Activate trigger"""
        try:
            response_from_db = self.orchestrator.activate_trigger(trigger_id)
            
            # Reload trigger in manager
            await self.trigger_manager.reload_trigger(trigger_id)
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Trigger activated successfully"
            }
        except Exception as e:
            self.logger.error(f"Failed to activate trigger {trigger_id}: {str(e)}")
            raise

    async def deactivate_trigger(self, trigger_id: str) -> Dict[str, Any]:
        """Deactivate trigger"""
        try:
            response_from_db = self.orchestrator.deactivate_trigger(trigger_id)
            
            # Reload trigger in manager (will stop handler)
            await self.trigger_manager.reload_trigger(trigger_id)
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Trigger deactivated successfully"
            }
        except Exception as e:
            self.logger.error(f"Failed to deactivate trigger {trigger_id}: {str(e)}")
            raise

    async def reload_trigger(self, trigger_id: str) -> Dict[str, Any]:
        """Reload trigger in manager"""
        try:
            success = await self.trigger_manager.reload_trigger(trigger_id)
            
            return {
                'action_status': success,
                'trigger_id': trigger_id,
                'message': "Trigger reloaded successfully" if success else "Failed to reload trigger"
            }
        except Exception as e:
            self.logger.error(f"Failed to reload trigger {trigger_id}: {str(e)}")
            raise

    # ==========================================
    # WEBHOOK OPERATIONS
    # ==========================================

    def get_webhook_info(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook information"""
        try:
            return self.trigger_manager.get_webhook_info(webhook_id)
        except Exception as e:
            self.logger.error(f"Failed to get webhook info {webhook_id}: {str(e)}")
            raise

    def get_all_webhooks(self) -> List[Dict[str, Any]]:
        """Get all active webhook information"""
        try:
            return self.trigger_manager.get_all_webhooks()
        except Exception as e:
            self.logger.error(f"Failed to get all webhooks: {str(e)}")
            raise

    def validate_webhook_id_availability(self, webhook_id: str) -> bool:
        """Check if webhook ID is available"""
        try:
            return self.orchestrator.check_webhook_id_availability(webhook_id)
        except Exception as e:
            self.logger.error(f"Failed to validate webhook ID {webhook_id}: {str(e)}")
            raise

    # ==========================================
    # STATISTICS AND MONITORING
    # ==========================================

    def get_trigger_statistics(self) -> Dict[str, Any]:
        """Get trigger statistics"""
        try:
            return self.orchestrator.get_trigger_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get trigger statistics: {str(e)}")
            raise

    def get_trigger_handler_status(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """Get trigger handler status"""
        try:
            return self.trigger_manager.get_handler_status(trigger_id)
        except Exception as e:
            self.logger.error(f"Failed to get handler status {trigger_id}: {str(e)}")
            raise

    def get_all_handlers_status(self) -> List[Dict[str, Any]]:
        """Get all trigger handlers status"""
        try:
            return self.trigger_manager.get_all_handlers_status()
        except Exception as e:
            self.logger.error(f"Failed to get all handlers status: {str(e)}")
            raise

    def get_trigger_manager_metrics(self) -> Dict[str, Any]:
        """Get trigger manager metrics"""
        try:
            return self.trigger_manager.get_component_metrics()
        except Exception as e:
            self.logger.error(f"Failed to get trigger manager metrics: {str(e)}")
            raise

    # ==========================================
    # TYPE-SPECIFIC OPERATIONS
    # ==========================================

    async def get_triggers_by_type(self, trigger_type: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get triggers by type"""
        try:
            from miniflow.database.models import TriggerType
            trigger_type_enum = TriggerType(trigger_type)
            
            triggers = self.orchestrator.get_by_type(trigger_type_enum, skip=skip, limit=limit)
            
            simplified_items = [
                self._simplify_trigger_item(trigger) 
                for trigger in triggers
            ]
            
            return {
                'items': simplified_items,
                'total': len(simplified_items),
                'skip': skip,
                'limit': limit,
                'trigger_type': trigger_type
            }
        except Exception as e:
            self.logger.error(f"Failed to get triggers by type {trigger_type}: {str(e)}")
            raise

    def get_schedule_info(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule information for scheduled trigger"""
        try:
            handler = self.trigger_manager.active_handlers.get(trigger_id)
            if handler and hasattr(handler, 'get_schedule_info'):
                return handler.get_schedule_info()
            return None
        except Exception as e:
            self.logger.error(f"Failed to get schedule info {trigger_id}: {str(e)}")
            raise
