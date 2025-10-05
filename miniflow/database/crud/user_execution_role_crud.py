from miniflow.database.models import UserExecutionRole
from miniflow.database.crud.base_junction_crud import BaseJunctionCRUD


class UserExecutionRoleCRUD(BaseJunctionCRUD[UserExecutionRole]):
    """CRUD operations for User-Execution role assignments."""
    
    def __init__(self):
        super().__init__(
            model=UserExecutionRole,
            user_field='user_id',
            resource_field='execution_id'
        )

