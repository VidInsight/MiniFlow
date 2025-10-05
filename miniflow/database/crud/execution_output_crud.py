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

    def _get_by_execution_id(self, session: Session, execution_id: str, skip: int = 0, limit: int = None) -> list[ExecutionOutput]:
        """Get execution outputs for a specific execution with pagination."""
        try:
            # Validate execution_id
            execution_id = validators._validate_id(execution_id)
            
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            # Query execution outputs filtered by execution_id
            query = session.query(self.model).filter(
                and_(
                    self.model.execution_id == execution_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.asc()
            ).offset(skip)
            
            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_execution_id',component=self.model_name,additional_info={'execution_id': execution_id,'offset': skip,'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} records by execution_id: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

    def _count_by_execution_id(self, session: Session, execution_id: str) -> int:
        """Get total count of execution outputs for a specific execution."""
        try:
            # Validate execution_id
            execution_id = validators._validate_id(execution_id)
            
            # Count execution outputs filtered by execution_id
            count = session.query(self.model).filter(
                and_(
                    self.model.execution_id == execution_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(operation='count_by_execution_id',component=self.model_name,additional_info={'execution_id': execution_id})
            raise DatabaseQueryError(f"Failed to count {self.model_name} records by execution_id: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

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