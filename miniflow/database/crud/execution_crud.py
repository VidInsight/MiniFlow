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

    def _create(self, session: Session, **kwargs) -> Execution:
        """Create a new execution with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate workflow_id
        workflow_id = kwargs.get('workflow_id')
        if workflow_id:
            kwargs['workflow_id'] = validators._validate_id(workflow_id)
        
        # Validate trigger_id if provided
        trigger_id = kwargs.get('trigger_id')
        if trigger_id:
            kwargs['trigger_id'] = validators._validate_id(trigger_id)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        execution = super()._create(session, **kwargs)
        return execution

    def _update(self, session: Session, record_id: str, **kwargs) -> Execution:
        """Update execution with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        execution = super()._update(session, record_id, **kwargs)
        return execution

    def _get_by_workflow_id(self, session: Session, workflow_id: str, skip: int = 0, limit: int = None) -> list[Execution]:
        """Get executions for a specific workflow with pagination."""
        try:
            # Validate workflow_id
            workflow_id = validators._validate_id(workflow_id)
            
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            # Query executions filtered by workflow_id
            query = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.started_at.desc()
            ).offset(skip)
            
            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(
                operation='get_by_workflow_id',
                component=self.model_name,
                additional_info={'workflow_id': workflow_id, 'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} records by workflow_id: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _count_by_workflow_id(self, session: Session, workflow_id: str) -> int:
        """Get total count of executions for a specific workflow."""
        try:
            # Validate workflow_id
            workflow_id = validators._validate_id(workflow_id)
            
            # Count executions filtered by workflow_id
            count = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(
                operation='count_by_workflow_id',
                component=self.model_name,
                additional_info={'workflow_id': workflow_id}
            )
            raise DatabaseQueryError(
                f"Failed to count {self.model_name} records by workflow_id: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_by_status(self, session: Session, status: ExecutionStatus, skip: int = 0, limit: int = None) -> list[Execution]:
        """Get executions by status with pagination."""
        try:
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            # Query executions filtered by status
            query = session.query(self.model).filter(
                and_(
                    self.model.status == status,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.started_at.desc()
            ).offset(skip)
            
            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(
                operation='get_by_status',
                component=self.model_name,
                additional_info={'status': str(status), 'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} records by status: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_active_executions(self, session: Session, skip: int = 0, limit: int = None) -> list[Execution]:
        """Get all active (PENDING, RUNNING) executions."""
        try:
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            # Query active executions
            query = session.query(self.model).filter(
                and_(
                    self.model.status.in_([
                        ExecutionStatus.PENDING,
                        ExecutionStatus.RUNNING
                    ]),
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.started_at.asc()
            ).offset(skip)
            
            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(
                operation='get_active_executions',
                component=self.model_name,
                additional_info={'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get active {self.model_name} records: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_active_executions_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = None) -> list[Execution]:
        """Get all active (PENDING, RUNNING) executions."""
        try:
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")

            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")

            validators._validate_id(workflow_id)

            # Query active executions
            query = session.query(self.model).filter(
                and_(
                    self.model.status.in_([
                        ExecutionStatus.PENDING,
                        ExecutionStatus.RUNNING
                    ]),
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.started_at.asc()
            ).offset(skip)

            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)

            results = query.all()
            return results

        except Exception as e:
            context = ErrorContext(
                operation='get_active_executions',
                component=self.model_name,
                additional_info={'offset': skip, 'limit': limit}
            )
            raise DatabaseQueryError(
                f"Failed to get active {self.model_name} records: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _increment_running_nodes(self, session: Session, record_id: str, increment: int = 1) -> Execution:
        """
        Move nodes from pending to running (pending -n, running +n).
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            session: Database session
            record_id: Execution ID
            increment: Amount to move (+1) or reverse (-1)
        
        Returns:
            Updated Execution object
        """
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
                raise ValidationError(
                    f"{self.model_name} with ID {record_id} not found",
                    context=ErrorContext(
                        operation='increment_running_nodes',
                        component=self.model_name,
                        additional_info={'record_id': record_id}
                    ),
                    severity=ErrorSeverity.MEDIUM
                )
            
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
            context = ErrorContext(
                operation='increment_running_nodes',
                component=self.model_name,
                additional_info={
                    'record_id': record_id,
                    'increment': increment
                }
            )
            raise DatabaseQueryError(
                f"Failed to increment running nodes for {self.model_name}: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _increment_executed_nodes(self, session: Session, record_id: str, increment: int = 1) -> Execution:
        """
        Move nodes from running to executed (running -n, executed +n).
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            session: Database session
            record_id: Execution ID
            increment: Amount to move (+1) or reverse (-1)
        
        Returns:
            Updated Execution object
        """
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
                raise ValidationError(
                    f"{self.model_name} with ID {record_id} not found",
                    context=ErrorContext(
                        operation='increment_executed_nodes',
                        component=self.model_name,
                        additional_info={'record_id': record_id}
                    ),
                    severity=ErrorSeverity.MEDIUM
                )
            
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
            context = ErrorContext(
                operation='increment_executed_nodes',
                component=self.model_name,
                additional_info={
                    'record_id': record_id,
                    'increment': increment
                }
            )
            raise DatabaseQueryError(
                f"Failed to increment executed nodes for {self.model_name}: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_by_correlation_id(self, session: Session, correlation_id: str) -> Execution:
        """Get execution by correlation ID."""
        # Validate correlation_id before database operations
        if not correlation_id or not isinstance(correlation_id, str):
            raise ValueError("Correlation ID must be a non-empty string")
        
        try:
            execution = session.query(self.model).filter(
                and_(
                    self.model.correlation_id == correlation_id,
                    self.model.is_deleted == False
                )
            ).first()
            
            return execution
            
        except ValueError:
            # Re-raise validation errors without wrapping
            raise
        except Exception as e:
            context = ErrorContext(
                operation='get_by_correlation_id',
                component=self.model_name,
                additional_info={'correlation_id': correlation_id}
            )
            raise DatabaseQueryError(
                f"Failed to get {self.model_name} by correlation_id: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _set_results(self, session: Session, record_id: str, results: dict, merge: bool = False) -> Execution:
        """
        Set or merge execution results.
        Uses SELECT FOR UPDATE to prevent race conditions when merging.
        
        Args:
            session: Database session
            record_id: Execution ID
            results: Results dictionary to set/merge
            merge: If True, merge with existing results; if False, replace
        
        Returns:
            Updated Execution object
        """
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
                raise ValidationError(
                    f"{self.model_name} with ID {record_id} not found",
                    context=ErrorContext(
                        operation='set_results',
                        component=self.model_name,
                        additional_info={'record_id': record_id}
                    ),
                    severity=ErrorSeverity.MEDIUM
                )
            
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
            # Re-raise validation errors without wrapping
            raise
        except Exception as e:
            context = ErrorContext(
                operation='set_results',
                component=self.model_name,
                additional_info={
                    'record_id': record_id,
                    'merge': merge
                }
            )
            raise DatabaseQueryError(
                f"Failed to set results for {self.model_name}: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )