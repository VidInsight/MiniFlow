from miniflow.database.models import EnvironmentVariable
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class EnvironmentVariableCRUD(BaseCRUD[EnvironmentVariable]):
    def __init__(self):
        super().__init__(EnvironmentVariable)