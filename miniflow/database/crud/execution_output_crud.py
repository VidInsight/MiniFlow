from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import ExecutionOutput
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionOutputCRUD(BaseCRUD[ExecutionOutput]):
    def __init__(self):
        super().__init__(ExecutionOutput)