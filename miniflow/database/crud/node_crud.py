from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
import os
from pathlib import Path

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity, ErrorContext
from ..models import Node, Workflow, Script, WorkflowStatus
from ..crud.base_crud import BaseCRUD


class NodeCRUD(BaseCRUD[Node]):
    def __init__(self):
        super().__init__(Node)
        self.required_fields = [
            "name", "workflow_id", "timeout_seconds"
            ]
        self.protected_fields = [
            'created_at', 'updated_at', 'id'
        ]

    def _validate_workflow_exists(self, session: Session, workflow_id: str) -> Workflow:
        workflow = session.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            context = ErrorContext(operation="validate_workflow_for_node", additional_info={"workflow_id": workflow_id})
            raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.HIGH)
        return workflow

    def _validate_script_exists(self, session: Session, script_id: str) -> Script:
        script = session.query(Script).filter(Script.id == script_id).first()
        if not script:
            context = ErrorContext(operation="validate_script_for_node", additional_info={"script_id": script_id})
            raise ValidationError(f"Script '{script_id}' not found", context=context, severity=ErrorSeverity.HIGH)
        
        self._validate_script_file_exists(script)

    def _validate_script_file_exists(self, script: Script) -> None:
        if not script.file_path:
            context = ErrorContext(operation="validate_script_file", additional_info={"script_id": script.id, "script_name": script.name})
            raise ValidationError(f"Script '{script.name}' has no file path configured", context=context, severity=ErrorSeverity.HIGH)
        
        script_path = Path(script.file_path)
        
        if not script_path.exists():
            context = ErrorContext(operation="validate_script_file", additional_info={"script_id": script.id, "script_name": script.name, "file_path": script.file_path})
            raise ValidationError(f"Script file not found: {script.file_path}", context=context, severity=ErrorSeverity.HIGH)
        
        if not script_path.is_file():
            context = ErrorContext(operation="validate_script_file", additional_info={"script_id": script.id, "script_name": script.name, "file_path": script.file_path})
            raise ValidationError(f"Script path is not a file: {script.file_path}", context=context, severity=ErrorSeverity.HIGH)
        
        if not os.access(script_path, os.R_OK):
            context = ErrorContext(operation="validate_script_file", additional_info={"script_id": script.id, "script_name": script.name, "file_path": script.file_path})
            raise ValidationError(f"Script file is not readable: {script.file_path}", context=context, severity=ErrorSeverity.HIGH)
        
        self.logger.debug(f"Script file validation passed: {script.file_path}")

    def _validate_name(self, session: Session, name: str, workflow_id: str, exclude_id: Optional[str] = None) -> str:
        if not name or not name.strip():
            context = ErrorContext(operation="validate_name", additional_info={"field": "name"})
            raise ValidationError("Node name cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        name = name.strip()

        if len(name) < 2:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name})
            raise ValidationError(f"Node name too short: {len(name)} chars (min 2)", context=context, severity=ErrorSeverity.MEDIUM)

        if len(name) > 100:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name})
            raise ValidationError(f"Node name too long: {len(name)} chars (max 100)", context=context, severity=ErrorSeverity.MEDIUM)
        
        existing = session.query(Node).filter(and_(Node.name == name, Node.workflow_id == workflow_id)).first()
        
        if existing and existing.id != exclude_id:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name, "workflow_id": workflow_id, "existing_id": existing.id})
            raise ValidationError(f"Node name '{name}' already exists in workflow", context=context, severity=ErrorSeverity.HIGH)
        
        return name

    def _validate_max_retries(self, max_retries: int) -> int:
        if max_retries < 0:
            context = ErrorContext(operation="validate_max_retries", additional_info={"field": "max_retries", "value": max_retries})
            raise ValidationError(f"Max retries cannot be negative: {max_retries}", context=context, severity=ErrorSeverity.MEDIUM)
        
        if max_retries > 5:
            context = ErrorContext(operation="validate_max_retries", additional_info={"field": "max_retries", "value": max_retries})
            raise ValidationError(f"Max retries too high: {max_retries} (max 10)", context=context, severity=ErrorSeverity.MEDIUM)
        
        return max_retries

    def _validate_timeout_seconds(self, timeout_seconds: int) -> int:
        if timeout_seconds < 1:
            context = ErrorContext(operation="validate_timeout", additional_info={"field": "timeout_seconds", "value": timeout_seconds})
            raise ValidationError(f"Timeout must be at least 1 second: {timeout_seconds}", context=context, severity=ErrorSeverity.MEDIUM)
        
        if timeout_seconds > 3600:  # 1 hour
            context = ErrorContext(operation="validate_timeout", additional_info={"field": "timeout_seconds", "value": timeout_seconds})
            raise ValidationError(f"Timeout too high: {timeout_seconds} seconds (max 3600)", context=context, severity=ErrorSeverity.MEDIUM)
        
        return timeout_seconds

    def _validate_json_fields(self, field_name: str, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        
        if not isinstance(value, dict):
            context = ErrorContext(operation="validate_json_field", additional_info={"field": field_name, "value_type": str(type(value))})
            raise ValidationError(f"{field_name} must be a dictionary, got {type(value)}", context=context, severity=ErrorSeverity.MEDIUM)
        
        return value

    def _validate_deletion_safety(self, session: Session, node_id: str) -> None:
        node = self._get_by_id(session, node_id)
        if not node:
            context = ErrorContext(operation="validate_deletion", additional_info={"node_id": node_id})
            raise ValidationError(f"Node '{node_id}' not found", context=context, severity=ErrorSeverity.HIGH)
        
        workflow = session.query(Workflow).filter(Workflow.id == node.workflow_id).first()
        if workflow and workflow.status == WorkflowStatus.ACTIVE:
            self.logger.warning(f"Deactivating workflow {workflow.id} before deleting node {node_id}")
            workflow.status = WorkflowStatus.DEACTIVATED
            workflow.status_message = "Workflow automatically deactivated due to node deletion"
            session.flush()  
            self.logger.info(f"Workflow {workflow.id} automatically deactivated due to node deletion")

    def _create(self, session: Session, **kwargs) -> Node:
        try:
            self.logger.debug(f"Creating node with data: {kwargs}")
            
            self._validate_required_fields(self.required_fields, kwargs)
            
            workflow_id = kwargs.get("workflow_id")
            name = kwargs.get("name")
            script_id = kwargs.get("script_id")
            
            # VALIDATION - Workflow exists
            self._validate_workflow_exists(session, workflow_id)
            
            # VALIDATION - Script exists and file exists (if provided)
            self._validate_script_exists(session, script_id)
            
            # VALIDATION - Name
            kwargs["name"] = self._validate_name(session, name, workflow_id)
            
            # VALIDATION - Max retries
            if "max_retries" in kwargs:
                kwargs["max_retries"] = self._validate_max_retries(kwargs["max_retries"])
            
            # VALIDATION - Timeout seconds
            if "timeout_seconds" in kwargs:
                kwargs["timeout_seconds"] = self._validate_timeout_seconds(kwargs["timeout_seconds"])
            
            # Validate JSON fields
            if "input_params" in kwargs:
                kwargs["input_params"] = self._validate_json_fields("input_params", kwargs["input_params"])
            
            if "output_params" in kwargs:
                kwargs["output_params"] = self._validate_json_fields("output_params", kwargs["output_params"])
            
            if "meta_data" in kwargs:
                kwargs["meta_data"] = self._validate_json_fields("meta_data", kwargs["meta_data"])
            
            valid_fields, invalid_fields = self._validate_request_data(kwargs)
            node = super()._create(session, **valid_fields)
            self.logger.info(f"Successfully created node: {node.name} ({node.id})")
            return node
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="create", additional_info={"node_data": kwargs})
            self.logger.error(f"Failed to create node: {str(e)}")
            raise ValidationError(f"Failed to create node: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _update(self, session: Session, record_id: str, **kwargs) -> Node:
        try:
            self.logger.debug(f"Updating node {record_id} with data: {kwargs}")
            
            existing_node = self._get_by_id(session, record_id)
            if not existing_node:
                context = ErrorContext(operation="update", additional_info={"node_id": record_id})
                raise ValidationError(f"Node '{record_id}' not found", context=context, severity=ErrorSeverity.HIGH)
            
            # Validate workflow exists (if being updated)
            if "workflow_id" in kwargs:
                self._validate_workflow_exists(session, kwargs["workflow_id"])
            
            # Validate script exists and file exists (if being updated)
            if "script_id" in kwargs and kwargs["script_id"]:
                script = self._validate_script_exists(session, kwargs["script_id"])
                self._validate_script_file_exists(script)
            
            # Validate and normalize name (if being updated)
            if "name" in kwargs:
                workflow_id = kwargs.get("workflow_id", existing_node.workflow_id)
                kwargs["name"] = self._validate_name(session, kwargs["name"], workflow_id, exclude_id=record_id)
            
            # Validate numeric fields
            if "max_retries" in kwargs:
                kwargs["max_retries"] = self._validate_max_retries(kwargs["max_retries"])
            
            if "timeout_seconds" in kwargs:
                kwargs["timeout_seconds"] = self._validate_timeout_seconds(kwargs["timeout_seconds"])
            
            # Validate JSON fields
            if "input_params" in kwargs:
                kwargs["input_params"] = self._validate_json_fields("input_params", kwargs["input_params"])
            
            if "output_params" in kwargs:
                kwargs["output_params"] = self._validate_json_fields("output_params", kwargs["output_params"])
            
            if "meta_data" in kwargs:
                kwargs["meta_data"] = self._validate_json_fields("meta_data", kwargs["meta_data"])
            
            valid_fields, invalid_fields = self._validate_request_data(kwargs)
            protected_fields = self._validate_protected_fields(self.protected_fields, valid_fields)
            
            node = super()._update(session, record_id, **protected_fields)
            self.logger.info(f"Successfully updated node: {node.name} ({node.id})")
            return node
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="update", additional_info={"node_id": record_id, "update_data": kwargs})
            self.logger.error(f"Failed to update node {record_id}: {str(e)}")
            raise ValidationError(f"Failed to update node: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _delete(self, session: Session, record_id: str) -> bool:
        try:
            self.logger.debug(f"Attempting to delete node: {record_id}")
            
            self._validate_deletion_safety(session, record_id)
            result = super()._delete(session, record_id)
            self.logger.info(f"Successfully deleted node: {record_id}")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="delete", additional_info={"node_id": record_id})
            self.logger.error(f"Failed to delete node {record_id}: {str(e)}")
            raise ValidationError(f"Failed to delete node: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _get_workflow_nodes(self, session: Session, workflow_id: str) -> List[Node]:
        try:
            nodes = session.query(Node).filter(Node.workflow_id == workflow_id).all()
            self.logger.debug(f"Found {len(nodes)} nodes in workflow {workflow_id}")
            return nodes
        except Exception as e:
            context = ErrorContext(operation="get_workflow_nodes", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to get nodes for workflow {workflow_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get nodes for workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _get_nodes_by_script(self, session: Session, script_id: str) -> List[Node]:
        try:
            nodes = session.query(Node).filter(Node.script_id == script_id).all()
            self.logger.debug(f"Found {len(nodes)} nodes using script {script_id}")
            return nodes
        except Exception as e:
            context = ErrorContext(operation="get_nodes_by_script", additional_info={"script_id": script_id})
            self.logger.error(f"Failed to get nodes for script {script_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get nodes for script: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e