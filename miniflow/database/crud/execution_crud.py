from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Execution
from ..enums import ExecutionStatus
from .base_crud import BaseCRUD


class ExecutionCRUD(BaseCRUD[Execution]):
    def __init__(self):
        super().__init__(Execution)
        self.model_fields = {column.name for column in Execution.__table__.columns}
        self.required_fields = {'workflow_id'}  # trigger_id is nullable, pending_nodes has default
        self.protected_fields = {'workflow_id', 'trigger_id', 'correlation_id'}

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> Execution:
        """Create a new execution with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate workflow_id
        workflow_id = kwargs.get('workflow_id')
        kwargs['workflow_id'] = validators.validate_record_id(component=self.model_name, record_id=workflow_id)
        
        # Validate trigger_id if provided
        trigger_id = kwargs.get('trigger_id')
        kwargs['trigger_id'] = validators.validate_record_id(component=self.model_name, record_id=trigger_id)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        execution = super()._create(session, **kwargs)
        return execution

    def _update(self, session: Session, record_id: str, **kwargs) -> Execution:
        """Update execution with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        execution = super()._update(session, record_id, **kwargs)
        return execution

    # =================================================================================== ORCHESTRATION OPERATIONS =====
    def _increment_running_nodes(self, session: Session, record_id: str, increment: int = 1) -> Execution:
        """Move nodes from pending to running (pending -n, running +n)."""
        # Validate increment value
        if not isinstance(increment, int):
            raise ValueError("Increment must be an integer")
        
        if increment not in [-1, 1]:
            raise ValueError("Increment must be -1 or +1")
        
        try:
            # Get execution with row-level lock (SELECT FOR UPDATE)
            execution = session.query(self.model).filter(
                and_(
                    self.model.id == record_id,
                    self.model.is_deleted == False
                )
            ).with_for_update().first()
            
            if not execution:
                self._raise_not_found_error(operation="increment_running_nodes", record_id=record_id)
            
            # Calculate new values
            new_pending = execution.pending_nodes - increment
            new_running = execution.running_nodes + increment
            
            # Validate new values are not negative
            if new_pending < 0:
                raise ValueError("Pending nodes cannot be negative")
            
            if new_running < 0:
                raise ValueError("Running nodes cannot be negative")
            
            # Update both counters
            execution.pending_nodes = new_pending
            execution.running_nodes = new_running
            session.add(execution)
            session.flush()
            return execution
            
        except (ValidationError, ValueError):
            # Re-raise validation errors without wrapping
            raise
        except Exception as e:
            context = ErrorContext(operation='increment_running_nodes',component=self.model_name,additional_info={'record_id': record_id,'increment': increment})
            raise DatabaseQueryError(f"Failed to increment running nodes for {self.model_name}: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

    def _increment_executed_nodes(self, session: Session, record_id: str, increment: int = 1) -> Execution:
        """Move nodes from running to executed (running -n, executed +n)."""
        # Validate increment value
        if not isinstance(increment, int):
            raise ValueError("Increment must be an integer")
        
        if increment not in [-1, 1]:
            raise ValueError("Increment must be -1 or +1")
        
        try:
            # Get execution with row-level lock (SELECT FOR UPDATE)
            execution = session.query(self.model).filter(
                and_(
                    self.model.id == record_id,
                    self.model.is_deleted == False
                )
            ).with_for_update().first()
            
            if not execution:
                self._raise_not_found_error(operation='increment_executed_nodes',record_id=record_id)
            
            # Calculate new values
            new_running = execution.running_nodes - increment
            new_executed = execution.executed_nodes + increment
            
            # Validate new values are not negative
            if new_running < 0:
                raise ValueError("Running nodes cannot be negative")
            
            if new_executed < 0:
                raise ValueError("Executed nodes cannot be negative")
            
            # Update both counters
            execution.running_nodes = new_running
            execution.executed_nodes = new_executed
            session.add(execution)
            session.flush()
            return execution
            
        except (ValidationError, ValueError):
            # Re-raise validation errors without wrapping
            raise
        except Exception as e:
            context = ErrorContext(operation='increment_executed_nodes',component=self.model_name,additional_info={'record_id': record_id,'increment': increment})
            raise DatabaseQueryError(f"Failed to increment executed nodes for {self.model_name}: {str(e)}",context=context,severity=ErrorSeverity.HIGH)

    def _set_results(self, session: Session, record_id: str, results: dict, merge: bool = False) -> Execution:
        """Set or merge execution results."""
        # Validate results
        if not isinstance(results, dict):
            raise ValueError("Results must be a dictionary")
        
        try:
            # Get execution with row-level lock (SELECT FOR UPDATE)
            execution = session.query(self.model).filter(
                and_(
                    self.model.id == record_id,
                    self.model.is_deleted == False
                )
            ).with_for_update().first()
            
            if not execution:
                self._raise_not_found_error(operation='set_results',record_id=record_id)
            
            # Set or merge results
            if merge:
                # Merge new results with existing ones
                current_results = execution.results or {}
                current_results.update(results)
                execution.results = current_results
            else:
                # Replace results entirely
                execution.results = results
            
            session.add(execution)
            session.flush()
            return execution
            
        except (ValidationError, ValueError):
            raise
        except Exception as e:
            context = ErrorContext( operation='set_results', component=self.model_name, additional_info={'record_id': record_id,'merge': merge})
            raise DatabaseQueryError(f"Failed to set results for {self.model_name}: {str(e)}",context=context,severity=ErrorSeverity.HIGH)