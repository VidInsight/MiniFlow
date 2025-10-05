from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Permission
from ..enums import Roles, Plans
from .base_crud import BaseCRUD


class PermissionCRUD(BaseCRUD[Permission]):
    def __init__(self):
        super().__init__(Permission)
        self.model_fields = {column.name for column in Permission.__table__.columns}
        self.required_fields = {'name', 'required_role', 'required_plan'}
        self.protected_fields = {'name'}  # Permission name shouldn't change

