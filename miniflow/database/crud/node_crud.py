from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Node
from .base_crud import BaseCRUD


class NodeCRUD(BaseCRUD[Node]):
    def __init__(self):
        super().__init__(Node)
        self.model_fields = {column.name for column in Node.__table__.columns}
        self.required_fields = {'workflow_id', 'name'}
        self.protected_fields = {'workflow_id', 'script_id', 'created_at', 'updated_at', 'is_deleted'}

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> Node:
        """Create a new node with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate workflow_id
        workflow_id = kwargs['workflow_id']
        kwargs['workflow_id'] = validators.validate_record_id(component=self.model_name, record_id=workflow_id)
        
        # Validate script_id if provided
        script_id = kwargs['script_id']
        kwargs['script_id'] = validators.validate_record_id(component=self.model_name, record_id=script_id)
        
        # Validate name
        name = kwargs['name']
        kwargs['name'] = validators.validate_name(component=self.model_name, name=name)

        # Validate Script Path
        script_path = kwargs['script_path']
        validators.validate_file_path(component=self.model_name, file_path=script_path)
        
        # Validate max_retries if provided
        max_retries = kwargs.get('max_retries')
        if max_retries is not None:
            if not isinstance(max_retries, int) or max_retries < 0:
                raise ValueError("max_retries must be a non-negative integer")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        node = super()._create(session, **kwargs)
        return node

    def _update(self, session: Session, record_id: str, **kwargs) -> Node:
        """Update node with validation."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        # Validate name if being updated
        if 'name' in kwargs and kwargs['name']:
            kwargs['name'] = validators.validate_name(component=self.model_name, name=kwargs['name'])
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        node = super()._update(session, record_id, **kwargs)
        return node

    def _get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[Node]:
        return self._get_all(
            session,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted,
            workflow_id=workflow_id
        )