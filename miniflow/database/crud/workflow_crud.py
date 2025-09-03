from miniflow.database.models import Workflow, WorkflowStatus
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class WorkflowCRUD(BaseCRUD[Workflow]):
    def __init__(self):
        super().__init__(Workflow)

    def _create_with_validation(self, session, name: str, **kwargs):
        if not name or not name.strip():
            raise ValidationError("Workflow name cannot be empty", severity=ErrorSeverity.HIGH)

        name = name.strip()
        existing_record = self._filter(session, filters={"name": name})
        if existing_record:
            raise ValidationError(f"Workflow with name '{name}' already exists", severity=ErrorSeverity.HIGH)

        if "status" not in kwargs:
            kwargs["status"] = WorkflowStatus.DRAFT

        return self._create(session, name=name, **kwargs)

    def _update_with_validation(self, session, record_id: str, **kwargs):
        if "name" in kwargs and kwargs["name"]:
            new_name = kwargs["name"].strip()
            if not new_name:
                raise ValidationError("Workflow name cannot be empty", severity=ErrorSeverity.HIGH)

            existing_record = self._filter(session, filters={"name": new_name})
            if existing_record and existing_record[0].id != record_id:
                raise ValidationError(f"Workflow with name '{new_name}' already exists", severity=ErrorSeverity.HIGH)

            kwargs["name"] = new_name

        return self._update(session, record_id, **kwargs)