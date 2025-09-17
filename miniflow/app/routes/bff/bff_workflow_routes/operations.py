"""
Workflow Operations
"""

from typing import List, Dict, Any, Optional

from ..base_operations import BaseBFFOperations
from .schemas import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowFilterRequest

from miniflow.core.logger import get_logger
from miniflow.database.orchestration.workflow_orchestrator import WorkflowOrchestrator



class WorkflowOperations(BaseBFFOperations[WorkflowOrchestrator]):
    def __init__(self, orchestrator: WorkflowOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "workflow")
    
    def _simplify_workflow_item(self, item: Dict[str, Any], exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Workflow verisini sade format'a çevir - Auto-reload test"""
        # Tüm alanları kopyala (ilişkiler dahil)
        result = item.copy()
        
        # Exclude fields'i uygula
        if exclude_fields:
            for field in exclude_fields:
                result.pop(field, None)
                
        return result

    # CREATE
    async def create_workflow_record(self, request: WorkflowCreateRequest) -> Dict[str, Any]:
        response_from_db = await self._create_record(**request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Workflow creation successful"
        }

    # GET BY ID
    async def get_workflow_record(self, record_id: str, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id, include_relationships, exclude_fields)
        return self._simplify_workflow_item(response_from_db, exclude_fields)

    # UPDATE
    async def update_workflow_record(self, record_id: str, request: WorkflowUpdateRequest) -> Dict[str, Any]:
        response_from_db = await self._update_record(record_id, **request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Workflow update successful"
        }

    # DELETE
    async def delete_workflow_record(self, record_id: str) -> Dict[str, Any]:
        response_from_db = await self._delete_record(record_id)
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Workflow delete successful"
        }

    # LIST ALL
    async def list_workflow_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)
        
        # Sade format için sadece temel alanları filtrele
        simplified_items = [
            self._simplify_workflow_item(item, exclude_fields) 
            for item in response_from_db.get('items', [])
        ]
        
        return {
            'items': simplified_items,
            'total': response_from_db.get('total', 0),
            'skip': response_from_db.get('skip', skip),
            'limit': response_from_db.get('limit', limit)
        }

    # COUNT
    async def count_workflow_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_workflow_records(self, request: WorkflowFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)
        
        # Sade format için sadece temel alanları filtrele
        simplified_items = [
            self._simplify_workflow_item(item, request.exclude_fields) 
            for item in response_from_db.get('items', [])
        ]
        
        return {
            'items': simplified_items,
            'total': response_from_db.get('total', 0),
            'skip': response_from_db.get('skip', request.skip),
            'limit': response_from_db.get('limit', request.limit)
        }

    # GET STATS
    async def get_stats(self, request_id: str) -> Dict[str, Any]:
        response_from_db = await self.orchestrator.get_stats(request_id)
        return response_from_db