from typing import List, Dict, Any, Optional

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import (
    ResourceNotFound,
    DatabaseError,
    ValidationError,
    ErrorContext,
    ErrorSeverity
)

# Dependencies will be injected via constructor
from miniflow.database.models import EnvironmentVariable, VariableScope, VariableType
from miniflow.database.orchestration.envar_orchestrator import EnvironmentVariableOrchestrator


class EnvironmentVariableActions:
    """BFF Environment Variables operations - Frontend için optimize edilmiş"""

    def __init__(self, orchestrator=None):
        self.logger = get_logger("miniflow_api")
        self.orchestrator: EnvironmentVariableOrchestrator = orchestrator

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for operations"""
        return ErrorContext(operation=operation, component=self.__class__.__name__, additional_info=kwargs)

    # CREATE
    async def create_envar_record(self, name: str, value: str, description: Optional[str] = None, variable_type: str = "string") -> Dict[str, Any]:
        """Create environment variable record"""
        try:
            var_type = VariableType(variable_type.lower())
            variable = self.orchestrator.create_environment_variable(name=name.upper(), value=value, scope=VariableScope.USER, variable_type=var_type, description=description)
            var_dict = variable.to_dict()
            
            return var_dict
        except ValueError as e:
            context = self._create_error_context("create_envar_record", name=name, variable_type=variable_type)
            raise ValidationError(f"Invalid variable type: {variable_type}", context=context, severity=ErrorSeverity.MEDIUM, source_error=e)
        except Exception as e:
            context = self._create_error_context("create_envar_record", name=name, variable_type=variable_type)
            raise DatabaseError(f"Failed to create environment variable '{name}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    # GET
    async def get_envar_record(self, record_id: str) -> Dict[str, Any]:
        try:
            record = self.orchestrator.get_environment_variable_by_id(record_id)
            if not record:
                context = self._create_error_context("get_envar_record", record_id=record_id)
                raise ResourceNotFound(f"Environment variable '{record_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)
            return record.to_dict()
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_envar_record", record_id=record_id)
            raise DatabaseError(f"Failed to retrieve environment variable: {str(e)}", context=context,
                                severity=ErrorSeverity.HIGH, source_error=e)

    # UPDATE
    async def update_envar_record(self, record_id:str, value: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update environment variable record"""
        try:
            update_data = {}
            if value is not None:
                update_data['value'] = value
            if description is not None:
                update_data['description'] = description
            
            if not update_data:
                context = self._create_error_context("update_envar_record", record_id=record_id)
                raise ValidationError("No update data provided", context=context, severity=ErrorSeverity.MEDIUM)
            
            updated_variable = self.orchestrator.update_environment_variable_by_id(record_id, **update_data)
            return updated_variable.to_dict()
        except ValidationError:
            raise
        except Exception as e:
            context = self._create_error_context("update_envar_record", record_id=record_id)
            raise DatabaseError(f"Failed to update environment variable '{record_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    # DELETE
    async def delete_envar_record(self, record_id: str) -> Dict[str, Any]:
        """Delete environment variable record"""
        try:
            deleted_variable = self.orchestrator.delete_environment_variable_by_id(record_id)
            if not deleted_variable:
                context = self._create_error_context("delete_envar_record", record_id=record_id)
                raise ResourceNotFound(f"Environment variable '{record_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)
            return {"deleted": True, "name": record_id, "message": f"Environment variable '{record_id}' deleted successfully"}
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("delete_envar_record", record_id=record_id)
            raise DatabaseError(f"Failed to delete environment variable '{record_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    # LIST
    async def get_envar_records(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get environment variable records"""
        try:
            variables = self.orchestrator.get_all_environment_variable()
            result = []
            for var in variables:
                result.append(var.to_dict())
            return result
        except Exception as e:
            context = self._create_error_context("get_envar_records", scope=scope)
            raise DatabaseError(f"Failed to retrieve environment variables: {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)