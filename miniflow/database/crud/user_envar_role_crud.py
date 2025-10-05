from miniflow.database.models import UserEnvarRole
from miniflow.database.crud.base_junction_crud import BaseJunctionCRUD


class UserEnvarRoleCRUD(BaseJunctionCRUD[UserEnvarRole]):
    """CRUD operations for User-EnvironmentVariable role assignments."""
    
    def __init__(self):
        super().__init__(
            model=UserEnvarRole,
            user_field='user_id',
            resource_field='envar_id'
        )

