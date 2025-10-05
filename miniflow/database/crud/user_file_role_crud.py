from miniflow.database.models import UserFileRole
from miniflow.database.crud.base_junction_crud import BaseJunctionCRUD


class UserFileRoleCRUD(BaseJunctionCRUD[UserFileRole]):
    """CRUD operations for User-FileUpload role assignments."""
    
    def __init__(self):
        super().__init__(
            model=UserFileRole,
            user_field='user_id',
            resource_field='file_id'
        )

