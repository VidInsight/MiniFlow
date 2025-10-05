from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import ExecutionOutput
from .base_crud import BaseCRUD


class ExecutionOutputCRUD(BaseCRUD[ExecutionOutput]):
    def __init__(self):
        super().__init__(ExecutionOutput)
        self.model_fields = {column.name for column in ExecutionOutput.__table__.columns}
        self.required_fields = {'execution_id', 'workflow_id', 'status'}
        self.protected_fields = {'execution_id', 'workflow_id', 'node_id'}

    def _create(self, session: Session, **kwargs) -> ExecutionOutput:
        """Create a new execution output record with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate execution_id
        execution_id = kwargs.get('execution_id')
        if execution_id:
            kwargs['execution_id'] = validators._validate_id(execution_id)
        
        # Validate workflow_id
        workflow_id = kwargs.get('workflow_id')
        if workflow_id:
            kwargs['workflow_id'] = validators._validate_id(workflow_id)
        
        # Validate node_id if provided
        node_id = kwargs.get('node_id')
        if node_id:
            kwargs['node_id'] = validators._validate_id(node_id)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        execution_output = super()._create(session, **kwargs)
        return execution_output

    def _collect_all_results_by_execution_id(self, session: Session, execution_id: str) -> dict:
        """Collect all output results for a specific execution into a single dictionary."""
        try:
            execution_id = validators._validate_id(execution_id)
            outputs = self._get_by_execution_id(session, execution_id)
            collected_results = {}
            
            for output in outputs:
                node_key = output.node_id if output.node_id else f"unknown_{output.id}"
                node_result = {"status": output.status.value if hasattr(output.status, 'value') else str(output.status)}
                
                if output.result_data and isinstance(output.result_data, dict):
                    for key, value in output.result_data.items():
                        if key not in node_result:  
                            node_result[key] = value
                
                collected_results[node_key] = node_result
            
            return collected_results
            
        except Exception as e:
            context = ErrorContext(operation='collect_all_results_by_execution_id',component=self.model_name,additional_info={'execution_id': execution_id})
            raise DatabaseQueryError(f"Failed to collect results for {self.model_name} by execution_id: {str(e)}",context=context,severity=ErrorSeverity.HIGH)