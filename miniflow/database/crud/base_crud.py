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
            session.flush()

            self.logger.info(f"Successfully created {self.model_name} with ID: {getattr(db_object, 'id', 'N/A')}")
            return db_object

        # Database Error
        except SQLAlchemyError as e:
            context = self._create_error_context("create", data_keys=list(valid_data.keys()), invalid_fields=invalid_fields)
            self.logger.error(f"Database error creating {self.model_name}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.model_name}",context=context,severity=ErrorSeverity.HIGH,source_error=e)

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
            raise DatabaseError( f"Failed to find {self.model_name} by ID", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("find_by_id", record_id=record_id)
            self.logger.error(f"Unexpected error finding {self.model_name} by ID {record_id}: {str(e)}")
            raise DatabaseQueryError( f"Object Retrieval Error (via ID): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

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
            raise DatabaseError(f"Failed to find {self.model_name} by name", context=context, severity=ErrorSeverity.HIGH, source_error=e)

        # CRUD Error
        except Exception as e:
            context = self._create_error_context("find_by_name", record_name=record_name)
            self.logger.error(f"Unexpected error finding {self.model_name} by name {record_name}: {str(e)}")
            raise DatabaseQueryError(f"Object Retrieval Error (via name): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)