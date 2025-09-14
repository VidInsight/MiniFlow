"""
Script Operations - Enhanced with File Operations
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import ValidationError, DatabaseError
from ..base_operations import BaseBFFOperations
from .schemas import ScriptCreateRequest, ScriptUpdateRequest, ScriptFilterRequest
from miniflow.database.orchestration.script_orchestrator import ScriptOrchestrator


class ScriptOperations(BaseBFFOperations[ScriptOrchestrator]):
    def __init__(self, orchestrator: ScriptOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "script")

    def _simplify_workflow_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow verisini sade format'a çevir - Auto-reload test"""
        return {
            'id': item['id'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at'],
            'name': item['name'],
            'description': item['description'],
            'version': item['version'],
            'category': item['category'],
            'subcategory': item['subcategory'],
            'file_extension': item['file_extension'],
            'content': item['content'],
            'author': item['author'],
            'input_schema': item['input_schema'],
            'output_schema': item['output_schema'],
            'test_input_params': item['test_input_params'],
            'test_output_params': item['test_output_params'],
        }

    def _generate_file_path(self, name: str, category: str, subcategory: Optional[str], 
                           file_extension: Optional[str]) -> str:
        """Generate file path for script - matches existing pattern"""
        # Build file path: scripts/{category}/{subcategory}/{name}.{ext}
        parts = ["scripts", category]
        if subcategory:
            parts.append(subcategory)
        
        # Add filename with extension
        if file_extension and not file_extension.startswith('.'):
            file_extension = f".{file_extension}"
        elif not file_extension:
            file_extension = ".txt"  # Default extension
            
        filename = f"{name}{file_extension}"
        parts.append(filename)
        
        file_path = "/".join(parts)
        return file_path

    def _create_physical_file(self, file_path: str, content: str) -> tuple[bool, Optional[str]]:
        """Create physical file on filesystem - matches existing pattern"""
        try:
            # Create directory if not exists
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True, None
        except Exception as e:
            return False, str(e)

    def _update_physical_file(self, file_path: str, content: str) -> tuple[bool, Optional[str]]:
        """Update physical file content - matches existing pattern"""
        try:
            if not os.path.exists(file_path):
                return self._create_physical_file(file_path, content)
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True, None
        except Exception as e:
            return False, str(e)

    def _delete_physical_file(self, file_path: str) -> tuple[bool, bool, Optional[str]]:
        """Delete physical file - matches existing pattern"""
        try:
            if not file_path or not os.path.exists(file_path):
                return False, False, None
                
            os.remove(file_path)
            return True, True, None
        except Exception as e:
            return True, False, str(e)

    # CREATE WITH FILE OPERATIONS (Database first, then file with rollback)
    async def create_script_record(self, request: ScriptCreateRequest) -> Dict[str, Any]:
        """Create script record with physical file creation - atomic operation"""
        file_path = None
        database_record = None
        
        try:
            # Generate file path and calculate size
            file_path = self._generate_file_path(
                request.name, request.category, request.subcategory, request.file_extension
            )
            file_size = len(request.content.encode('utf-8'))
            
            # Prepare kwargs for orchestrator
            kwargs = {
                'file_path': file_path,
                'file_size': file_size,
                'content': request.content,
                'description': request.description,
                'version': request.version,
                'author': request.author
            }
            
            # Step 1: Create database record first
            database_record = self.orchestrator.create(
                name=request.name.strip(),
                category=request.category.strip(),
                subcategory=request.subcategory.strip() if request.subcategory else None,
                file_extension=request.file_extension,
                **kwargs
            )
            
            # Step 2: Create physical file
            file_created, file_error = self._create_physical_file(file_path, request.content)
            if not file_created:
                # Rollback database record if file creation fails
                try:
                    self.orchestrator.delete(database_record['id'])
                    self.logger.info(f"Rolled back database record due to file creation failure")
                except Exception as rollback_error:
                    self.logger.error(f"Failed to rollback database record: {rollback_error}")
                raise DatabaseError(f"Failed to create physical file: {file_error}")
            
            return {
                'action_status': True,
                'record_id': database_record['id'],
                'message': "Script creation successful",
                'file_operations': {
                    'physical_file_created': True,
                    'file_path': database_record['file_path'],
                    'file_size': database_record['file_size'],
                    'checksum': database_record.get('checksum')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create script: {str(e)}")
            # Cleanup any created files and database records on error
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Cleaned up file on error: {file_path}")
                except OSError as cleanup_error:
                    self.logger.warning(f"Failed to cleanup file {file_path}: {cleanup_error}")
            
            if database_record:
                try:
                    self.orchestrator.delete(database_record['id'])
                    self.logger.info(f"Cleaned up database record on error: {database_record['id']}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to cleanup database record: {cleanup_error}")
            raise

    # GET BY ID
    async def get_script_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id)
        return self._simplify_workflow_item(response_from_db)

    # UPDATE WITH FILE OPERATIONS (Atomic file-database updates)
    async def update_script_record(self, record_id: str, request: ScriptUpdateRequest) -> Dict[str, Any]:
        """Update script record and file atomically - content changes require both to succeed"""
        original_content = None
        file_backup_created = False
        
        try:
            # Get current script to check file path
            current_script = await self._get_record(record_id)
            
            # Prepare update data
            update_data = request.to_dict()
            
            # If content is being updated, handle file operations atomically
            content_updated = False
            if update_data.get('content') is not None:
                new_content = update_data['content']
                file_path = current_script.get('file_path')
                
                if file_path and os.path.exists(file_path):
                    # Backup original content for rollback
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            original_content = f.read()
                        file_backup_created = True
                    except Exception as backup_error:
                        self.logger.warning(f"Failed to backup original content: {backup_error}")
                    
                    # Update physical file first
                    file_updated, file_error = self._update_physical_file(file_path, new_content)
                    if not file_updated:
                        raise DatabaseError(f"Failed to update physical file: {file_error}")
                    
                    content_updated = True
                
                # Update file size if content changed
                update_data['file_size'] = len(new_content.encode('utf-8'))
            
            # Update database record
            try:
                response_from_db = await self._update_record(record_id, **update_data)
            except Exception as db_error:
                # Rollback file changes if database update fails
                if content_updated and original_content is not None and file_backup_created:
                    try:
                        file_path = current_script.get('file_path')
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                        self.logger.info(f"Rolled back file content due to database update failure")
                    except Exception as rollback_error:
                        self.logger.error(f"Failed to rollback file content: {rollback_error}")
                raise db_error
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Script update successful",
                'file_operations': {
                    'physical_file_updated': content_updated,
                    'file_path': response_from_db.get('file_path'),
                    'file_size': response_from_db.get('file_size'),
                    'checksum': response_from_db.get('checksum')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update script {record_id}: {str(e)}")
            raise

    # DELETE WITH FILE CLEANUP (Database first, then file cleanup)
    async def delete_script_record(self, record_id: str) -> Dict[str, Any]:
        """Delete script with atomic file-database management"""
        backup_content = None
        file_backup_created = False
        
        try:
            # Get script before deletion for file path
            current_script = await self._get_record(record_id)
            file_path = current_script.get('file_path')
            
            # Backup file content for potential rollback
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        backup_content = f.read()
                    file_backup_created = True
                except Exception as backup_error:
                    self.logger.warning(f"Failed to backup file content: {backup_error}")
            
            # Step 1: Delete from database first
            response_from_db = await self._delete_record(record_id)
            
            # Step 2: Delete physical file
            file_existed, physical_file_deleted, file_error = self._delete_physical_file(file_path)
            
            # If file deletion fails after database deletion, log warning but don't rollback
            # (Database deletion should be permanent for consistency)
            warnings = []
            if file_existed and not physical_file_deleted:
                warnings.append(f"Physical file could not be removed: {file_error}")
                self.logger.warning(f"Database record deleted but physical file remains: {file_path}")
            elif not file_existed and file_path:
                warnings.append("Physical file did not exist on filesystem")
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "Script deletion successful",
                'file_operations': {
                    'physical_file_deleted': physical_file_deleted,
                    'file_path': file_path,
                    'file_size': current_script.get('file_size'),
                    'checksum': current_script.get('checksum'),
                    'warnings': warnings if warnings else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete script {record_id}: {str(e)}")
            # If database deletion failed but we have file backup, we could restore
            # but typically database deletion failure means record still exists
            raise

    # LIST ALL
    async def list_script_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)

        simplified_items = [
            self._simplify_workflow_item(item)
            for item in response_from_db.get('items', [])
        ]

        return {
            'items': simplified_items,
            'total': response_from_db.get('total', 0),
            'skip': response_from_db.get('skip', skip),
            'limit': response_from_db.get('limit', limit)
        }

    # COUNT
    async def count_script_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_script_records(self, request: ScriptFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)

        simplified_items = [
            self._simplify_workflow_item(item)
            for item in response_from_db.get('items', [])
        ]

        return {
            'items': simplified_items,
            'total': response_from_db.get('total', 0),
            'skip': response_from_db.get('skip', request.skip),
            'limit': response_from_db.get('limit', request.limit)
        }
