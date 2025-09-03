from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import Edge
from miniflow.database.crud.base_crud import BaseCRUD


class EdgeCRUD(BaseCRUD[Edge]):
    def __init__(self):
        super().__init__(Edge)

    def _create_with_validation(self, session, workflow_id: str, from_node_id: str, to_node_id: str, **kwargs):
        if not workflow_id or not workflow_id.strip():
            raise ValidationError("Workflow ID cannot be empty", severity=ErrorSeverity.MEDIUM)

        if not from_node_id or not from_node_id.strip():
            raise ValidationError("From node ID cannot be empty", severity=ErrorSeverity.MEDIUM)

        if not to_node_id or not to_node_id.strip():
            raise ValidationError("To node ID cannot be empty", severity=ErrorSeverity.MEDIUM)

        if from_node_id == to_node_id:
            raise ValidationError("From and to nodes cannot be the same", severity=ErrorSeverity.MEDIUM)

        workflow_id = workflow_id.strip()
        from_node_id = from_node_id.strip()
        to_node_id = to_node_id.strip()

        existing = self._filter(session, filters={
            "workflow_id": workflow_id,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id
        })
        if existing:
            raise ValidationError(f"Edge already exists between nodes '{from_node_id}' and '{to_node_id}' in workflow", severity=ErrorSeverity.MEDIUM)

        edge_data = {
            "workflow_id": workflow_id,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            **kwargs
        }
        return self._create(session, **edge_data)

    def _update_with_validation(self, session, record_id: str, **kwargs):
        if 'condition_type' in kwargs and kwargs['condition_type']:
            condition_type = kwargs['condition_type']
            if hasattr(condition_type, 'value'):
                condition_type = condition_type.value
            
            valid_condition_types = ['SUCCESS', 'FAILURE', 'ALWAYS', 'CONDITIONAL']
            if condition_type not in valid_condition_types:
                raise ValidationError(f"Invalid condition type. Must be one of: {', '.join(valid_condition_types)}", severity=ErrorSeverity.MEDIUM)
            kwargs['condition_type'] = condition_type

        return self._update(session, record_id, **kwargs)