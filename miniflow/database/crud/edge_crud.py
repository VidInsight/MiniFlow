from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import Edge
from miniflow.database.crud.base_crud import BaseCRUD


class EdgeCRUD(BaseCRUD[Edge]):
    def __init__(self):
        super().__init__(Edge)
    
    def _create(self, session: Session, **kwargs):
        # Safe key extraction
        workflow_id = kwargs.get("workflow_id")
        from_node_id = kwargs.get("from_node_id")
        to_node_id = kwargs.get("to_node_id")
        
        # Validation
        if not workflow_id:
            raise ValidationError("Workflow ID is required", severity=ErrorSeverity.HIGH)
        if not from_node_id:
            raise ValidationError("From Node ID is required", severity=ErrorSeverity.HIGH)
        if not to_node_id:
            raise ValidationError("To Node ID is required", severity=ErrorSeverity.HIGH)
        if from_node_id == to_node_id:
            raise ValidationError("Self-loops are not allowed", severity=ErrorSeverity.MEDIUM)
            
        # Check for duplicates
        existing = self._filter(session, filters={
            "workflow_id": workflow_id,
            "from_node_id": from_node_id, 
            "to_node_id": to_node_id
        })
        if existing:
            raise ValidationError("Edge already exists between these nodes", severity=ErrorSeverity.MEDIUM)
            
        return super()._create(session, **kwargs)