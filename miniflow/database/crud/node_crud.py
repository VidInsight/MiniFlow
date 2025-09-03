from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import Node
from miniflow.database.crud.base_crud import BaseCRUD


class NodeCRUD(BaseCRUD[Node]):
    def __init__(self):
        super().__init__(Node)

    def _create_with_validation(self, session, workflow_id: str, name: str, **kwargs):
        if not name or not name.strip():
            raise ValidationError("Node name cannot be empty", severity=ErrorSeverity.MEDIUM)

        name = name.strip()
        
        existing = self._filter(session, filters={"name": name, "workflow_id": workflow_id})
        if existing:
            raise ValidationError(f"Node name '{name}' already exists in workflow", severity=ErrorSeverity.MEDIUM)

        node_data = {
            "workflow_id": workflow_id,
            "name": name,
            **kwargs
        }
        return self._create(session, **node_data)

    def _update_with_validation(self, session, record_id: str, **kwargs):
        if 'name' in kwargs and kwargs['name']:
            new_name = kwargs['name'].strip()
            if not new_name:
                raise ValidationError("Node name cannot be empty", severity=ErrorSeverity.MEDIUM)

            node = self._get_by_id(session, record_id)
            if not node:
                raise ValidationError(f"Node '{record_id}' not found", severity=ErrorSeverity.MEDIUM)

            existing = self._filter(session, filters={"name": new_name, "workflow_id": node.workflow_id})
            if existing and existing[0].id != record_id:
                raise ValidationError(f"Node name '{new_name}' already exists in workflow", severity=ErrorSeverity.MEDIUM)

            kwargs['name'] = new_name

        return self._update(session, record_id, **kwargs)