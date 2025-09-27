from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import ExecutionOutput
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionOutputCRUD(BaseCRUD[ExecutionOutput]):
    def __init__(self):
        super().__init__(ExecutionOutput)
        self.required_fields = [
            "execution_id", "workflow_id", "node_id", "status"
        ]
        self.protected_fields = [
            'created_at', 'updated_at', 'id'
        ]

    def _get_inputs_by_execution(self, session: Session, execution_id: str) -> List[ExecutionOutput]:
        return self._filter(session, {'execution_id': execution_id})