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

    def _create(self, session: Session, **kwargs) -> Node:
        """Create a new node with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate workflow_id
        workflow_id = kwargs['workflow_id']
        kwargs['workflow_id'] = validators._validate_id(workflow_id)
        
        # Validate script_id if provided
        script_id = kwargs['script_id']
        kwargs['script_id'] = validators._validate_id(script_id)
        
        # Validate name
        name = kwargs['name']
        kwargs['name'] = validators._validate_name(name)

        # Validate Script Path
        script_path = kwargs['script_path']
        validators._validate_file_path(script_path)
        
        # Validate input_params if provided (should be dict)
        input_params = kwargs['input_params']
        if input_params is not None:
            if not isinstance(input_params, dict):
                raise ValueError("input_params must be a dictionary")
            # Serialize to JSON for storage
            kwargs['input_params'] = input_params
        
        # Validate output_params if provided (should be dict)
        output_params = kwargs['output_params']
        if output_params is not None:
            if not isinstance(output_params, dict):
                raise ValueError("output_params must be a dictionary")
            # Serialize to JSON for storage
            kwargs['output_params'] = output_params
        
        # Validate meta_data if provided (should be dict)
        meta_data = kwargs.get('meta_data')
        if meta_data is not None:
            if not isinstance(meta_data, dict):
                raise ValueError("meta_data must be a dictionary")
            # Serialize to JSON for storage
            kwargs['meta_data'] = meta_data
        
        # Validate max_retries if provided
        max_retries = kwargs.get('max_retries')
        if max_retries is not None:
            if not isinstance(max_retries, int) or max_retries < 0:
                raise ValueError("max_retries must be a non-negative integer")
        
        # Validate timeout_seconds if provided
        timeout_seconds = kwargs.get('timeout_seconds')
        if timeout_seconds is not None:
            if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
                raise ValueError("timeout_seconds must be a positive integer")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        node = super()._create(session, **kwargs)
        return node

    def _update(self, session: Session, record_id: str, **kwargs) -> Node:
        """Update node with validation."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        # Validate name if being updated
        if 'name' in kwargs and kwargs['name']:
            kwargs['name'] = validators._validate_name(kwargs['name'])
        
        # Validate input_params if being updated
        if 'input_params' in kwargs and kwargs['input_params'] is not None:
            if not isinstance(kwargs['input_params'], dict):
                raise ValueError("input_params must be a dictionary")
        
        # Validate output_params if being updated
        if 'output_params' in kwargs and kwargs['output_params'] is not None:
            if not isinstance(kwargs['output_params'], dict):
                raise ValueError("output_params must be a dictionary")
        
        # Validate meta_data if being updated
        if 'meta_data' in kwargs and kwargs['meta_data'] is not None:
            if not isinstance(kwargs['meta_data'], dict):
                raise ValueError("meta_data must be a dictionary")
        
        # Validate max_retries if being updated
        if 'max_retries' in kwargs:
            if not isinstance(kwargs['max_retries'], int) or kwargs['max_retries'] < 0:
                raise ValueError("max_retries must be a non-negative integer")
        
        # Validate timeout_seconds if being updated
        if 'timeout_seconds' in kwargs:
            if not isinstance(kwargs['timeout_seconds'], int) or kwargs['timeout_seconds'] <= 0:
                raise ValueError("timeout_seconds must be a positive integer")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        node = super()._update(session, record_id, **kwargs)
        return node

    def _get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = None) -> List[Node]:
        """Get all nodes for a workflow."""
        try:
            workflow_id = validators._validate_id(workflow_id)
            
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.asc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_workflow', component=self.model_name, additional_info={'workflow_id': workflow_id, 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH)

    def _count_by_workflow(self, session: Session, workflow_id: str) -> int:
        """Count nodes in a workflow."""
        try:
            workflow_id = validators._validate_id(workflow_id)
            
            count = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(operation='count_by_workflow', component=self.model_name, additional_info={'workflow_id': workflow_id})
            raise DatabaseQueryError(f"Failed to count {self.model_name} by workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH)

    def _get_by_script(self, session: Session, script_id: str, skip: int = 0, limit: int = None) -> List[Node]:
        """Get all nodes using a specific script."""
        try:
            script_id = validators._validate_id(script_id)
            
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.script_id == script_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_script', component=self.model_name, additional_info={'script_id': script_id, 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by script: {str(e)}", context=context, severity=ErrorSeverity.HIGH)

    def _delete_all_by_workflow(self, session: Session, workflow_id: str) -> List[Node]:
        """Delete all nodes in a workflow (soft delete)."""
        try:
            workflow_id = validators._validate_id(workflow_id)
            
            nodes = self._get_by_workflow(session, workflow_id)
            
            deleted = []
            for node in nodes:
                self._delete(session, node.id)
                deleted.append(node)
            
            return deleted
            
        except Exception as e:
            context = ErrorContext(operation='delete_all_by_workflow', component=self.model_name, additional_info={'workflow_id': workflow_id})
            raise DatabaseQueryError(f"Failed to delete {self.model_name} by workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH)

