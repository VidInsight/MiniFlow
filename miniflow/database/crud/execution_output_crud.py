"""
ExecutionOutput CRUD Operations

Database operations for ExecutionOutput model.
READ-ONLY operations for execution results monitoring and analysis.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from miniflow.database.models import ExecutionOutput
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionOutputCRUD(BaseCRUD[ExecutionOutput]):
    """ExecutionOutput CRUD operations (READ-ONLY)"""

    def __init__(self):
        """Initialize ExecutionOutput CRUD with model"""
        super().__init__(ExecutionOutput)

    def get_execution_output_by_id(self, session: Session, execution_output_id: str) -> Optional[ExecutionOutput]:
        """
        Get execution output by ID
        
        Args:
            session: Database session
            execution_output_id: ID of the execution output
            
        Returns:
            ExecutionOutput instance or None
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.id == execution_output_id).first()

    def get_all_execution_outputs(self, session: Session, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get all execution outputs with pagination
        
        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionOutput instances
        """
        return self.get_all(session, skip=skip, limit=limit)

    def get_execution_outputs_by_execution(self, session: Session, execution_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by execution ID
        
        Args:
            session: Database session
            execution_id: ID of the execution
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionOutput instances for the execution
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.execution_id == execution_id).offset(skip).limit(limit).all()

    def get_execution_outputs_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by workflow ID
        
        Args:
            session: Database session
            workflow_id: ID of the workflow
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionOutput instances for the workflow
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.workflow_id == workflow_id).offset(skip).limit(limit).all()

    def get_execution_outputs_by_node(self, session: Session, node_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by node ID
        
        Args:
            session: Database session
            node_id: ID of the node
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionOutput instances for the node
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.node_id == node_id).offset(skip).limit(limit).all()

    def get_execution_outputs_by_status(self, session: Session, status: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by status
        
        Args:
            session: Database session
            status: Status to filter by (SUCCESS, FAILED, TIMEOUT, CANCELLED)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionOutput instances with the specified status
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.status == status).offset(skip).limit(limit).all()

    def count_execution_outputs(self, session: Session) -> int:
        """
        Count total execution outputs
        
        Args:
            session: Database session
            
        Returns:
            Total number of execution outputs
        """
        return session.query(ExecutionOutput).count()

    def count_execution_outputs_by_execution(self, session: Session, execution_id: str) -> int:
        """
        Count execution outputs by execution ID
        
        Args:
            session: Database session
            execution_id: ID of the execution
            
        Returns:
            Number of execution outputs for the execution
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.execution_id == execution_id).count()

    def count_execution_outputs_by_workflow(self, session: Session, workflow_id: str) -> int:
        """
        Count execution outputs by workflow ID
        
        Args:
            session: Database session
            workflow_id: ID of the workflow
            
        Returns:
            Number of execution outputs for the workflow
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.workflow_id == workflow_id).count()

    def count_execution_outputs_by_node(self, session: Session, node_id: str) -> int:
        """
        Count execution outputs by node ID
        
        Args:
            session: Database session
            node_id: ID of the node
            
        Returns:
            Number of execution outputs for the node
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.node_id == node_id).count()

    def count_execution_outputs_by_status(self, session: Session, status: str) -> int:
        """
        Count execution outputs by status
        
        Args:
            session: Database session
            status: Status to filter by
            
        Returns:
            Number of execution outputs with the specified status
        """
        return session.query(ExecutionOutput).filter(ExecutionOutput.status == status).count()
