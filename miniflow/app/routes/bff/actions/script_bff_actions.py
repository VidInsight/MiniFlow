import os
from typing import List, Dict, Any, Optional
from miniflow.database.models import ScriptType
from miniflow.core.exceptions import (
    MiniflowException, ResourceNotFound, ValidationError, 
    DatabaseError, ErrorContext, ErrorSeverity
)


class ScriptActions:
    """Minimal Script operations for BFF layer"""
    
    def __init__(self, orchestrator):
        """
        Initialize Script operations
        
        Args:
            orchestrator: ScriptOrchestrator instance
        """
        self.orchestrator = orchestrator

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking"""
        return ErrorContext(
            operation=operation,
            component="ScriptActions",
            additional_info=kwargs
        )

    def _convert_language_to_enum(self, language_str: str) -> ScriptType:
        """
        Convert string language to ScriptType enum
        
        Args:
            language_str: Language string (e.g., "PYTHON", "BASH")
            
        Returns:
            ScriptType: Enum value
            
        Raises:
            ValidationError: If language is not supported
        """
        try:
            return ScriptType(language_str.upper())
        except ValueError:
            valid_languages = [e.value for e in ScriptType]
            context = self._create_error_context("convert_language", language=language_str)
            raise ValidationError(
                f"Invalid language '{language_str}'. Valid options: {valid_languages}",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )

    async def create_script(
        self,
        name: str,
        language: str,
        category: str,
        content: str,
        subcategory: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = "1.0.0",
        required_packages: Optional[List[str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        test_input_params: Optional[Dict[str, Any]] = None,
        test_output_params: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create script with automatic file creation
        
        Args:
            name: Script name (unique)
            language: Script language (PYTHON, BASH)
            category: Script category (required)
            content: Script content (required)
            subcategory: Optional subcategory
            description: Optional description
            version: Script version (default: "1.0.0")
            required_packages: Optional package list
            input_schema: Optional input JSON schema
            output_schema: Optional output JSON schema
            test_input_params: Optional test input parameters
            test_output_params: Optional test output parameters
            tags: Optional tags list
            author: Optional author name
            
        Returns:
            Dict: Script.to_dict() - Pure model response
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If script creation fails
        """
        try:
            # Validate required fields
            if not name or not name.strip():
                context = self._create_error_context("create_script", name=name)
                raise ValidationError(
                    "Script name cannot be empty",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            if not content or not content.strip():
                context = self._create_error_context("create_script", name=name)
                raise ValidationError(
                    "Script content cannot be empty",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            if not category or not category.strip():
                context = self._create_error_context("create_script", name=name)
                raise ValidationError(
                    "Script category cannot be empty",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            # Convert language string to enum
            language_enum = self._convert_language_to_enum(language)
            
            # Prepare kwargs for orchestrator
            kwargs = {}
            if description is not None:
                kwargs['description'] = description
            if version is not None:
                kwargs['version'] = version
            if required_packages is not None:
                kwargs['required_packages'] = required_packages
            if input_schema is not None:
                kwargs['input_schema'] = input_schema
            if output_schema is not None:
                kwargs['output_schema'] = output_schema
            if test_input_params is not None:
                kwargs['test_input_params'] = test_input_params
            if test_output_params is not None:
                kwargs['test_output_params'] = test_output_params
            if tags is not None:
                kwargs['tags'] = tags
            if author is not None:
                kwargs['author'] = author
            
            # Call orchestrator to create script + file
            script_record = self.orchestrator.create_script(
                name=name.strip(),
                language=language_enum,
                content=content,
                category=category.strip(),
                subcategory=subcategory.strip() if subcategory else None,
                **kwargs
            )
            
            # Return pure model response
            return script_record.to_dict()
            
        except (ValidationError, ResourceNotFound):
            raise
        except Exception as e:
            context = self._create_error_context("create_script", name=name, language=language)
            raise DatabaseError(
                f"Failed to create script '{name}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def get_script_record(self, script_id: str) -> Dict[str, Any]:
        """
        Get single script record by ID
        
        Args:
            script_id: Script ID
            
        Returns:
            Dict: Script.to_dict() - Pure model response
            
        Raises:
            ResourceNotFound: If script not found
            DatabaseError: If database query fails
        """
        try:
            script_record = self.orchestrator.get_script_by_id(script_id)
            if not script_record:
                context = self._create_error_context("get_script_record", script_id=script_id)
                raise ResourceNotFound(
                    f"Script '{script_id}' not found",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            # Return pure model response
            return script_record.to_dict()
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_script_record", script_id=script_id)
            raise DatabaseError(
                f"Failed to retrieve script '{script_id}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def get_script_records(
        self,
        language: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of script records with optional filtering
        
        Args:
            language: Optional filter by language
            category: Optional filter by category
            
        Returns:
            List[Dict]: List of Script.to_dict() - Pure model responses
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            # Build filters
            filters = {}
            if language is not None:
                # Convert language string to enum for filtering
                language_enum = self._convert_language_to_enum(language)
                filters['language'] = language_enum
            if category is not None:
                filters['category'] = category
            
            # Get filtered scripts
            if filters:
                script_records = self.orchestrator.filter_scripts(**filters)
            else:
                script_records = self.orchestrator.get_all_scripts()
            
            # Return pure model responses
            return [script_record.to_dict() for script_record in script_records]
            
        except ValidationError:
            raise
        except Exception as e:
            context = self._create_error_context(
                "get_script_records",
                language=language,
                category=category
            )
            raise DatabaseError(
                f"Failed to retrieve script records: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )

    async def delete_script(self, script_id: str) -> Dict[str, Any]:
        """
        Delete script with detailed response
        
        Args:
            script_id: Script ID
            
        Returns:
            Dict: ScriptDeleteResponse schema format
            
        Raises:
            ResourceNotFound: If script not found
            DatabaseError: If deletion fails
        """
        try:
            # Get script before deletion
            script_record = self.orchestrator.get_script_by_id(script_id)
            if not script_record:
                context = self._create_error_context("delete_script", script_id=script_id)
                raise ResourceNotFound(
                    f"Script '{script_id}' not found",
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
            
            # Check if physical file exists before deletion
            file_existed = script_record.file_path and os.path.exists(script_record.file_path)
            file_path = script_record.file_path
            
            # Delete from database first
            deleted_record = self.orchestrator.delete_script_by_id(script_id)
            
            # Manually delete physical file (orchestrator might not handle filesystem)
            physical_file_deleted = False
            if file_existed and file_path:
                try:
                    os.remove(file_path)
                    physical_file_deleted = True
                except (OSError, FileNotFoundError) as file_error:
                    # File removal failed, but database deletion succeeded
                    pass
            
            # Double-check if file was actually removed
            if file_existed and file_path:
                physical_file_deleted = not os.path.exists(file_path)
            
            # Collect any warnings
            warnings = []
            if file_existed and not physical_file_deleted:
                warnings.append(f"Physical file could not be removed: {script_record.file_path}")
            elif not file_existed and script_record.file_path:
                warnings.append("Physical file did not exist on filesystem")
            
            # Return enhanced delete response
            return {
                "deleted_record": deleted_record.to_dict(),
                "database_deleted": True,
                "physical_file_deleted": physical_file_deleted,
                "file_existed": file_existed,
                "message": f"Script '{script_record.name}' deleted successfully",
                "warnings": warnings if warnings else None
            }
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("delete_script", script_id=script_id)
            raise DatabaseError(
                f"Failed to delete script '{script_id}': {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH,
                source_error=e
            )