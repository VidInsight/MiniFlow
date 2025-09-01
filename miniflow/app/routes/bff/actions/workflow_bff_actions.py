from typing import List, Dict, Any, Optional
from miniflow.database.models import WorkflowStatus
from miniflow.core.exceptions import (
    MiniflowException, ResourceNotFound, ValidationError, 
    DatabaseError, ErrorContext, ErrorSeverity
)


class WorkflowActions:
    """Minimal Workflow operations for BFF layer"""
    
    def __init__(self, orchestrator):
        """
        Initialize Workflow operations
        
        Args:
            orchestrator: WorkflowOrchestrator instance
        """
        self.orchestrator = orchestrator

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking"""
        return ErrorContext(
            operation=operation,
            component="WorkflowActions",
            additional_info=kwargs
        )

    def _convert_status_to_enum(self, status_str: str) -> WorkflowStatus:
        """
        Convert string status to WorkflowStatus enum
        
        Args:
            status_str: Status string (e.g., "DRAFT", "ACTIVE")
            
        Returns:
            WorkflowStatus: Enum value
            
        Raises:
            ValidationError: If status is not supported
        """
        try:
            return WorkflowStatus(status_str.upper())
        except ValueError:
            valid_statuses = [e.value for e in WorkflowStatus]
            context = self._create_error_context("convert_status", status=status_str)
            raise ValidationError(
                f"Invalid status '{status_str}'. Valid options: {valid_statuses}",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )

    async def create_workflow(
        self,
        name: str,
        description: Optional[str] = None,
        priority: Optional[int] = 0
    ) -> Dict[str, Any]:
        """
        Create new workflow
        
        Args:
            name: Workflow name
            description: Workflow description
            priority: Workflow priority (0-100)
            
        Returns:
            Dict: Workflow.to_dict() format
            
        Raises:
            ValidationError: If input validation fails
            DatabaseError: If creation fails
        """
        try:
            # Validate inputs
            if not name or not name.strip():
                context = self._create_error_context("create_workflow", name=name)
                raise ValidationError("Workflow name cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

            if priority is not None and (priority < 0 or priority > 100):
                context = self._create_error_context("create_workflow", priority=priority)
                raise ValidationError("Priority must be between 0 and 100", context=context, severity=ErrorSeverity.MEDIUM)

            # Create workflow via orchestrator
            workflow = self.orchestrator.create_workflow(
                name=name.strip(),
                description=description.strip() if description else None,
                priority=priority or 0
            )
            
            return workflow.to_dict()
            
        except (ValidationError, ResourceNotFound):
            raise
        except Exception as e:
            context = self._create_error_context("create_workflow", name=name)
            raise DatabaseError(
                f"Failed to create workflow '{name}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def get_workflow_record(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get single workflow by ID
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Dict: Workflow.to_dict() format
            
        Raises:
            ResourceNotFound: If workflow not found
            DatabaseError: If query fails
        """
        try:
            workflow = self.orchestrator.get_workflow_by_id(workflow_id)
            if not workflow:
                context = self._create_error_context("get_workflow_record", workflow_id=workflow_id)
                raise ResourceNotFound(
                    f"Workflow '{workflow_id}' not found",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            return workflow.to_dict()
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_workflow_record", workflow_id=workflow_id)
            raise DatabaseError(
                f"Failed to retrieve workflow '{workflow_id}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def get_workflow_records(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all workflows with optional filtering
        
        Args:
            status: Filter by status (DRAFT, ACTIVE, DEACTIVATED)
            priority: Filter by priority
            
        Returns:
            List[Dict]: List of Workflow.to_dict() format
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            if status or priority:
                # Use filter method
                filter_kwargs = {}
                if status:
                    filter_kwargs['status'] = self._convert_status_to_enum(status)
                if priority is not None:
                    filter_kwargs['priority'] = priority
                    
                workflows = self.orchestrator.filter_workflows(**filter_kwargs)
            else:
                # Get all workflows
                workflows = self.orchestrator.get_all_workflows()
            
            # Convert to dict format
            result = []
            for workflow in workflows:
                result.append(workflow.to_dict())
            
            return result
            
        except (ValidationError, ResourceNotFound):
            raise
        except Exception as e:
            context = self._create_error_context("get_workflow_records", status=status, priority=priority)
            raise DatabaseError(
                f"Failed to retrieve workflows: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        status_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update workflow by ID
        
        Args:
            workflow_id: Workflow ID
            name: New name
            description: New description
            priority: New priority
            status: New status
            status_message: New status message
            
        Returns:
            Dict: Updated Workflow.to_dict() format
            
        Raises:
            ResourceNotFound: If workflow not found
            ValidationError: If input validation fails
            DatabaseError: If update fails
        """
        try:
            # Prepare update data
            update_data = {}
            
            if name is not None:
                if not name.strip():
                    context = self._create_error_context("update_workflow", workflow_id=workflow_id, name=name)
                    raise ValidationError("Workflow name cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)
                update_data['name'] = name.strip()
            
            if description is not None:
                update_data['description'] = description.strip() if description else None
            
            if priority is not None:
                if priority < 0 or priority > 100:
                    context = self._create_error_context("update_workflow", workflow_id=workflow_id, priority=priority)
                    raise ValidationError("Priority must be between 0 and 100", context=context, severity=ErrorSeverity.MEDIUM)
                update_data['priority'] = priority
            
            if status is not None:
                update_data['status'] = self._convert_status_to_enum(status)
            
            if status_message is not None:
                update_data['status_message'] = status_message.strip() if status_message else None
            
            # Update via orchestrator
            workflow = self.orchestrator.update_workflow(workflow_id, **update_data)
            
            return workflow.to_dict()
            
        except (ValidationError, ResourceNotFound):
            raise
        except Exception as e:
            context = self._create_error_context("update_workflow", workflow_id=workflow_id)
            raise DatabaseError(
                f"Failed to update workflow '{workflow_id}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Delete workflow with detailed response
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Dict: WorkflowDeleteResponse schema format
            
        Raises:
            ResourceNotFound: If workflow not found
            DatabaseError: If deletion fails
        """
        try:
            # Get workflow before deletion
            workflow_record = self.orchestrator.get_workflow_by_id(workflow_id)
            if not workflow_record:
                context = self._create_error_context("delete_workflow", workflow_id=workflow_id)
                raise ResourceNotFound(
                    f"Workflow '{workflow_id}' not found",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            # Delete from database
            deleted_success = self.orchestrator.delete_workflow(workflow_id)
            
            # Return enhanced delete response
            return {
                "deleted_record": workflow_record.to_dict(),
                "database_deleted": deleted_success,
                "message": f"Workflow '{workflow_record.name}' deleted successfully",
                "warnings": None
            }
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("delete_workflow", workflow_id=workflow_id)
            raise DatabaseError(
                f"Failed to delete workflow '{workflow_id}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )
