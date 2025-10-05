from typing import Any, Dict, Generic, List, Optional, TypeVar, cast, Callable
from sqlalchemy.orm import DeclarativeMeta, Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from sqlalchemy import select, func, exists
from functools import wraps

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorContext, ErrorSeverity
from miniflow.database import validators

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
T = TypeVar('T')

# Maximum allowed limit for pagination
MAX_QUERY_LIMIT = 1000

def handle_crud_errors(operation_name: str = None):
    """Decorator for CRUD operation error management"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self, session: Session, *args, **kwargs) -> T:
            op_name = operation_name or func.__name__
            data = kwargs.copy()
            data.pop('session', None)
            try:
                result = func(self, session, *args, **kwargs)
                return result
            except (ValidationError, DatabaseQueryError):
                raise
            except SQLAlchemyError as e:
                context = ErrorContext(operation=op_name, component=self.model_name, additional_info={"data": data})
                raise DatabaseQueryError(f"Database Error (via BaseCRUD {op_name}): {self.model_name}", context=context, severity=ErrorSeverity.HIGH, source_error=e)
            except Exception as e:
                context = ErrorContext(operation=op_name, component=self.model_name, additional_info={"data": data})
                raise DatabaseQueryError(f"CRUD Error (via BaseCRUD {op_name}): {self.model_name}",context=context,severity=ErrorSeverity.HIGH,source_error=e)
        return wrapper

    return decorator


class BaseCRUD(Generic[ModelType]):
    """
    A generic base class for CRUD operations for all entities.
    Provides type-safe CRUD operations with increased performance.

    Note: This class works with the DatabaseEngine's session context management framework.
    Session rollbacks are handled at the engine level. Never call session.commit() within
    these methods - use session.flush() to persist changes within the transaction.
    """

    def __init__(self, model: type[ModelType]):
        self.model = model
        self.model_name = model.__name__
        self.logger = get_logger("database_orchestration")

    # ========================================================================================== EXCEPTION HELPERS =====
    def _raise_not_found_error(self, operation: str, record_id: str) -> None:
        """Raise a standardized not found error"""
        context = ErrorContext(operation=operation, component=self.model_name, additional_info={"id": record_id})
        raise DatabaseQueryError(f"{self.model_name} with ID '{record_id}' not found",context=context,severity=ErrorSeverity.MEDIUM)

    # ========================================================================================= VALIDATION HELPERS =====
    def _validate_required_fields_in_kwargs(self, required_fields: List[str], kwargs: Dict[str, Any]) -> None:
        """Validate that all required fields are present in kwargs"""
        missing_fields = [field for field in required_fields if field not in kwargs or kwargs[field] is None]
        if missing_fields:
            context = ErrorContext(operation="validate_required_fields",component=self.model_name,additional_info={"missing_fields": missing_fields})
            raise ValidationError(f"Missing required fields for {self.model_name}: {missing_fields}",context=context,severity=ErrorSeverity.HIGH)

    def _validate_no_extra_fields(self, allowed_fields: List[str], kwargs: Dict[str, Any]) -> None:
        """Validate that no extra fields are present in kwargs"""
        extra_fields = [field for field in kwargs if field not in allowed_fields]
        if extra_fields:
            context = ErrorContext(operation="validate_no_extra_fields",component=self.model_name,additional_info={"extra_fields": extra_fields})
            raise ValidationError(f"Extra fields not allowed for {self.model_name}: {extra_fields}",context=context,severity=ErrorSeverity.MEDIUM)

    def _validate_no_protected_fields(self, protected_fields: List[str], kwargs: Dict[str, Any]) -> None:
        """Validate that no protected fields are being modified in kwargs"""
        protected_attempts = [field for field in kwargs if field in protected_fields]
        if protected_attempts:
            context = ErrorContext(operation="validate_no_protected_fields",component=self.model_name,additional_info={"protected_fields": protected_attempts})
            raise ValidationError(f"Attempted to modify protected fields for {self.model_name}: {protected_attempts}",context=context,severity=ErrorSeverity.HIGH)

    # ============================================================================================ CRUD OPERATIONS =====
    @handle_crud_errors(operation_name="CREATE")
    def _create(self, session: Session, **kwargs) -> ModelType:
        """
        Create new database record.

        Args:
            session: SQLAlchemy session
            **kwargs: Field values for the new record

        Returns:
            Created model instance
        """
        if not kwargs:
            context = ErrorContext(operation="create", component=self.model_name)
            raise ValidationError("No data provided for creation", context=context, severity=ErrorSeverity.HIGH)

        db_object = cast(ModelType, self.model(**kwargs))
        session.add(db_object)
        session.flush()

        return db_object

    @handle_crud_errors(operation_name="GET_BY_ID")
    def _get_by_id(self, session: Session, record_id: str, *, relationships: Optional[List[str]] = None, load_all_relationships: bool = False) -> Optional[ModelType]:
        """
        Get single record by ID.

        Args:
            session: SQLAlchemy session
            record_id: ID of the record to retrieve
            relationships: List of specific relationship names to load
            load_all_relationships: If True, load all relationships (overrides relationships param)

        Returns:
            Model instance or None if not found
        """
        record_id = validators.validate_record_id(record_id, self.model_name)

        if not relationships and not load_all_relationships:
            return session.get(self.model, record_id)

        query = select(self.model).where(self.model.id == record_id)
        rels_to_load = (
            self.model.__mapper__.relationships.keys()
            if load_all_relationships
            else relationships or []
        )

        for rel_name in rels_to_load:
            if rel_name in self.model.__mapper__.relationships.keys():
                query = query.options(selectinload(getattr(self.model, rel_name)))
            else:
                self.logger.warning(
                    f"Relationship '{rel_name}' not found in {self.model_name}",
                    extra={"relationship": rel_name, "model": self.model_name}
                )

        return session.execute(query).scalar_one_or_none()

    @handle_crud_errors(operation_name="UPDATE")
    def _update(self, session: Session, record_id: str, **kwargs) -> ModelType:
        """
        Update existing record by ID.

        Args:
            session: SQLAlchemy session
            record_id: ID of the record to update
            **kwargs: Fields to update with their new values

        Returns:
            Updated model instance
        """
        record_id = validators.validate_record_id(record_id, self.model_name)

        if not kwargs:
            context = ErrorContext(operation="update", component=self.model_name, additional_info={"id": record_id})
            raise ValidationError("No data provided for update", context=context, severity=ErrorSeverity.HIGH)

        db_object = self._get_by_id(session, record_id)
        if not db_object:
            self._raise_not_found_error(record_id)

        for key, value in kwargs.items():
            if hasattr(db_object, key):
                setattr(db_object, key, value)
            else:
                self.logger.warning(f"Attempted to update non-existent field '{key}' on {self.model_name}")

        session.add(db_object)
        session.flush()

        return db_object

    @handle_crud_errors(operation_name="DELETE")
    def _delete(self, session: Session, record_id: str) -> None:
        """
        Permanently delete record by ID.

        Args:
            session: SQLAlchemy session
            record_id: ID of the record to delete
        """
        record_id = validators.validate_record_id(record_id, self.model_name)

        db_object = self._get_by_id(session, record_id)
        if not db_object:
            self._raise_not_found_error(record_id)

        session.delete(db_object)
        session.flush()

    @handle_crud_errors(operation_name="SOFT_DELETE")
    def _soft_delete(self, session: Session, record_id: str, user_id: str) -> None:
        """
        Soft delete record by ID (marks as deleted without removing from database).

        Args:
            session: SQLAlchemy session
            record_id: ID of the record to soft delete
            user_id: ID of the user performing the deletion
        """
        record_id = validators.validate_record_id(record_id, self.model_name)
        user_id = validators.validate_record_id(user_id, "User")

        db_object = self._get_by_id(session, record_id)
        if not db_object:
            self._raise_not_found_error(record_id)

        if hasattr(db_object, 'is_deleted') and hasattr(db_object, 'deleted_at') and hasattr(db_object, 'deleted_by'):
            setattr(db_object, 'is_deleted', True)
            setattr(db_object, 'deleted_at', datetime.now(timezone.utc))
            setattr(db_object, 'deleted_by', user_id)
            session.add(db_object)
            session.flush()
        else:
            context = ErrorContext(operation="soft_delete", component=self.model_name, additional_info={"id": record_id})
            raise ValidationError(f"{self.model_name} does not support soft deletion (missing required fields: is_deleted, deleted_at, deleted_by)",context=context,severity=ErrorSeverity.HIGH)

    @handle_crud_errors(operation_name="RESTORE")
    def _restore(self, session: Session, record_id: str) -> None:
        """
        Restore soft-deleted record by ID.

        Args:
            session: SQLAlchemy session
            record_id: ID of the record to restore
        """
        record_id = validators.validate_record_id(record_id, self.model_name)

        db_object = self._get_by_id(session, record_id)
        if not db_object:
            self._raise_not_found_error(record_id)

        if hasattr(db_object, 'is_deleted') and hasattr(db_object, 'deleted_at') and hasattr(db_object, 'deleted_by'):
            setattr(db_object, 'is_deleted', False)
            setattr(db_object, 'deleted_at', None)
            setattr(db_object, 'deleted_by', None)
            session.add(db_object)
            session.flush()
        else:
            context = ErrorContext(operation="restore", component=self.model_name, additional_info={"id": record_id})
            raise ValidationError(f"{self.model_name} does not support restoration (missing required fields: is_deleted, deleted_at, deleted_by)",context=context,severity=ErrorSeverity.HIGH)

    @handle_crud_errors(operation_name="EXISTS")
    def _exists(self, session: Session, record_id: str) -> bool:
        """
        Check if record exists by ID.

        Args:
            session: SQLAlchemy session
            record_id: ID of the record to check

        Returns:
            True if record exists, False otherwise
        """
        record_id = validators.validate_record_id(record_id, self.model_name)

        query = select(exists().where(self.model.id == record_id))
        result = session.execute(query).scalar()

        return bool(result)

    @handle_crud_errors(operation_name="GET_ALL")
    def _get_all( self, session: Session, *, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, relationships: Optional[List[str]] = None, load_all_relationships: bool = False, **filters) -> List[ModelType]:
        """
        Get all records with pagination, filtering, and optional ordering.

        Args:
            session: SQLAlchemy session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Field name to order by
            order_desc: If True, order in descending order
            include_deleted: If True, include soft-deleted records
            relationships: List of specific relationship names to load
            load_all_relationships: If True, load all relationships
            **filters: Field equality filters

        Returns:
            List of model instances
        """
        if skip < 0:
            context = ErrorContext(operation="get_all", component=self.model_name, additional_info={"skip": skip})
            raise ValidationError("Skip parameter must be non-negative", context=context, severity=ErrorSeverity.MEDIUM)

        if limit <= 0:
            context = ErrorContext(operation="get_all", component=self.model_name, additional_info={"limit": limit})
            raise ValidationError("Limit parameter must be positive", context=context, severity=ErrorSeverity.MEDIUM)

        if limit > MAX_QUERY_LIMIT:
            context = ErrorContext(operation="get_all", component=self.model_name, additional_info={"limit": limit})
            raise ValidationError(f"Limit parameter exceeds maximum allowed value of {MAX_QUERY_LIMIT}",context=context,severity=ErrorSeverity.MEDIUM)

        query = select(self.model)

        # Filter out soft-deleted records unless explicitly requested
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.where(getattr(self.model, 'is_deleted').is_(False))

        # Apply custom filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
            else:
                self.logger.warning(f"Attempted to filter by non-existent field '{key}' on {self.model_name}",extra={"field": key, "model": self.model_name})

        # Apply ordering
        if order_by:
            if hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                query = query.order_by(order_field.desc() if order_desc else order_field)
            else:
                self.logger.warning(f"Attempted to order by non-existent field '{order_by}' on {self.model_name}",extra={"field": order_by, "model": self.model_name})

        # Load relationships if requested
        if load_all_relationships:
            for relationship_name in self.model.__mapper__.relationships.keys():
                query = query.options(selectinload(getattr(self.model, relationship_name)))
        elif relationships:
            for rel_name in relationships:
                if rel_name in self.model.__mapper__.relationships.keys():
                    query = query.options(selectinload(getattr(self.model, rel_name)))
                else:
                    self.logger.warning(f"Relationship '{rel_name}' not found in {self.model_name}",extra={"relationship": rel_name, "model": self.model_name})

        # Apply pagination
        query = query.offset(skip).limit(limit)

        results = session.execute(query).scalars().all()
        return list(results)

    @handle_crud_errors(operation_name="COUNT")
    def _count(self, session: Session, *, include_deleted: bool = False, **filters) -> int:
        """
        Count total records with optional filters.

        Args:
            session: SQLAlchemy session
            include_deleted: If True, include soft-deleted records in count
            **filters: Field equality filters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(self.model)

        # Filter out soft-deleted records unless explicitly requested
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.where(getattr(self.model, 'is_deleted').is_(False))  

        # Apply custom filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
            else:
                self.logger.warning(f"Attempted to filter by non-existent field '{key}' on {self.model_name}",extra={"field": key, "model": self.model_name})

        result = session.execute(query).scalar()
        return result or 0