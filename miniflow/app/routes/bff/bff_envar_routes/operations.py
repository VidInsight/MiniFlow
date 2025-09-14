"""
Environment Variable Operations
"""

from typing import List, Dict, Any, Optional

from miniflow.core.logger import get_logger
from ..base_operations import BaseBFFOperations
from .schemas import EnvironmentVariableCreateRequest, EnvironmentVariableUpdateRequest, EnvironmentVariableFilterRequest
from miniflow.database.models import EnvironmentVariable, VariableScope, VariableType
from miniflow.database.orchestration.envar_orchestrator import EnvironmentVariableOrchestrator



class EnvironmentVariableOperations(BaseBFFOperations[EnvironmentVariableOrchestrator]):
    def __init__(self, orchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "environment_variable")


    # CREATE
    async def create_envar_record(self, request: EnvironmentVariableCreateRequest) -> Dict[str, Any]:
        response_from_db = await self._create_record(**request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Environment Variable creation successful"
        }

    # GET BY ID
    async def get_envar_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id)
        return response_from_db

    # UPDATE
    async def update_envar_record(self, record_id: str, request: EnvironmentVariableUpdateRequest) -> Dict[str, Any]:
        response_from_db = await self._update_record(record_id, **request.to_dict())
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Environment Variable update successful"
        }

    # DELETE
    async def delete_envar_record(self, record_id: str) -> Dict[str, Any]:
        response_from_db = await self._delete_record(record_id)
        return {
            'action_status': True,
            'record_id': response_from_db['id'],
            'message': "Environment Variable delete successful"
        }

    # LIST ALL
    async def list_envar_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)
        return response_from_db

    # COUNT
    async def count_envar_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_envar_records(self, request: EnvironmentVariableFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)
        return response_from_db