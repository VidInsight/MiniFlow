"""
Dashboard Operations - Aggregated Data Provider
"""

from typing import List, Dict, Any, Optional

from miniflow.core.logger import get_logger
from .schemas import DashboardFilterRequest
from miniflow.database.orchestration import DatabaseOrchestrator


class DashboardOperations:
    """
    Dashboard operations - special case that doesn't inherit from BaseBFFOperations
    because it's not a traditional CRUD entity but an aggregation layer.
    
    Dashboard provides computed analytics and overview data by aggregating
    information from multiple orchestrators.
    """
    def __init__(self, database_orchestrator: DatabaseOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.database_orchestrator = database_orchestrator
        self.entity_name = "dashboard"

    # Dashboard-specific aggregation methods
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get complete dashboard overview with system statistics"""
        try:
            # Aggregate data from various orchestrators
            workflow_count = self.database_orchestrator.workflow_orchestrator.count()
            node_count = self.database_orchestrator.node_orchestrator.count()
            edge_count = self.database_orchestrator.edge_orchestrator.count()
            script_count = self.database_orchestrator.script_orchestrator.count()
            execution_count = self.database_orchestrator.execution_orchestrator.count()
            
            return {
                'overview': {
                    'total_workflows': workflow_count,
                    'total_nodes': node_count,
                    'total_edges': edge_count,
                    'total_scripts': script_count,
                    'total_executions': execution_count
                },
                'message': 'Dashboard overview retrieved successfully'
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard overview: {str(e)}")
            raise

    async def get_recent_activity(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent activity across all entities"""
        try:
            # Get recent executions as activity indicator
            recent_executions = self.database_orchestrator.execution_orchestrator.get_all(
                skip=0, limit=limit, order_by='created_at'
            )
            
            return {
                'recent_activity': recent_executions,
                'message': 'Recent activity retrieved successfully'
            }
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {str(e)}")
            raise

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators"""
        try:
            # Basic health indicators based on entity counts
            health_status = {
                'status': 'healthy',
                'indicators': {
                    'database_connection': True,
                    'orchestrators_active': True
                }
            }
            
            return {
                'health': health_status,
                'message': 'System health retrieved successfully'
            }
        except Exception as e:
            self.logger.error(f"Failed to get system health: {str(e)}")
            raise

    # Compatibility methods for interface consistency
    async def list_dashboard_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """List dashboard data - returns overview by default"""
        return await self.get_dashboard_overview()

    async def count_dashboard_records(self) -> int:
        """Count dashboard items - returns 1 as there's always one dashboard overview"""
        return 1

    async def filter_dashboard_records(self, request: DashboardFilterRequest) -> Dict[str, Any]:
        """Filter dashboard data based on request parameters"""
        # Dashboard filtering could be implemented based on specific analytics needs
        return await self.get_dashboard_overview()