"""
ExecutionInput CRUD Operations

Database operations for ExecutionInput model.
READ-ONLY operations for scheduler monitoring and execution planning.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from miniflow.database.models import ExecutionInput
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionInputCRUD(BaseCRUD[ExecutionInput]):
    """ExecutionInput CRUD operations (READ-ONLY)"""

    def __init__(self):
        """Initialize ExecutionInput CRUD with model"""
        super().__init__(ExecutionInput)

    def get_execution_input_by_id(self, session: Session, execution_input_id: str) -> Optional[ExecutionInput]:
        """
        Get execution input by ID
        
        Args:
            session: Database session
            execution_input_id: ID of the execution input
            
        Returns:
            ExecutionInput instance or None
        """
        return self.get_by_id(session, execution_input_id)

    def get_all_execution_inputs(self, session: Session, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get all execution inputs with pagination
        
        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionInput instances
        """
        return self.get_all(session, skip=skip, limit=limit)

    def get_execution_inputs_by_execution(self, session: Session, execution_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by execution ID
        
        Args:
            session: Database session
            execution_id: ID of the execution
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionInput instances for the execution
        """
        return session.query(ExecutionInput).filter(ExecutionInput.execution_id == execution_id).offset(skip).limit(limit).all()

    def get_execution_inputs_by_node(self, session: Session, node_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by node ID
        
        Args:
            session: Database session
            node_id: ID of the node
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionInput instances for the node
        """
        return session.query(ExecutionInput).filter(ExecutionInput.node_id == node_id).offset(skip).limit(limit).all()

    def get_execution_inputs_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by workflow ID
        
        Args:
            session: Database session
            workflow_id: ID of the workflow
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionInput instances for the workflow
        """
        return session.query(ExecutionInput).filter(ExecutionInput.workflow_id == workflow_id).offset(skip).limit(limit).all()

    def get_execution_inputs_by_priority(self, session: Session, priority: int, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by priority level
        
        Args:
            session: Database session
            priority: Priority level to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExecutionInput instances with the specified priority
        """
        return session.query(ExecutionInput).filter(ExecutionInput.priority == priority).offset(skip).limit(limit).all()

    def count_execution_inputs(self, session: Session) -> int:
        """
        Count total execution inputs
        
        Args:
            session: Database session
            
        Returns:
            Total number of execution inputs
        """
        return session.query(ExecutionInput).count()

    def count_execution_inputs_by_execution(self, session: Session, execution_id: str) -> int:
        """
        Count execution inputs by execution ID
        
        Args:
            session: Database session
            execution_id: ID of the execution
            
        Returns:
            Number of execution inputs for the execution
        """
        return session.query(ExecutionInput).filter(ExecutionInput.execution_id == execution_id).count()

    def count_execution_inputs_by_node(self, session: Session, node_id: str) -> int:
        """
        Count execution inputs by node ID
        
        Args:
            session: Database session
            node_id: ID of the node
            
        Returns:
            Number of execution inputs for the node
        """
        return session.query(ExecutionInput).filter(ExecutionInput.node_id == node_id).count()

    def count_execution_inputs_by_workflow(self, session: Session, workflow_id: str) -> int:
        """
        Count execution inputs by workflow ID
        
        Args:
            session: Database session
            workflow_id: ID of the workflow
            
        Returns:
            Number of execution inputs for the workflow
        """
        return session.query(ExecutionInput).filter(ExecutionInput.workflow_id == workflow_id).count()
