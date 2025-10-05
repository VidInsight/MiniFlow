from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import ExecutionInput
from .base_crud import BaseCRUD


class ExecutionInputCRUD(BaseCRUD[ExecutionInput]):
    def __init__(self):
        super().__init__(ExecutionInput)
        self.model_fields = {column.name for column in ExecutionInput.__table__.columns}
        self.required_fields = {'execution_id', 'workflow_id', 'node_name', 'script_name', 'script_path'}  # node_id optional due to ondelete='SET NULL'
        self.protected_fields = {'execution_id', 'workflow_id', 'node_id'}

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> ExecutionInput:
        """Create a new execution input record with validation."""
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
        
        # Validate node_name
        node_name = kwargs.get('node_name')
        kwargs['node_name'] = validators._validate_name(node_name)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        execution_input = super()._create(session, **kwargs)
        return execution_input

    def _increase_wait_factor(self, session: Session, record_id: str) -> ExecutionInput:
        """Increase the wait factor for a specific execution input."""
        execution_input = super()._get_by_id(session, record_id)
        if not execution_input:
            context = ErrorContext(operation='increase_wait_factor',component=self.model_name,additional_info={'id': record_id})
            raise ValidationError(f"{self.model_name} with ID {record_id} does not exist",severity=ErrorSeverity.HIGH,context=context)
        
        # Increment wait_factor
        execution_input.wait_factor += 1
        session.add(execution_input)
        session.flush()
        
        return execution_input

    def _get_ready_to_process(self, session: Session, limit: int = 10) -> list[ExecutionInput]:
        """Get execution inputs ready to process with starvation prevention."""
        try:
            # Validate limit
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("Limit must be a positive integer")
            
            # Query ALL execution inputs with dependency_count = 0, ordered by computed priority
            all_ready = session.query(self.model).filter(
                and_(
                    self.model.dependency_count == 0,
                    self.model.is_deleted == False
                )
            ).order_by(
                # Computed priority: priority + (wait_factor * 10)
                (self.model.priority + (self.model.wait_factor * 10)).desc(),
                self.model.created_at.asc()  # FIFO for same priority
            ).all()
            
            # If no ready records, return empty list
            if not all_ready:
                return []
            
            # Split into two groups: to process (limit) and to wait (remaining)
            to_process = all_ready[:limit]
            to_wait = all_ready[limit:]
            
            # Increase wait_factor for records that didn't make the cut (starvation prevention)
            if to_wait:
                for record in to_wait:
                    record.wait_factor += 1
                    session.add(record)
                
                # Flush to persist wait_factor updates
                session.flush()
            
            return to_process
            
        except Exception as e:
            context = ErrorContext(operation='get_ready_to_process',component=self.model_name,additional_info={'limit': limit})
            raise DatabaseQueryError(f"Failed to get ready-to-process {self.model_name} records: {str(e)}",context=context,severity=ErrorSeverity.HIGH)
