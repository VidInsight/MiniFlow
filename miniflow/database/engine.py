import time
import threading
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import SQLAlchemyError

from .config import DatabaseConfig
from .models import Base

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import (
    ConfigurationError, DatabaseError, DatabaseConnectionError, 
    DatabaseQueryError, InvalidState, ErrorContext, ErrorSeverity
)


logger = get_logger("miniflow_database")


class DatabaseEngine:
    """Simplified SQLAlchemy Engine ve Session yönetimi için ana sınıf"""

    def __init__(self, config: DatabaseConfig) -> None:
        """Engine instance'ı oluşturur ve konfigrasyon ayarlar"""
        self._config = self._validate_config(config)
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._connection_string = config.get_connection_string()

        # Thread-safe state management
        self.is_alive = False
        self._lock = threading.RLock()

        logger.info(f"DatabaseEngine initialized for {config.db_type.value}:{config.db_name}")

    def _validate_config(self, config: DatabaseConfig) -> DatabaseConfig:
        """Configuration validation"""
        if not config:
            context = ErrorContext(operation="validate_config", component="DatabaseEngine")
            raise ConfigurationError("Configuration cannot be None",  context=context,  severity=ErrorSeverity.HIGH)

        if not config.db_name:
            context = ErrorContext(operation="validate_config", component="DatabaseEngine")
            raise ConfigurationError("Database name is required", context=context, severity=ErrorSeverity.HIGH)

        if hasattr(config, 'engine_config') and config.engine_config:
            if hasattr(config.engine_config, 'pool_size') and config.engine_config.pool_size <= 0:
                context = ErrorContext(operation="validate_config", component="DatabaseEngine")
                raise ConfigurationError("Pool size must be positive", context=context, severity=ErrorSeverity.MEDIUM)

        return config

    def start(self, create_tables: bool = False) -> None:
        """Database engine'i başlatır ve kullanıma hazır hale getirir"""
        with self._lock:
            if self.is_alive:
                logger.warning("Engine is already running")
                return

            try:
                self._create_engine()
                self._create_session_factory()
                self.is_alive = True
                logger.info(f"Database engine started successfully: {self._config.db_type.value}")

                # Tabloları oluştur (eğer istenirse)
                if create_tables:
                    self.create_tables(Base.metadata)
                    logger.info("Database tables created successfully")

            except Exception as e:
                logger.error(f"Failed to start engine: {e}")
                self.is_alive = False
                self._cleanup_resources()
                
                context = ErrorContext(operation="start_engine", component="DatabaseEngine")
                if isinstance(e, SQLAlchemyError):
                    raise DatabaseConnectionError(
                        f"Failed to start database engine: {str(e)}",
                        context=context,
                        severity=ErrorSeverity.HIGH,
                        source_error=e
                    )
                else:
                    raise DatabaseError(
                        f"Failed to start database engine: {str(e)}",
                        context=context,
                        severity=ErrorSeverity.HIGH,
                        source_error=e
                    )

    def stop(self) -> None:
        """Database engine'i durdurur ve kaynakları temizler"""
        with self._lock:
            if not self.is_alive:
                logger.warning("Engine is already stopped")
                return

            try:
                if self._engine:
                    self._engine.dispose()

                self._cleanup_resources()
                self.is_alive = False
                logger.info("Database engine stopped successfully")

            except Exception as e:
                logger.error(f"Error during engine shutdown: {e}")
                context = ErrorContext(operation="stop_engine", component="DatabaseEngine")
                raise DatabaseError(
                    f"Error during engine shutdown: {str(e)}",
                    context=context,
                    severity=ErrorSeverity.HIGH,
                    source_error=e
                )

    def _create_engine(self) -> None:
        """SQLAlchemy Engine oluşturur"""
        try:
            engine_config = self._config.engine_config.to_dict()

            self._engine = create_engine(
                self._connection_string,
                **engine_config
            )

            logger.debug(f"Engine created with config: {engine_config}")
        except Exception as e:
            context = ErrorContext(operation="create_engine", component="DatabaseEngine")
            raise DatabaseConnectionError(
                f"Failed to create database engine: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    def _create_session_factory(self) -> None:
        """Session factory oluşturur"""
        try:
            session_config = self._config.engine_config.get_session_config()

            session_kwargs = {
                'bind': self._engine,
                'autocommit': session_config['autocommit'],
                'autoflush': session_config['autoflush'],
                'expire_on_commit': session_config['expire_on_commit']
            }

            # Isolation level handling
            if self._config.engine_config.isolation_level:
                session_kwargs['bind'] = self._engine.execution_options(
                    isolation_level=self._config.engine_config.isolation_level
                )

            self._session_factory = sessionmaker(**session_kwargs)
            logger.debug("Session factory created")
        except Exception as e:
            context = ErrorContext(operation="create_session_factory", component="DatabaseEngine")
            raise DatabaseError(
                f"Failed to create session factory: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    def _cleanup_resources(self) -> None:
        """Tüm kaynakları temizler"""
        self._engine = None
        self._session_factory = None

    @property
    def engine(self) -> Engine:
        """SQLAlchemy Engine instance'ını döner"""
        if not self.is_alive:
            context = ErrorContext(operation="get_engine", component="DatabaseEngine")
            raise InvalidState(
                "Engine not initialized. Call start() method first.",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        return self._engine

    def get_session(self) -> Session:
        """Yeni Session instance oluşturur ve döner"""
        if not self.is_alive:
            context = ErrorContext(operation="get_session", component="DatabaseEngine")
            raise InvalidState(
                "Engine not initialized. Call start() method first.",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        try:
            session = self._session_factory()
            logger.debug("Session created")
            return session
        except Exception as e:
            context = ErrorContext(operation="get_session", component="DatabaseEngine")
            raise DatabaseQueryError(
                f"Failed to create session: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    @contextmanager
    def session_context(self, auto_commit: bool = True, auto_flush: bool = True):
        """
        Session context manager for automatic session lifecycle management.
        
        This context manager:
        1. Creates a new session from the session factory
        2. Yields the session for use in database operations
        3. Automatically flushes changes if auto_flush=True (before commit)
        4. Automatically commits changes if auto_commit=True
        5. Automatically rolls back on exceptions
        6. Ensures session cleanup in finally block
        
        Args:
            auto_commit (bool): Whether to automatically commit changes. Default True.
            auto_flush (bool): Whether to automatically flush before commit. Default True.
            
        Usage:
            with engine.session_context() as session:
                # Database operations
                user = User(name="John")
                session.add(user)
                # Auto-flush and auto-commit will handle the rest
        """
        session = None
        try:
            session = self._session_factory()
            logger.debug("Session created for context")
            yield session

            # Auto-flush and auto-commit logic
            if session.is_active:
                # First, flush any pending changes to get IDs and ensure consistency
                if auto_flush and (session.dirty or session.new or session.deleted):
                    session.flush()
                    logger.debug("Session auto-flushed")
                
                # Then commit if requested
                if auto_commit:
                    session.commit()
                    logger.debug("Session auto-committed")
                elif auto_flush:
                    # If we flushed but not committing, log this state
                    logger.debug("Session flushed but not committed (auto_commit=False)")

        except Exception as e:
            # Auto-rollback logic: rollback on any exception
            if session and session.is_active:
                try:
                    session.rollback()
                    logger.debug("Session rolled back due to error")
                except Exception as rollback_error:
                    logger.warning(f"Rollback failed: {rollback_error}")
            
            # Re-raise with proper context
            context = ErrorContext(operation="session_context", component="DatabaseEngine")
            if isinstance(e, SQLAlchemyError):
                raise DatabaseQueryError(f"Database operation failed: {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)
            else:
                raise

        finally:
            # Session cleanup: always close the session
            if session:
                try:
                    session.close()
                    logger.debug("Session closed")
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")

    def create_tables(self, base_metadata) -> None:
        """Database'de tüm tabloları oluşturur"""
        if not self.is_alive:
            self.start()
            
        try:
            base_metadata.create_all(bind=self._engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            context = ErrorContext(operation="create_tables", component="DatabaseEngine")
            raise DatabaseError(f"Failed to create tables: {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def drop_tables(self, base_metadata) -> None:
        """Database'den tüm tabloları siler"""
        if not self.is_alive:
            self.start()
            
        try:
            base_metadata.drop_all(bind=self._engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            context = ErrorContext(operation="drop_tables", component="DatabaseEngine")
            raise DatabaseError(f"Failed to drop tables: {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def test_connection(self) -> bool:
        """Simple database bağlantı testi"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                return True
        except SQLAlchemyError as e:
            logger.warning(f"Database connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False

    def health_check(self) -> bool:
        """Simple health check"""
        return self.is_alive and self.test_connection()

    def get_connection_info(self) -> Dict[str, Any]:
        """Basic connection information"""
        return {
            'database_type': self._config.db_type.value,
            'database_name': self._config.db_name,
            'is_alive': self.is_alive
        }

    def __repr__(self) -> str:
        """String representation"""
        return (f"DatabaseEngine("
                f"db_type={self._config.db_type.value}, "
                f"db_name={self._config.db_name}, "
                f"is_alive={self.is_alive})")

    def __enter__(self):
        """Context manager entry"""
        if not self.is_alive:
            self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# =================================================================================================== FACTORY FUNCTION ==
def create_database_engine(config: DatabaseConfig, auto_start: bool = True, create_tables: bool = False) -> DatabaseEngine:
    """Enhanced DatabaseEngine factory fonksiyonu"""
    try:
        logger.info(f"Creating database engine for {config.db_type.value}:{config.db_name}")
        db_engine = DatabaseEngine(config)

        if auto_start:
            db_engine.start(create_tables=create_tables)

        return db_engine

    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise