"""
Trigger Operations
"""

from typing import List, Dict, Any, Optional

from ..base_operations import BaseBFFOperations
from .schemas import TriggerCreateRequest, TriggerUpdateRequest, TriggerFilterRequest, TriggerExecutionRequest

from miniflow.core.logger import get_logger
from miniflow.database.orchestration.trigger_orchestrator import TriggerOrchestrator


class TriggerOperations(BaseBFFOperations[TriggerOrchestrator]):
    def __init__(self, orchestrator: TriggerOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "trigger")
    
    def _simplify_trigger_item(self, item: Dict[str, Any], exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Trigger verisini sade format'a çevir"""
        # Tüm alanları kopyala (ilişkiler dahil)
        result = item.copy()
        
        # Exclude fields'i uygula
        if exclude_fields:
            for field in exclude_fields:
                result.pop(field, None)
                
        return result

    # CREATE
    async def create_trigger_record(self, request: TriggerCreateRequest) -> Dict[str, Any]:
        response_from_db = await self._create_record(**request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Trigger creation successful"
        }

    # GET BY ID
    async def get_trigger_record(self, record_id: str, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id, include_relationships, exclude_fields)
        return self._simplify_trigger_item(response_from_db, exclude_fields)

    # UPDATE
    async def update_trigger_record(self, record_id: str, request: TriggerUpdateRequest) -> Dict[str, Any]:
        response_from_db = await self._update_record(record_id, **request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Trigger update successful"
        }

    # DELETE
    async def delete_trigger_record(self, record_id: str) -> Dict[str, Any]:
        response_from_db = await self._delete_record(record_id)
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Trigger delete successful"
        }

    # LIST ALL
    async def list_trigger_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)
        
        # Sade format için sadece temel alanları filtrele
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

    # COUNT
    async def count_trigger_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_trigger_records(self, request: TriggerFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)
        
        # Sade format için sadece temel alanları filtrele
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

    # TRIGGER EXECUTION METHODS
    
    async def trigger_by_api(self, trigger_id: str, request: TriggerExecutionRequest) -> Dict[str, Any]:
        """API trigger execution"""
        try:
            self.logger.info(f"Triggering API trigger: {trigger_id}")
            result = self.orchestrator.trigger_by_api(
                trigger_id=trigger_id,
                correlation_id=request.correlation_id,
                trigger_data=request.trigger_data
            )
            
            return {
                'execution_id': result.get('id'),
                'workflow_id': result.get('workflow_id'),
                'trigger_id': trigger_id,
                'correlation_id': result.get('correlation_id'),
                'nodes_count': result.get('nodes_count', 0),
                'execution_inputs_count': result.get('execution_inputs_count', 0),
                'status': result.get('status'),
                'message': "API trigger execution successful"
            }
        except Exception as e:
            self.logger.error(f"Failed to trigger API trigger {trigger_id}: {str(e)}")
            raise

    async def trigger_by_webhook(self, trigger_id: str, request: TriggerExecutionRequest) -> Dict[str, Any]:
        """Webhook trigger execution"""
        try:
            self.logger.info(f"Triggering webhook trigger: {trigger_id}")
            result = self.orchestrator.trigger_by_webhook(
                trigger_id=trigger_id,
                correlation_id=request.correlation_id,
                trigger_data=request.trigger_data
            )
            
            return {
                'execution_id': result.get('id'),
                'workflow_id': result.get('workflow_id'),
                'trigger_id': trigger_id,
                'correlation_id': result.get('correlation_id'),
                'nodes_count': result.get('nodes_count', 0),
                'execution_inputs_count': result.get('execution_inputs_count', 0),
                'status': result.get('status'),
                'message': "Webhook trigger execution successful"
            }
        except Exception as e:
            self.logger.error(f"Failed to trigger webhook trigger {trigger_id}: {str(e)}")
            raise

    async def trigger_by_scheduled(self, trigger_id: str, request: TriggerExecutionRequest) -> Dict[str, Any]:
        """Scheduled trigger execution"""
        try:
            self.logger.info(f"Triggering scheduled trigger: {trigger_id}")
            result = self.orchestrator.trigger_by_scheduled(
                trigger_id=trigger_id,
                correlation_id=request.correlation_id,
                trigger_data=request.trigger_data
            )
            
            return {
                'execution_id': result.get('id'),
                'workflow_id': result.get('workflow_id'),
                'trigger_id': trigger_id,
                'correlation_id': result.get('correlation_id'),
                'nodes_count': result.get('nodes_count', 0),
                'execution_inputs_count': result.get('execution_inputs_count', 0),
                'status': result.get('status'),
                'message': "Scheduled trigger execution successful"
            }
        except Exception as e:
            self.logger.error(f"Failed to trigger scheduled trigger {trigger_id}: {str(e)}")
            raise
