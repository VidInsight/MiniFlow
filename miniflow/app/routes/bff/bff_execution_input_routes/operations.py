"""
Execution Input Operations (READ-ONLY)
"""

from typing import List, Dict, Any, Optional

from miniflow.core.logger import get_logger
from ..base_operations import BaseBFFOperations
from .schemas import ExecutionInputFilterRequest
from miniflow.database.orchestration.execution_input_orchestrator import ExecutionInputOrchestrator


class ExecutionInputOperations(BaseBFFOperations[ExecutionInputOrchestrator]):
    def __init__(self, orchestrator: ExecutionInputOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "execution_input")

    # CAPABILITY OVERRIDES - READ-ONLY entity
    @property
    def supports_create(self) -> bool:
        """Execution inputs cannot be created via API - they are created by the engine"""
        return False
    
    @property 
    def supports_update(self) -> bool:
        """Execution inputs cannot be updated via API - they are managed by the engine"""
        return False
    
    @property
    def supports_delete(self) -> bool:
        """Execution inputs cannot be deleted via API - they are managed by the engine"""
        return False
    
    @property
    def supports_filter(self) -> bool:
        """Execution inputs support filtering for monitoring purposes"""
        return True

    # GET BY ID
    async def get_execution_input_record(self, record_id: str, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id, include_relationships, exclude_fields)
        return response_from_db

    # LIST ALL
    async def list_execution_input_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)
        return response_from_db

    # COUNT
    async def count_execution_input_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_execution_input_records(self, request: ExecutionInputFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)
        return response_from_db
