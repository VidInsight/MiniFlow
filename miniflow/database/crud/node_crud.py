from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import Node
from miniflow.database.crud.base_crud import BaseCRUD


class NodeCRUD(BaseCRUD[Node]):
    def __init__(self):
        super().__init__(Node)

    def _create(self, session: Session, **kwargs):
        # Safe key extraction
        name = kwargs.get("name")
        workflow_id = kwargs.get("workflow_id")

        if not name or not name.strip():
            raise ValidationError("Node name cannot be empty", severity=ErrorSeverity.MEDIUM)
        if not workflow_id:
            raise ValidationError("Workflow ID is required", severity=ErrorSeverity.MEDIUM)

        name = name.strip()

        existing = self._filter(session, filters={"name": name, "workflow_id": workflow_id})
        if existing:
            raise ValidationError(f"Node name '{name}' already exists in workflow", severity=ErrorSeverity.MEDIUM)

        # Update kwargs with normalized values
        kwargs["name"] = name
        kwargs["workflow_id"] = workflow_id
        return super()._create(session, **kwargs)

    def _update(self, session: Session, record_id: str, **kwargs):
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

        return super()._update(session, record_id, **kwargs)