from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import ExecutionInput
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionInputCRUD(BaseCRUD[ExecutionInput]):
    def __init__(self):
        super().__init__(ExecutionInput)

    def _get_by_execution(self, session: Session, execution_id: str) -> List[ExecutionInput]:
        return self._filter(session, {'execution_id': execution_id})