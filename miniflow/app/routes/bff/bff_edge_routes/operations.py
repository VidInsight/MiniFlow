"""
Edge Operations
"""

from typing import List, Dict, Any, Optional

from miniflow.core.logger import get_logger
from ..base_operations import BaseBFFOperations
from .schemas import EdgeCreateRequest, EdgeUpdateRequest, EdgeFilterRequest
from miniflow.database.orchestration.edge_orchestrator import EdgeOrchestrator


class EdgeOperations(BaseBFFOperations[EdgeOrchestrator]):
    def __init__(self, orchestrator: EdgeOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "edge")

    # CREATE
    async def create_edge_record(self, request: EdgeCreateRequest) -> Dict[str, Any]:
        response_from_db = await self._create_record(**request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Edge creation successful"
        }

    # GET BY ID
    async def get_edge_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id)
        return response_from_db

    # UPDATE
    async def update_edge_record(self, record_id: str, request: EdgeUpdateRequest) -> Dict[str, Any]:
        response_from_db = await self._update_record(record_id, **request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Edge update successful"
        }

    # DELETE
    async def delete_edge_record(self, record_id: str) -> Dict[str, Any]:
        response_from_db = await self._delete_record(record_id)
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Edge delete successful"
        }

    # LIST ALL
    async def list_edge_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)
        return response_from_db

    # COUNT
    async def count_edge_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_edge_records(self, request: EdgeFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)
        return response_from_db
