from miniflow.database.models import UserWorkflowRole
from miniflow.database.crud.base_junction_crud import BaseJunctionCRUD


class UserWorkflowRoleCRUD(BaseJunctionCRUD[UserWorkflowRole]):
    """CRUD operations for User-Workflow role assignments."""
    
    def __init__(self):
        super().__init__(
            model=UserWorkflowRole,
            user_field='user_id',
            resource_field='workflow_id'
        )

