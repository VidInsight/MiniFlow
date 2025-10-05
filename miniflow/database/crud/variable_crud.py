import json
from sqlalchemy.orm import Session

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext
import miniflow.database.validators as validators

from ..models import EnvironmentVariable
from .base_crud import BaseCRUD


class EnvironmentVariableCRUD(BaseCRUD[EnvironmentVariable]):
    def __init__(self):
        super().__init__(EnvironmentVariable)
        self.model_fields = {column.name for column in EnvironmentVariable.__table__.columns}
        self.required_fields = {'name', 'value'}

    def _create(self, session: Session, **kwargs):
        """Create a new environment variable with type validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)

        name = kwargs.get('name')
        kwargs['name'] = validators._validate_name(name)

        value = kwargs.get('value')
        variable_type = kwargs.get('variable_type', 'STRING')
        validators._validate_variable_type(value, variable_type)
        
        # Serialize JSON types (dict/list) to string for database storage
        if variable_type == 'JSON' and isinstance(value, (dict, list)):
            kwargs['value'] = json.dumps(value)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        variable =  super()._create(session, **kwargs)
        return variable

    def _update(self, session: Session, record_id: str, **kwargs):
        """Update environment variable with type validation."""
        if kwargs.get('name'):
            name = kwargs.get('name')
            kwargs['name'] = validators._validate_name(name)

        if kwargs.get('value'):
            value = kwargs.get('value')
            # Get the existing variable_type if not provided in kwargs
            existing_var = super()._get_by_id(session, record_id)
            if existing_var:
                variable_type = kwargs.get('variable_type', existing_var.variable_type.value if hasattr(existing_var.variable_type, 'value') else existing_var.variable_type)
            else:
                variable_type = kwargs.get('variable_type', 'STRING')
            validators._validate_variable_type(value, variable_type)
            
            # Serialize JSON types (dict/list) to string for database storage
            if variable_type == 'JSON' and isinstance(value, (dict, list)):
                kwargs['value'] = json.dumps(value)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        variable = super()._update(session, record_id, **kwargs)
        return variable