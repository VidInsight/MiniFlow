from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import DeclarativeMeta, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import (
    InvalidInput,
    ValidationError,
    DatabaseError,
    DatabaseQueryError,
    ErrorContext,
    ErrorSeverity
)


ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseCRUD(Generic[ModelType]):
    """
    A generic base class for CRUD operations for all entities.
    Provides type-safe CRUD operations with increased performance.

    Note: This class works with the DatabaseEngine's session context management framework.
    Session rollbacks are handled at the engine level.
    """

    def __init__(self, model: type[ModelType]):
        """Initialize BaseCRUD with the specific model type for type-safe operations."""
        self.model = model
        self.model_name = model.__name__
        self.logger = get_logger("database_orchestration")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    def create(self, session: Session, **model_data) -> ModelType:
        """Create new database record with automatic field validation."""
        if not model_data:
            context = self._create_error_context("DB query: create", data_keys=[])
            raise ValidationError(f"No data provided for {self.model_name} creation", context=context, severity=ErrorSeverity.HIGH)

        # Filter out invalid fields that don't exist in the model
        valid_data = {}
        invalid_fields = []
        for field, value in model_data.items():
            if hasattr(self.model, field):
                valid_data[field] = value
            else:
                invalid_fields.append(field)
                self.logger.warning(f"Ignoring invalid field '{field}' for {self.model_name}")

        # Create Action
        try:
            self.logger.debug(f"Creating {self.model_name} with data: {list(valid_data.keys())}")
            db_object = self.model(**valid_data)
            session.add(db_object)
            # Flush to get the ID immediately (engine will handle final commit)
            session.flush()
            self.logger.info(f"Successfully created {self.model_name} with ID: {getattr(db_object, 'id', 'N/A')}")
            return db_object

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("create", data_keys=list(valid_data.keys()), invalid_fields=invalid_fields)
            self.logger.error(f"Database error creating {self.model_name}: {str(e)}")
            raise DatabaseQueryError(f"Failed to create {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("create", data_keys=list(valid_data.keys()), invalid_fields=invalid_fields)
            self.logger.error(f"Unexpected error creating {self.model_name}: {str(e)}")
            raise DatabaseQueryError(f"Object Creation Error: {self.model_name}", context=context, severity=ErrorSeverity.CRITICAL, source_error=e)

    def find_by_id(self, session: Session, record_id: Union[str, int]) -> Optional[ModelType]:
        """Find single record by primary key ID."""
        if record_id is None:
            context = self._create_error_context("find_by_id", record_id=record_id)
            raise ValidationError("Record ID cannot be None", context=context, severity=ErrorSeverity.MEDIUM)

        # Find Action
        try:
            self.logger.debug(f"Finding {self.model_name} by ID: {record_id}")

            result = session.get(self.model, record_id)
            if result:
                self.logger.debug(f"Found {self.model_name} with ID: {record_id}")
                return result
            else:
                self.logger.debug(f"No {self.model_name} found with ID: {record_id}")
                return None

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("find_by_id", record_id=record_id)
            self.logger.error(f"Database error finding {self.model_name} by ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to find {self.model_name} by ID", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("find_by_id", record_id=record_id)
            self.logger.error(f"Unexpected error finding {self.model_name} by ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Object Retrieval Error (via ID): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def find_by_name(self, session: Session, record_name: str) -> Optional[ModelType]:
        """Find single record by name field (if model has name attribute)."""
        if not record_name or not record_name.strip():
            context = self._create_error_context("find_by_name", record_name=record_name)
            raise ValidationError("Record name cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        if not hasattr(self.model, 'name'):
            context = self._create_error_context("find_by_name", record_name=record_name)
            raise ValidationError(f"{self.model_name} does not have a 'name' field", context=context, severity=ErrorSeverity.MEDIUM)

        # Find Action
        try:
            self.logger.debug(f"Finding {self.model_name} by name: {record_name}")
            stmt = select(self.model).where(self.model.name == record_name)
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                self.logger.debug(f"Found {self.model_name} with name: {record_name}")
                return result
            else:
                self.logger.debug(f"No {self.model_name} found with name: {record_name}")
                return None

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("find_by_name", record_name=record_name)
            self.logger.error(f"Database error finding {self.model_name} by name {record_name}: {str(e)}")
            raise DatabaseQueryError(f"Failed to find {self.model_name} by name", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("find_by_name", record_name=record_name)
            self.logger.error(f"Unexpected error finding {self.model_name} by name {record_name}: {str(e)}")
            raise DatabaseQueryError(f"Object Retrieval Error (via name): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def update(self, session: Session, record_id: Union[str, int], **model_data) -> ModelType:
        """Update existing record with automatic timestamp and field validation."""
        if not model_data:
            context = self._create_error_context("update", record_id=record_id, data_keys=[])
            raise ValidationError(f"No data provided for {self.model_name} update", context=context, severity=ErrorSeverity.MEDIUM)

        db_object = self.find_by_id(session, record_id)
        if db_object is None:
            context = self._create_error_context("update", record_id=record_id, data_keys=list(model_data.keys()))
            raise DatabaseQueryError(f"Object Update Error: No such {self.model_name} record with ID {record_id}", context=context, severity=ErrorSeverity.HIGH)

        # Add timestamp if model supports it
        if hasattr(db_object, 'updated_at'):
            model_data['updated_at'] = datetime.now(timezone.utc)

        updated_fields = []
        invalid_fields = []

        try:
            self.logger.debug(f"Updating {self.model_name} ID {record_id} with data: {list(model_data.keys())}")
            for field, value in model_data.items():
                if hasattr(db_object, field):
                    setattr(db_object, field, value)
                    updated_fields.append(field)
                else:
                    invalid_fields.append(field)
                    self.logger.warning(f"Ignoring invalid field '{field}' for {self.model_name} update")
            # No manual flush needed - engine will handle auto-flush before commit
            self.logger.info(f"Successfully updated {self.model_name} ID {record_id}, fields: {updated_fields}")
            return db_object

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("update", record_id=record_id, updated_fields=updated_fields, invalid_fields=invalid_fields)
            self.logger.error(f"Database error updating {self.model_name} ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to update {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("update", record_id=record_id, updated_fields=updated_fields, invalid_fields=invalid_fields)
            self.logger.error(f"Unexpected error updating {self.model_name} ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Object Update Error: {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def delete(self, session: Session, record_id: Union[str, int]) -> ModelType:
        """Delete record by ID and return the deleted object."""
        db_object = self.find_by_id(session, record_id)
        if db_object is None:
            context = self._create_error_context("delete", record_id=record_id)
            raise DatabaseQueryError(f"Object Deletion Error: No such {self.model_name} record with ID {record_id}", context=context, severity=ErrorSeverity.HIGH)

        try:
            self.logger.debug(f"Deleting {self.model_name} ID {record_id}")
            session.delete(db_object)
            # No manual flush needed - engine will handle auto-flush before commit
            self.logger.info(f"Successfully deleted {self.model_name} ID {record_id}")
            return db_object

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("delete", record_id=record_id)
            self.logger.error(f"Database error deleting {self.model_name} ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to delete {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("delete", record_id=record_id)
            self.logger.error(f"Unexpected error deleting {self.model_name} ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Object Deletion Error: {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def exists(self, session: Session, record_id: Union[str, int]) -> bool:
        """Check if record exists by ID."""
        if record_id is None:
            context = self._create_error_context("exists", record_id=record_id)
            raise ValidationError("Record ID cannot be None",context=context,severity=ErrorSeverity.MEDIUM)

        stmt = select(func.count(self.model.id)).where(self.model.id == record_id)

        try:
            self.logger.debug(f"Checking if {self.model_name} exists with ID: {record_id}")
            result = session.execute(stmt).scalar_one() > 0
            self.logger.debug(f"{self.model_name} ID {record_id} exists: {result}")
            return result

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("exists", record_id=record_id)
            self.logger.error(f"Database error checking {self.model_name} existence ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to check {self.model_name} existence",context=context,severity=ErrorSeverity.HIGH,source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("exists", record_id=record_id)
            self.logger.error(f"Unexpected error checking {self.model_name} existence ID {record_id}: {str(e)}")
            raise DatabaseQueryError(f"Object Exists Error: {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def count(self, session: Session) -> int:
        """Count total number of records in the table."""
        stmt = select(func.count(self.model.id))

        try:
            self.logger.debug(f"Counting {self.model_name} records")
            result = session.execute(stmt).scalar_one()
            self.logger.debug(f"Total {self.model_name} count: {result}")
            return result

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("count")
            self.logger.error(f"Database error counting {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Failed to count {self.model_name} records", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("count")
            self.logger.error(f"Unexpected error counting {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Object Count Error: {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def get_all(self, session: Session, skip: int = 0, limit: int = 100, order_by: str = None) -> List[ModelType]:
        """Get all records with pagination and optional ordering."""
        if skip < 0:
            context = self._create_error_context("get_all", skip=skip, limit=limit, order_by=order_by)
            raise ValidationError("Skip value cannot be negative", context=context, severity=ErrorSeverity.MEDIUM)

        if limit <= 0:
            context = self._create_error_context("get_all", skip=skip, limit=limit, order_by=order_by)
            raise ValidationError("Limit value must be positive", context=context, severity=ErrorSeverity.MEDIUM)

        limit = min(limit, 1000)  # Memory protection
        stmt = select(self.model)

        if order_by:
            if hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                stmt = stmt.order_by(order_column)
            else:
                self.logger.warning(f"Invalid order_by field '{order_by}' for {self.model_name}, using default ID ordering")
                stmt = stmt.order_by(self.model.id)
        else:
            stmt = stmt.order_by(self.model.id)  # Default ID ordering

        stmt = stmt.offset(skip).limit(limit)

        try:
            self.logger.debug(f"Getting all {self.model_name} records: skip={skip}, limit={limit}, order_by={order_by}")
            results = list(session.execute(stmt).scalars().all())
            self.logger.debug(f"Retrieved {len(results)} {self.model_name} records")
            return results

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("get_all", skip=skip, limit=limit, order_by=order_by)
            self.logger.error(f"Database error getting all {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Failed to retrieve {self.model_name} records", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("get_all", skip=skip, limit=limit, order_by=order_by)
            self.logger.error(f"Unexpected error getting all {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Object Retrieval Error (via Get All): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def filter(self, session: Session, filters: Dict[str, Any], skip: int = 0, limit: int = 100, order_by_field: str = None) -> List[ModelType]:
        """Filter records by field values with pagination and ordering - Optimized version."""
        if not filters:
            context = self._create_error_context("filter", filters=filters, skip=skip, limit=limit,order_by_field=order_by_field)
            raise ValidationError("Filter criteria cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        if skip < 0:
            context = self._create_error_context("filter", filters=filters, skip=skip, limit=limit, order_by_field=order_by_field)
            raise ValidationError("Skip value cannot be negative", context=context, severity=ErrorSeverity.MEDIUM)

        if limit <= 0:
            context = self._create_error_context("filter", filters=filters, skip=skip, limit=limit,order_by_field=order_by_field)
            raise ValidationError("Limit value must be positive", context=context, severity=ErrorSeverity.MEDIUM)

        limit = min(limit, 1000)
        valid_filters = []
        invalid_fields = []

        stmt = select(self.model)

        # Loop for validation and query building
        for field_name, field_value in filters.items():
            if hasattr(self.model, field_name):
                field_attr = getattr(self.model, field_name)
                stmt = stmt.where(field_attr == field_value)
                valid_filters.append(f"{field_name}={field_value}")
            else:
                invalid_fields.append(field_name)
                raise ValidationError(f"Field '{field_name}' does not exist in {self.model_name}", context=self._create_error_context("filter", field_name=field_name), severity=ErrorSeverity.MEDIUM)

        # Ordering logic
        if order_by_field and hasattr(self.model, order_by_field):
            stmt = stmt.order_by(getattr(self.model, order_by_field))
        else:
            # Default ordering only if no valid order_by_field
            if not order_by_field or not hasattr(self.model, order_by_field):
                if order_by_field:
                    self.logger.warning(
                        f"Invalid order_by_field '{order_by_field}' for {self.model_name}, using default ID ordering")
                stmt = stmt.order_by(self.model.id)

        # Apply pagination
        if skip > 0 or limit < 1000:
            stmt = stmt.offset(skip).limit(limit)

        try:
            self.logger.debug(f"Filtering {self.model_name} records: {valid_filters}, skip={skip}, limit={limit}")
            results = session.execute(stmt).scalars().all()
            self.logger.debug(f"Filter returned {len(results)} {self.model_name} records")
            return results

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("filter", valid_filters=valid_filters, invalid_fields=invalid_fields,skip=skip, limit=limit)
            self.logger.error(f"Database error filtering {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Failed to filter {self.model_name} records", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("filter", valid_filters=valid_filters, invalid_fields=invalid_fields,skip=skip, limit=limit)
            self.logger.error(f"Unexpected error filtering {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Object Retrieval Error (via Filter): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def count_filtered(self, session: Session, filters: Dict[str, Any]) -> int:
        """Count records matching the specified filter criteria - Optimized version."""
        if not filters:
            context = self._create_error_context("count_filtered", filters=filters)
            raise ValidationError("Filter criteria cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        valid_filters = []
        invalid_fields = []

        stmt = select(func.count(self.model.id))

        # Loop for validation and query building
        for field_name, field_value in filters.items():
            if hasattr(self.model, field_name):
                field_attr = getattr(self.model, field_name)
                stmt = stmt.where(field_attr == field_value)
                valid_filters.append(f"{field_name}={field_value}")
            else:
                invalid_fields.append(field_name)
                raise ValidationError(f"Field '{field_name}' does not exist in {self.model_name}", context=self._create_error_context("count_filtered", field_name=field_name), severity=ErrorSeverity.MEDIUM)

        try:
            self.logger.debug(f"Counting filtered {self.model_name} records: {valid_filters}")
            result = session.execute(stmt).scalar_one()
            self.logger.debug(f"Filtered {self.model_name} count: {result}")
            return result

        except SQLAlchemyError as e:
            context = self._create_error_context("count_filtered", valid_filters=valid_filters, invalid_fields=invalid_fields)
            self.logger.error(f"Database error counting filtered {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Failed to count filtered {self.model_name} records", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        except Exception as e:
            context = self._create_error_context("count_filtered", valid_filters=valid_filters, invalid_fields=invalid_fields)
            self.logger.error(f"Unexpected error counting filtered {self.model_name} records: {str(e)}")
            raise DatabaseQueryError(f"Object Count Error (via Count Filtered): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)