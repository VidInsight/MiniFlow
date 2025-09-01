from typing import List, Optional
from miniflow.database.models import EnvironmentVariable, VariableScope, VariableType
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session


class EnvironmentVariableOrchestrator(BaseOrchestrator):
    """
    Environment Variable orchestrator for basic CRUD operations.
    
    Provides simple methods for managing environment variables
    with automatic session management through DatabaseEngine.
    """

    @with_session
    def create_record(self, session, name: str, value: str, **kwargs) -> EnvironmentVariable:
        """
        Create new environment variable.
        
        Args:
            name: Variable name
            value: Variable value
            **kwargs: Additional parameters (scope, type, description)
            
        Returns:
            Created EnvironmentVariable instance
        """
        return self.envar_crud.create_environment_variable(session, name, value, **kwargs)

    @with_session
    def get_record_by_id(self, session, record_id: str) -> Optional[EnvironmentVariable]:
        """
        Get environment variable by ID.
        
        Args:
            record_id: Variable ID
            
        Returns:
            EnvironmentVariable instance or None
        """
        return self.envar_crud.find_by_id(session, record_id)

    @with_session
    def get_record_by_name(self, session, name: str) -> Optional[EnvironmentVariable]:
        """
        Get environment variable by name.

        Args:
            name: Variable name

        Returns:
            EnvironmentVariable instance or None
        """
        return self.envar_crud.find_by_name(session, name)

    @with_session
    def update_record_by_name(self, session, name: str, value: str, **kwargs) -> EnvironmentVariable:
        """
        Update environment variable.
        
        Args:
            name: Variable name
            value: New value
            **kwargs: Additional parameters to update
            
        Returns:
            Updated EnvironmentVariable instance
        """
        variable = self.envar_crud.find_by_name(session, name)
        if not variable:
            self._handle_not_found("EnvironmentVariable", name, "update_record_by_name")
        
        return self.envar_crud.update_environment_variable(session, variable.id, value=value, **kwargs)

    @with_session
    def update_record_by_id(self, session, record_id: str, **kwargs) -> EnvironmentVariable:
        """
        Update environment variable.

        Args:
            record_id: Variable ID
            **kwargs: Parameters to update

        Returns:
            Updated EnvironmentVariable instance
        """
        return self.envar_crud.update_environment_variable(session, record_id, **kwargs)

    @with_session
    def delete_variable_by_name(self, session, name: str) -> Optional[EnvironmentVariable]:
        """
        Delete environment variable.
        
        Args:
            name: Variable name
            
        Returns:
            Deleted EnvironmentVariable instance or None if not found
        """
        variable = self.envar_crud.find_by_name(session, name)
        if not variable:
            return None

        return self.envar_crud.delete_environment_variable(session, variable.id)

    @with_session
    def delete_variable_by_id(self, session, record_id: str) -> EnvironmentVariable:
        """
        Delete environment variable.

        Args:
            record_id: Variable ID

        Returns:
            Deleted EnvironmentVariable instance
        """
        return self.envar_crud.delete_environment_variable(session, record_id)

    @with_session
    def list_variables(self, session) -> List[EnvironmentVariable]:
        """
        List environment variables.
        
        Returns:
            List of EnvironmentVariable instances
        """
        return self.envar_crud.get_all(session)

    @with_session 
    def get_variables_by_filter(self, session, filters: dict) -> List[EnvironmentVariable]:
        """
        Get environment variables by filter criteria.
        
        Args:
            filters: Dictionary of field filters
            
        Returns:
            List of EnvironmentVariable instances matching filter
        """
        return self.envar_crud.filter(session, filters, limit=1000)

    @with_session
    def get_variables_by_scope(self, session, scope: str) -> List[EnvironmentVariable]:
        """
        Get environment variables by scope.
        
        Args:
            scope: Variable scope string
            
        Returns:
            List of EnvironmentVariable instances in scope
        """
        scope_enum = VariableScope(scope)
        return self.envar_crud.filter(session, {'scope': scope_enum}, limit=1000)

    def create_variable(self, name: str, value: str, description: Optional[str] = None, 
                       variable_type: VariableType = VariableType.STRING, 
                       scope: VariableScope = VariableScope.GLOBAL) -> EnvironmentVariable:
        """
        Create new environment variable with parameters.
        
        Args:
            name: Variable name
            value: Variable value
            description: Optional description
            variable_type: Variable type enum
            scope: Variable scope enum
            
        Returns:
            Created EnvironmentVariable instance
        """
        return self.create_record(name, value, description=description, 
                                variable_type=variable_type, scope=scope)

    def get_variable_by_name(self, name: str) -> Optional[EnvironmentVariable]:
        """
        Get environment variable by name.
        
        Args:
            name: Variable name
            
        Returns:
            EnvironmentVariable instance or None
        """
        return self.get_record_by_name(name)

    def update_variable(self, name: str, **kwargs) -> EnvironmentVariable:
        """
        Update environment variable by name.
        
        Args:
            name: Variable name
            **kwargs: Update parameters (can include value, description, etc.)
            
        Returns:
            Updated EnvironmentVariable instance
        """
        # Get current variable to get current value if not updating value
        variable = self.get_record_by_name(name)
        if not variable:
            self._handle_not_found("EnvironmentVariable", name, "update_variable")
        
        # If value is provided, use it; otherwise keep current value
        value = kwargs.pop('value', variable.value)
        return self.update_record_by_name(name, value, **kwargs)

    def delete_variable(self, name: str) -> bool:
        """
        Delete environment variable by name.
        
        Args:
            name: Variable name
            
        Returns:
            True if deleted, False if not found
        """
        result = self.delete_variable_by_name(name)
        return result is not None
