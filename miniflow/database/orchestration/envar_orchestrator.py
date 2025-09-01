from typing import List, Optional
from miniflow.database.models import EnvironmentVariable, VariableScope, VariableType
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session

from miniflow.core.exceptions import OrchestrationError


class EnvironmentVariableOrchestrator(BaseOrchestrator):
    """
    Environment Variable orchestrator for basic CRUD operations.
    
    Provides simple methods for managing environment variables
    with automatic session management through DatabaseEngine.
    """

    @with_session
    def create_environment_variable(self, session, name: str, value: str, **kwargs) -> EnvironmentVariable:
        """
        Create a new environment variable.

        Args:
            session: Database session
            name (str): Name of the environment variable
            value (str): Value of the environment variable
            **kwargs: Additional fields like description, variable_type, scope etc.

        Returns:
            EnvironmentVariable: Created environment variable instance

        Raises:
            OrchestrationError: If variable with same name already exists or validation fails
        """
        try:
            # Check if variable already exists
            existing = self.envar_crud.find_by_name(session, name)
            if existing:
                context = self._create_error_context("create", name=name)
                raise OrchestrationError(f"Environment variable '{name}' already exists", context=context)

            return self.envar_crud.create_environment_variable(session, name=name, value=value, **kwargs)
        except Exception as e:
            context = self._create_error_context("create", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_environment_variable_by_id(self, session, record_id: str) -> Optional[EnvironmentVariable]:
        """
        Get environment variable by ID.

        Args:
            session: Database session
            record_id (str): ID of the environment variable

        Returns:
            Optional[EnvironmentVariable]: Environment variable if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.envar_crud.find_by_id(session, record_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_environment_variable_by_name(self, session, name: str) -> Optional[EnvironmentVariable]:
        """
        Get environment variable by name.

        Args:
            session: Database session
            name (str): Name of the environment variable

        Returns:
            Optional[EnvironmentVariable]: Environment variable if found, None otherwise

        Raises:
            DatabaseQueryError: If database query fails
        """
        try:
            return self.envar_crud.find_by_name(session, name)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_environment_variable_by_name(self, session, name: str, value: str, **kwargs) -> EnvironmentVariable:
        """
        Update environment variable by name.

        Args:
            session: Database session
            name (str): Name of the environment variable
            value (str): New value
            **kwargs: Additional fields to update

        Returns:
            EnvironmentVariable: Updated environment variable

        Raises:
            OrchestrationError: If variable not found or validation fails
        """
        try:
            envar = self.envar_crud.find_by_name(session, name)
            if not envar:
                self._handle_not_found("Environment variable", name, "update_by_name")
            
            return self.envar_crud.update_environment_variable(session, envar.id, value=value, **kwargs)
        except Exception as e:
            context = self._create_error_context("update_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_environment_variable_by_id(self, session, record_id: str, **kwargs) -> EnvironmentVariable:
        """
        Update environment variable by ID.

        Args:
            session: Database session
            record_id (str): ID of the environment variable
            **kwargs: Fields to update

        Returns:
            EnvironmentVariable: Updated environment variable

        Raises:
            OrchestrationError: If variable not found or validation fails
        """
        try:
            envar = self.envar_crud.find_by_id(session, record_id)
            if not envar:
                self._handle_not_found("Environment variable", record_id, "update_by_id")
            
            return self.envar_crud.update_environment_variable(session, record_id, **kwargs)
        except Exception as e:
            context = self._create_error_context("update_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_environment_variable_by_name(self, session, name: str) -> Optional[EnvironmentVariable]:
        """
        Delete environment variable by name.

        Args:
            session: Database session
            name (str): Name of the environment variable

        Returns:
            Optional[EnvironmentVariable]: Deleted environment variable if found

        Raises:
            OrchestrationError: If database operation fails
        """
        try:
            envar = self.envar_crud.find_by_name(session, name)
            if not envar:
                return None
            
            return self.envar_crud.delete_environment_variable(session, envar.id)
        except Exception as e:
            context = self._create_error_context("delete_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_environment_variable_by_id(self, session, record_id: str) -> EnvironmentVariable:
        """
        Delete environment variable by ID.

        Args:
            session: Database session
            record_id (str): ID of the environment variable

        Returns:
            EnvironmentVariable: Deleted environment variable

        Raises:
            OrchestrationError: If variable not found or deletion fails
        """
        try:
            envar = self.envar_crud.find_by_id(session, record_id)
            if not envar:
                self._handle_not_found("Environment variable", record_id, "delete_by_id")
            
            return self.envar_crud.delete_environment_variable(session, record_id)
        except Exception as e:
            context = self._create_error_context("delete_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all_environment_variable(self, session) -> List[EnvironmentVariable]:
        """
        Get all environment variables.

        Args:
            session: Database session

        Returns:
            List[EnvironmentVariable]: List of all environment variables

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.envar_crud.get_all(session)
        except Exception as e:
            context = self._create_error_context("get_all")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_environment_variables(self, session, **kwargs) -> List[EnvironmentVariable]:
        """
        Filter environment variables by criteria.

        Args:
            session: Database session
            **kwargs: Filter criteria (e.g. scope, variable_type, etc.)

        Returns:
            List[EnvironmentVariable]: List of filtered environment variables

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.envar_crud.filter(session, filters=kwargs)
        except Exception as e:
            context = self._create_error_context("filter", filters=kwargs)
            raise OrchestrationError(str(e), context=context) from e