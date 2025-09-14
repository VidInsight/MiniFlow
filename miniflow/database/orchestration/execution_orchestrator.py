from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from miniflow.database.models import Execution
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class ExecutionOrchestrator(BaseOrchestrator):
    """Execution orchestrator for full CRUD operations and execution monitoring."""

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        return self.execution_crud

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get executions for a specific workflow."""
        if not workflow_id:
            return []
        try:
            results = self.execution_crud._filter(session, filters={"workflow_id": workflow_id}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_executions_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_status(self, session: Session, status: str, skip: int = 0, limit: int = 100, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get executions by status."""
        if not status:
            return []
        try:
            results = self.execution_crud._filter(session, filters={"status": status}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_executions_by_status", status=status)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_daily_stats(self, session: Session, target_date: Optional[datetime] = None) -> Dict[str, Any]:
        try:
            stats = self.execution_crud.get_daily_execution_stats(session, target_date)
            # Ensure we return a dict even if stats is None
            return stats if stats is not None else {}
        except Exception as e:
            context = self._create_error_context("get_daily_execution_stats", target_date=str(target_date) if target_date else "today")
            raise OrchestrationError(f"Failed to get daily execution statistics: {str(e)}", context=context) from e

    @with_session
    def get_recent_by_workflow(self, session: Session, workflow_id: str, limit: int = 10, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get N most recent executions for a specific workflow using standard serialization."""
        if not workflow_id:
            return []
        try:
            # Use standard CRUD + serialization approach for consistency
            executions = self.execution_crud._get_recent_by_workflow(session, workflow_id, limit)
            return self._serialize_multiple_results(executions, include_relationships, exclude_fields)
            
        except Exception as e:
            context = self._create_error_context("get_recent_by_workflow", workflow_id=workflow_id, limit=limit)
            raise OrchestrationError(f"Failed to get recent executions for workflow: {str(e)}", context=context) from e

    @with_session
    def get_recent_by_workflow_summary(self, session: Session, workflow_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get N most recent executions with custom summary fields (id, workflow_name, status, pending_nodes, executed_nodes)."""
        if not workflow_id:
            return []
        try:
            executions = self.execution_crud._get_recent_by_workflow(session, workflow_id, limit)
            
            # Get workflow name once
            workflow = self.workflow_crud._get_by_id(session, workflow_id)
            workflow_name = workflow.name if workflow else f"Workflow-{workflow_id}"
            
            # Build custom summary response
            result = []
            for execution in executions:
                result.append({
                    'id': execution.id,
                    'workflow_name': workflow_name,
                    'status': execution.status.value,
                    'pending_nodes': execution.pending_nodes,
                    'executed_nodes': execution.executed_nodes
                })
            
            return result
            
        except Exception as e:
            context = self._create_error_context("get_recent_by_workflow_summary", workflow_id=workflow_id, limit=limit)
            raise OrchestrationError(f"Failed to get recent executions summary for workflow: {str(e)}", context=context) from e
    @with_session
    def get_yesterday_stats(self, session: Session) -> Dict[str, Any]:
        """Get yesterday's execution statistics."""
        try:
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            stats = self.execution_crud._get_daily_stats(session, yesterday)
            return stats if stats is not None else {}
        except Exception as e:
            context = self._create_error_context("get_yesterday_stats")
            raise OrchestrationError(f"Failed to get yesterday's execution stats: {str(e)}", context=context) from e

    @with_session
    def get_recently_executed_workflows_with_executions(self, session: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently executed workflows with their last executions."""
        try:
            # Get recently executed workflows
            recent_workflows = self.execution_crud._get_recently_executed_workflows(session, limit)
            
            result = []
            for workflow_data in recent_workflows:
                workflow_id = workflow_data.get('workflow_id')
                if not workflow_id:
                    continue
                
                # Get last 5 executions for this workflow
                recent_executions = self.execution_crud._get_recent_executions_by_workflow(session, workflow_id, 5)
                
                # Get today's execution count for this workflow
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                today_count = self.execution_crud._count_executions_by_workflow_and_date(session, workflow_id, today)
                
                workflow_summary = {
                    'workflow_id': workflow_id,
                    'workflow_name': workflow_data.get('workflow_name', 'Unknown'),
                    'workflow_status': workflow_data.get('workflow_status', 'UNKNOWN'),
                    'last_execution_time': workflow_data.get('last_execution_time'),
                    'total_executions_today': today_count or 0,
                    'recent_executions': self._serialize_multiple_results(recent_executions)
                }
                result.append(workflow_summary)
            
            return result
            
        except Exception as e:
            context = self._create_error_context("get_recently_executed_workflows_with_executions", limit=limit)
            raise OrchestrationError(f"Failed to get recently executed workflows with executions: {str(e)}", context=context) from e
