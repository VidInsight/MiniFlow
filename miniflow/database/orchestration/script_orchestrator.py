"""
Script Orchestrator

This module provides high-level orchestration for script operations,
managing database sessions and coordinating complex script workflows.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from miniflow.database.models import Script, ScriptType
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError
import os

class ScriptOrchestrator(BaseOrchestrator):
    """Script orchestrator for basic CRUD operations and script management."""

    def __init__(self, database_engine):
        """
        Initialize script orchestrator
        
        Args:
            database_engine: DatabaseEngine instance
        """
        super().__init__(database_engine)
        # Script CRUD instance is already initialized in BaseOrchestrator
        
        # Fixed scripts base path
        self.scripts_base_path = Path("scripts")
        
        # Script type to file extension mapping
        self.extension_mapping = {
            ScriptType.PYTHON: ".py",
            ScriptType.BASH: ".sh"
        }

    def _get_file_extension(self, language: ScriptType) -> str:
        """Get file extension based on script language"""
        return self.extension_mapping.get(language, ".txt")

    def _create_script_file(self, name: str, category: str, subcategory: Optional[str], 
                          language: ScriptType, content: str) -> str:
        """
        Create script file with category/subcategory structure and return absolute path
        
        Args:
            name: Script name (will be used as filename)
            category: Script category (required)  
            subcategory: Script subcategory (optional)
            language: Script language type
            content: Script content
            
        Returns:
            str: Absolute path to created file
            
        Raises:
            OrchestrationError: If file creation fails
        """
        try:
            # Sanitize name for filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            # Get file extension and create filename
            extension = self._get_file_extension(language)
            filename = f"{safe_name}{extension}"
            
            # Build directory path: scripts/category or scripts/category/subcategory
            if subcategory:
                dir_path = self.scripts_base_path / category / subcategory
            else:
                dir_path = self.scripts_base_path / category
                
            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = dir_path / filename
            absolute_path = file_path.resolve()
            
            # Create file with exclusive creation mode to prevent race conditions
            try:
                with open(absolute_path, 'x', encoding='utf-8') as f:  # 'x' = exclusive creation
                    f.write(content)
            except FileExistsError:
                context = self._create_error_context("create_script_file", file_path=str(absolute_path))
                raise OrchestrationError(f"File already exists: {absolute_path}", context=context)
                
            self.logger.info(f"Successfully created script file: {absolute_path}")
            return str(absolute_path)
            
        except (PermissionError, OSError) as e:
            context = self._create_error_context("create_script_file", name=name, category=category)
            raise OrchestrationError(f"Failed to create script file: {str(e)}", context=context) from e

    @with_session
    def create_script(self, session, name: str, language: ScriptType, content: str, 
                     category: str, subcategory: Optional[str] = None, **kwargs) -> Script:
        """
        Create a new script record with automatic file creation.

        Args:
            session: Database session
            name (str): Name of the script
            language (ScriptType): Script language/type
            content (str): Script content
            category (str): Script category (required)
            subcategory (Optional[str]): Script subcategory (optional)
            **kwargs: Additional script attributes (description, version, etc.)

        Returns:
            Script: Created script record

        Raises:
            OrchestrationError: If script creation fails
        """
        try:
            # Check if script already exists
            existing = self.script_crud.find_by_name(session, name)
            if existing:
                context = self._create_error_context("create", name=name)
                raise OrchestrationError(f"Script '{name}' already exists", context=context)

            # Create physical file and get absolute path
            absolute_file_path = self._create_script_file(
                name=name,
                category=category,
                subcategory=subcategory,
                language=language,
                content=content
            )

            # Create database record with the generated file path
            # Remove file_path from kwargs to avoid conflict
            kwargs.pop('file_path', None)
            
            return self.script_crud.create_script_record(
                session,
                name=name,
                language=language,
                content=content,
                file_path=absolute_file_path,
                category=category,
                subcategory=subcategory,
                **kwargs
            )
        except Exception as e:
            context = self._create_error_context("create", name=name, category=category)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_script_by_id(self, session, record_id: str) -> Optional[Script]:
        """
        Get script by ID.

        Args:
            session: Database session
            record_id (str): ID of the script

        Returns:
            Optional[Script]: Script if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.script_crud.find_by_id(session, record_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_script_by_name(self, session, name: str) -> Optional[Script]:
        """
        Get script by name.

        Args:
            session: Database session
            name (str): Name of the script

        Returns:
            Optional[Script]: Script if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.script_crud.find_by_name(session, name)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_script_by_id(self, session, record_id: str) -> Script:
        """
        Delete script by ID.

        Args:
            session: Database session
            record_id (str): ID of the script

        Returns:
            Script: Deleted script

        Raises:
            OrchestrationError: If script not found or deletion fails
        """
        try:
            # Get script first to obtain file path
            script = self.script_crud.find_by_id(session, record_id)
            if not script:
                context = self._create_error_context("delete_by_id", record_id=record_id)
                raise OrchestrationError(f"Script with ID '{record_id}' not found", context=context)
            
            # Store file path before deletion
            file_path = script.file_path
            
            # Delete database record
            deleted_script = self.script_crud.delete(session, record_id)
            
            # Delete file from filesystem if it exists
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Successfully deleted script file: {file_path}")
                except OSError as e:
                    self.logger.warning(f"Failed to delete script file {file_path}: {str(e)}")
                    # Don't raise exception for file deletion failure
            
            return deleted_script
            
        except Exception as e:
            context = self._create_error_context("delete_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all_scripts(self, session) -> List[Script]:
        """
        Get all scripts.

        Args:
            session: Database session

        Returns:
            List[Script]: List of all scripts

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.script_crud.get_all(session)
        except Exception as e:
            context = self._create_error_context("get_all")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_scripts(self, session, **kwargs) -> List[Script]:
        """
        Filter scripts by criteria.

        Args:
            session: Database session
            **kwargs: Filter criteria (e.g. language, category, etc.)

        Returns:
            List[Script]: List of filtered scripts

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.script_crud.filter(session, filters=kwargs)
        except Exception as e:
            context = self._create_error_context("filter", filters=kwargs)
            raise OrchestrationError(str(e), context=context) from e


    @with_session
    def delete_script_by_name(self, session, name: str) -> Optional[Script]:
        """
        Delete script by name.

        Args:
            session: Database session
            name (str): Name of the script to delete

        Returns:
            Optional[Script]: Deleted script if found, None otherwise

        Raises:
            OrchestrationError: If database operation fails
        """
        try:
            script = self.script_crud.find_by_name(session, name)
            if not script:
                return None
            
            return self.script_crud.delete(session, script.id)
        except Exception as e:
            context = self._create_error_context("delete_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e