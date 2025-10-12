import uuid
from typing import cast, Iterable, Any
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean, Enum, UniqueConstraint, CheckConstraint, event, ForeignKeyConstraint

from .enums import *

# SQLAlchemy declarative base for all models
Base = declarative_base()


class BaseModel(Base):
    """Abstract base model with common functionality for all entities"""
    __abstract__ = True
    __allow_unmapped__ = True

    @classmethod
    def _generate_id(cls):
        """Generate unique ID with class-specific prefix"""
        prefix = getattr(cls, '__prefix__', 'XX')  # Get class prefix (e.g., 'WF' for Workflow)
        uuid_suffix = str(uuid.uuid4()).replace('-', '')[:17].upper()  # 17-char UUID suffix
        return f"{prefix}-{uuid_suffix}"

    # Primary key with auto-generated ID
    id = Column(String(20), primary_key=True)

    # Timestamps with automatic updates
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Audit Trail - Track who created/updated records
    created_by = Column(String(20), nullable=True)
    updated_by = Column(String(20), nullable=True)

    # Soft Delete - Mark records as deleted without removing them
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(20), nullable=True)

    # Optimistic Locking - Prevent concurrent modification conflicts
    version_number = Column(Integer, default=1, nullable=False)

    def __init__(self, **kwargs):
        """Initialize the model with auto-generated ID if not provided"""
        # Auto-generate ID if not provided (uses class-specific prefix)
        if 'id' not in kwargs or kwargs['id'] is None:
            kwargs['id'] = self._generate_id()
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """Return string representation of the model instance"""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self, include_relationships=False, exclude_fields=None, include_properties=False) -> dict:
        """Convert model instance to dictionary representation"""
        result = {}
        exclude_fields = exclude_fields or []

        # Process table columns - cast() helps type checker understand SQLAlchemy collections
        columns = cast(Iterable[Any], self.__table__.c)
        for column in columns:
            field_name = column.name
            if field_name in exclude_fields:
                continue

            try:
                # Get column value and serialize it
                value = getattr(self, field_name)
                result[field_name] = BaseModel._serialize_value(value)
            except (AttributeError, TypeError, ValueError):
                # Skip problematic fields silently
                continue

        # Process relationships if requested
        if include_relationships:
            for relationship_name in self.__mapper__.relationships.keys():
                if relationship_name in exclude_fields:
                    continue

                try:
                    # Get relationship value and serialize it
                    relationship_value = getattr(self, relationship_name)
                    result[relationship_name] = BaseModel._serialize_relationship(relationship_value)
                except (AttributeError, TypeError, ValueError):
                    # Skip problematic relationships silently
                    continue

        # Process @property attributes if requested
        if include_properties:
            for name in dir(self.__class__):
                # Skip private attributes
                if name.startswith('_'):
                    continue

                if name in exclude_fields:
                    continue

                # Check if it's a property and serialize it
                attr = getattr(self.__class__, name, None)
                if isinstance(attr, property):
                    try:
                        value = getattr(self, name)
                        result[name] = BaseModel._serialize_value(value)
                    except (AttributeError, TypeError, ValueError):
                        # Skip problematic properties silently
                        continue

        return result

    @staticmethod
    def _serialize_value(value):
        """Serialize individual values to JSON-safe format"""
        if value is None:
            return None
        elif isinstance(value, datetime):
            # Convert datetime to ISO format string
            return value.isoformat()
        elif isinstance(value, enum.Enum):
            # Convert enum to its value
            return value.value
        elif isinstance(value, (int, float, str, bool, list, dict)):
            # Already JSON-safe types
            return value
        else:
            try:
                # Try to convert to string as fallback
                return str(value)
            except (TypeError, ValueError):
                # Return None if conversion fails
                return None

    @staticmethod
    def _serialize_relationship(relationship_value):
        """Serialize relationship values safely (collections or single objects)"""
        if relationship_value is None:
            return None
        elif hasattr(relationship_value, '__iter__') and not isinstance(relationship_value, (str, dict, bytes)):
            # Handle collections (lists, sets, etc.) - avoid infinite recursion
            return [
                item.to_dict(include_relationships=False) if hasattr(item, 'to_dict') else str(item)
                for item in relationship_value
            ]
        else:
            # Handle single objects - avoid infinite recursion
            return (
                relationship_value.to_dict(include_relationships=False)
                if hasattr(relationship_value, 'to_dict')
                else str(relationship_value)
            )


class EnvironmentVariable(BaseModel):
    """Environment variables for workflow execution"""
    __prefix__ = "EV"
    __tablename__ = 'environment_variables'

    # Basic information
    name = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Type and scope classification
    variable_type = Column(Enum(VariableType), default=VariableType.STRING, nullable=False, index=True)
    scope = Column(Enum(VariableScope), default=VariableScope.GLOBAL, nullable=False, index=True)

    # Security - Encryption flag for sensitive values
    is_encrypted = Column(Boolean, default=False, nullable=False)

    # Relationships - Role-based access control
    user_roles = relationship("UserEnvarRole", back_populates="environment_variable", cascade="all, delete-orphan")


class FileUpload(BaseModel):
    """File upload management with security scanning"""
    __prefix__ = "FU"
    __tablename__ = 'file_uploads'
    __table_args__ = (
        CheckConstraint('file_size > 0', name='_positive_file_size'),
        CheckConstraint('file_size <= 104857600', name='_max_file_size_100mb'),  # 100MB limit
    )

    # Basic file information
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_extension = Column(String(20), nullable=False)
    file_path = Column(Text, unique=True, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)
    is_temporary = Column(Boolean, default=False, nullable=False)

    # Relationships - Role-based access control
    user_roles = relationship("UserFileRole", back_populates="file_upload", cascade="all, delete-orphan")


class Script(BaseModel):
    """Executable scripts with versioning, testing, and performance tracking"""
    __prefix__ = "SC"
    __tablename__ = 'scripts'

    # Basic information
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Organization - Category and subcategory for grouping
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True, index=True)

    # File information - Script storage and metadata
    file_extension = Column(String(10), nullable=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    script_metadata = Column(JSON, nullable=True)

    # Environment - Required Python packages
    required_packages = Column(JSON, default=lambda: [], nullable=False)

    # Schema definitions - Input/output validation
    input_schema = Column(JSON, default=lambda: {}, nullable=False)
    output_schema = Column(JSON, default=lambda: {}, nullable=False)
    test_input_params = Column(JSON, default=lambda: {}, nullable=False)
    test_output_params = Column(JSON, default=lambda: {}, nullable=False)

    # Testing and quality assurance
    test_status = Column(Enum(ScriptTestStatus), default=ScriptTestStatus.UNTESTED, nullable=False, index=True)
    test_coverage = Column(Float, nullable=True)
    last_test_run_at = Column(DateTime, nullable=True, index=True)
    test_results = Column(JSON, default=lambda: {}, nullable=False)
    is_dangerous = Column(Boolean, default=False, nullable=False)

    # Performance metrics - Execution statistics
    avg_execution_time = Column(Float, nullable=True)
    min_execution_time = Column(Float, nullable=True)
    max_execution_time = Column(Float, nullable=True)
    total_executions = Column(Integer, default=0, nullable=False)

    # Security and approval workflow
    is_approved = Column(Boolean, default=False, nullable=False, index=True)
    approved_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Metadata and documentation
    tags = Column(JSON, default=lambda: [], nullable=True)
    documentation_url = Column(String(500), nullable=True)

    # Relationships
    nodes = relationship("Node", back_populates="script")
    approver = relationship("User", foreign_keys="[Script.approved_by]", back_populates="approved_scripts")


class Workflow(BaseModel):
    """Workflow definition and execution management"""
    __prefix__ = "WF"
    __tablename__ = 'workflows'

    # Basic workflow information
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=1, nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False, index=True)
    status_message = Column(Text, nullable=True, default='Currently no error context is available')

    # Ownership and access control
    is_public = Column(Boolean, default=False, nullable=False)

    # Execution statistics - Performance tracking
    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    cancelled_executions = Column(Integer, default=0, nullable=False)

    # Performance metrics - Duration tracking
    avg_execution_duration = Column(Float, nullable=True)
    min_execution_duration = Column(Float, nullable=True)
    max_execution_duration = Column(Float, nullable=True)

    # Execution timestamps - Last execution tracking
    last_executed_at = Column(DateTime, nullable=True, index=True)
    last_successful_execution_at = Column(DateTime, nullable=True)
    last_failed_execution_at = Column(DateTime, nullable=True)

    # Relationships
    nodes = relationship("Node", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
    trigger_assignments = relationship("WorkflowTrigger", back_populates="workflow", cascade="all, delete-orphan")
    user_roles = relationship("UserWorkflowRole", back_populates="workflow", cascade="all, delete-orphan")
    execution_inputs = relationship("ExecutionInput", back_populates="workflow", cascade="all, delete-orphan")
    execution_outputs = relationship("ExecutionOutput", back_populates="workflow", cascade="all, delete-orphan")


class Node(BaseModel):
    """Workflow nodes representing executable steps"""
    __prefix__ = "ND"
    __tablename__ = 'nodes'
    __table_args__ = (
        UniqueConstraint('workflow_id', 'name', name='_workflow_node_name_unique'),
        CheckConstraint('max_retries >= 0', name='_non_negative_retries'),
        CheckConstraint('timeout_seconds > 0', name='_positive_timeout'),
    )

    # Relationships - Parent workflow and associated script
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    script_id = Column(String(20), ForeignKey('scripts.id', ondelete='RESTRICT'), nullable=True)

    # Node configuration
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    input_params = Column(JSON, nullable=True, default=lambda: {})
    output_params = Column(JSON, nullable=True, default=lambda: {})
    meta_data = Column(JSON, default=lambda: {}, nullable=True)
    
    # Execution settings - Retry and timeout configuration
    max_retries = Column(Integer, default=3, nullable=False)
    timeout_seconds = Column(Integer, default=300, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")
    script = relationship("Script", back_populates="nodes")
    outgoing_edges = relationship("Edge", foreign_keys="[Edge.from_node_id]", back_populates="from_node", cascade="all, delete-orphan")
    incoming_edges = relationship("Edge", foreign_keys="[Edge.to_node_id]", back_populates="to_node", cascade="all, delete-orphan")
    execution_inputs = relationship("ExecutionInput", back_populates="node")
    execution_outputs = relationship("ExecutionOutput", back_populates="node")


class Edge(BaseModel):
    """Workflow edges defining node connections and execution flow"""
    __prefix__ = "ED"
    __tablename__ = 'edges'
    __table_args__ = (
        CheckConstraint('from_node_id != to_node_id', name='_edge_no_self_loop'),  
        UniqueConstraint('workflow_id', 'from_node_id', 'to_node_id', 'condition_type', name='_workflow_edge_unique'),
    )

    # Relationships - Parent workflow and connected nodes
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    from_node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)
    to_node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)

    # Edge configuration - Conditional execution
    condition_type = Column(Enum(ConditionType), default=ConditionType.SUCCESS, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")
    from_node = relationship("Node", foreign_keys="[Edge.from_node_id]", back_populates="outgoing_edges")
    to_node = relationship("Node", foreign_keys="[Edge.to_node_id]", back_populates="incoming_edges")


class Execution(BaseModel):
    """Workflow execution instances with comprehensive tracking"""
    __prefix__ = "EX"
    __tablename__ = 'executions'

    # Relationships - Parent workflow and trigger
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    trigger_id = Column(String(20), ForeignKey('triggers.id', ondelete='SET NULL'), nullable=True)

    # Execution status and timing
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)

    # Node execution tracking - Progress monitoring
    pending_nodes = Column(Integer, default=0, nullable=False)
    running_nodes = Column(Integer, default=0, nullable=False)
    executed_nodes = Column(Integer, default=0, nullable=False)

    # Execution data - Input and output
    trigger_data = Column(JSON, default=lambda: {}, nullable=False)
    results = Column(JSON, default=lambda: {}, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    trigger = relationship("Trigger", back_populates="executions")
    execution_inputs = relationship("ExecutionInput", back_populates="execution", cascade="all, delete-orphan")
    execution_outputs = relationship("ExecutionOutput", back_populates="execution", cascade="all, delete-orphan")
    user_roles = relationship("UserExecutionRole", back_populates="execution", cascade="all, delete-orphan")


class ExecutionInput(BaseModel):
    """Node execution input parameters and scheduling"""
    __prefix__ = "EI"
    __tablename__ = 'execution_inputs'

    # Relationships - Parent execution and workflow
    execution_id = Column(String(20), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    node_id = Column(String(20), ForeignKey('nodes.id', ondelete='SET NULL'), nullable=True)  # Nullable for SET NULL on delete

    # Scheduling parameters - Execution order and priority
    dependency_count = Column(Integer, default=0, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    wait_factor = Column(Integer, default=0, nullable=False)

    # Node execution data - Parameters and script information
    node_name = Column(String(100), nullable=False)
    node_params = Column(JSON, default=lambda: {}, nullable=False)
    script_name = Column(String(100), nullable=False)
    script_path = Column(Text, nullable=False)

    # Relationships
    execution = relationship("Execution", back_populates="execution_inputs")
    workflow = relationship("Workflow", back_populates="execution_inputs")
    node = relationship("Node", back_populates="execution_inputs")


class ExecutionOutput(BaseModel):
    """Node execution results and performance tracking"""
    __prefix__ = "EO"
    __tablename__ = 'execution_outputs'

    # Relationships - Parent execution and workflow
    execution_id = Column(String(20), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    node_id = Column(String(20), ForeignKey('nodes.id', ondelete='SET NULL'), nullable=True)

    # Execution results - Status and output data
    status = Column(Enum(ExecutionOutputStatus), nullable=False, index=True)
    result_data = Column(JSON, nullable=True, default=lambda: {})

    # Performance tracking - Timing and duration
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    execution = relationship("Execution", back_populates="execution_outputs")
    workflow = relationship("Workflow", back_populates="execution_outputs")
    node = relationship("Node", back_populates="execution_outputs")


class Trigger(BaseModel):
    """Reusable triggers for automated workflow execution"""
    __prefix__ = "TR"
    __tablename__ = 'triggers'
    
    # Trigger configuration - Basic information
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    trigger_type = Column(Enum(TriggerType), nullable=False, index=True)
    config = Column(JSON, default=lambda: {}, nullable=False)
    input_mapping = Column(JSON, default=lambda: {}, nullable=True)

    # Status and scheduling - Execution control
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    last_triggered_at = Column(DateTime, nullable=True, index=True)
    trigger_count = Column(Integer, default=0, nullable=False)

    # Relationships
    workflow_assignments = relationship("WorkflowTrigger", back_populates="trigger", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="trigger")


class WorkflowTrigger(BaseModel):
    """Junction table for Trigger-Workflow many-to-many relationship"""
    __prefix__ = "WT"
    __tablename__ = 'workflow_triggers'
    __table_args__ = (
        UniqueConstraint('trigger_id', 'workflow_id', name='_trigger_workflow_unique'),
    )

    # Relationships
    trigger_id = Column(String(20), ForeignKey('triggers.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    trigger = relationship("Trigger", back_populates="workflow_assignments")
    workflow = relationship("Workflow", back_populates="trigger_assignments")


class User(BaseModel):
    """User accounts with authentication and access control"""
    __prefix__ = "US"
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('username', name='_user_username_unique'),
        UniqueConstraint('email', name='_user_email_unique'),
        CheckConstraint('length(username) >= 3', name='_username_min_length'),
        CheckConstraint('length(username) <= 50', name='_username_max_length'),
    )

    # Basic user information
    username = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=True)
    surname = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    country_code = Column(String(2), nullable=True)
    phone_number = Column(String(20), nullable=True)
    plan = Column(Enum(Plans), default=Plans.FREE, nullable=False, index=True)

    # Account status - User state management
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)

    # Security - Authentication and access control
    last_login_at = Column(DateTime, nullable=True, index=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    password_changed_at = Column(DateTime, nullable=True)

    # Verification - Email and password reset
    email_verified_at = Column(DateTime, nullable=True)
    verification_token = Column(String(100), nullable=True)
    reset_token = Column(String(100), nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

    # Relationships
    approved_scripts = relationship("Script", foreign_keys="[Script.approved_by]", back_populates="approver")
    workflow_roles = relationship("UserWorkflowRole", foreign_keys="[UserWorkflowRole.user_id]", back_populates="user", cascade="all, delete-orphan")
    envar_roles = relationship("UserEnvarRole", foreign_keys="[UserEnvarRole.user_id]", back_populates="user", cascade="all, delete-orphan")
    file_roles = relationship("UserFileRole", foreign_keys="[UserFileRole.user_id]", back_populates="user", cascade="all, delete-orphan")
    execution_roles = relationship("UserExecutionRole", foreign_keys="[UserExecutionRole.user_id]", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", foreign_keys="[ApiKey.user_id]", back_populates="user", cascade="all, delete-orphan")
    auth_sessions = relationship("AuthSession", foreign_keys="[AuthSession.user_id]", back_populates="user", cascade="all, delete-orphan")


class Permission(BaseModel):
    """System permissions for role-based access control"""
    __prefix__ = "PM"
    __tablename__ = 'permissions'

    # Permission definition - Access control rules
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    endpoint = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=True)
    required_role = Column(Enum(Roles), nullable=False, index=True)
    required_plan = Column(Enum(Plans), nullable=False)


class BaseRoleAssignmentModel(BaseModel):
    """Abstract base for user-to-entity role assignments (junction tables)."""
    __abstract__ = True
    __allow_unmapped__ = True

    # Common role assignment fields
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(Enum(Roles), nullable=False, index=True)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    granted_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    # Generic target record id; concrete subclasses bind this to a specific table via FK constraint
    record_id = Column(String(20), nullable=False, index=True)


class UserWorkflowRole(BaseRoleAssignmentModel):
    """User roles for workflow access control"""
    __prefix__ = "UW"
    __tablename__ = 'user_workflow_roles'

    __table_args__ = (
        ForeignKeyConstraint(['record_id'], ['workflows.id'], ondelete='CASCADE'),
    )
    # Relationships - User and workflow

    # Relationships
    user = relationship("User", foreign_keys="[UserWorkflowRole.user_id]", back_populates="workflow_roles")
    workflow = relationship("Workflow", back_populates="user_roles", foreign_keys="[UserWorkflowRole.record_id]")


class UserEnvarRole(BaseRoleAssignmentModel):
    """User roles for environment variable access control"""
    __prefix__ = "UE"
    __tablename__ = 'user_envar_roles'

    __table_args__ = (
        ForeignKeyConstraint(['record_id'], ['environment_variables.id'], ondelete='CASCADE'),
    )
    # Relationships - User and environment variable

    # Relationships
    user = relationship("User", foreign_keys="[UserEnvarRole.user_id]", back_populates="envar_roles")
    environment_variable = relationship("EnvironmentVariable", back_populates="user_roles", foreign_keys="[UserEnvarRole.record_id]")
    

class UserFileRole(BaseRoleAssignmentModel):
    """User roles for file upload access control"""
    __prefix__ = "UF"
    __tablename__ = 'user_file_roles'

    __table_args__ = (
        ForeignKeyConstraint(['record_id'], ['file_uploads.id'], ondelete='CASCADE'),
    )
    # Relationships - User and file upload

    # Relationships
    user = relationship("User", foreign_keys="[UserFileRole.user_id]", back_populates="file_roles")
    file_upload = relationship("FileUpload", back_populates="user_roles", foreign_keys="[UserFileRole.record_id]")
    

class UserExecutionRole(BaseRoleAssignmentModel):
    """User roles for execution access control"""
    __prefix__ = "UX"
    __tablename__ = 'user_execution_roles'

    __table_args__ = (
        ForeignKeyConstraint(['record_id'], ['executions.id'], ondelete='CASCADE'),
    )
    # Relationships - User and execution

    # Relationships
    user = relationship("User", foreign_keys="[UserExecutionRole.user_id]", back_populates="execution_roles")
    execution = relationship("Execution", back_populates="user_roles", foreign_keys="[UserExecutionRole.record_id]")


class ApiKey(BaseModel):
    """API keys for programmatic access with rate limiting and scope control"""
    __prefix__ = "AK"
    __tablename__ = 'api_keys'

    # Relationships - Owner user
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Key information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String(20), nullable=False)  # First few characters for identification
    
    # Access control - Permissions and scopes
    scopes = Column(JSON, default=lambda: [], nullable=False)  # List of allowed scopes/permissions
    allowed_ips = Column(JSON, default=lambda: [], nullable=False)  # IP whitelist (empty = all IPs)
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Expiration - Time-based access control
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Usage tracking - Statistics and monitoring
    last_used_at = Column(DateTime, nullable=True, index=True)
    last_used_ip = Column(String(45), nullable=True)  # IPv6 max length
    total_requests = Column(Integer, default=0, nullable=False)
    
    # Rate limiting - Request throttling
    rate_limit_per_hour = Column(Integer, nullable=True)  # Requests per hour limit
    rate_limit_per_day = Column(Integer, nullable=True)  # Requests per day limit
    current_hour_requests = Column(Integer, default=0, nullable=False)
    current_day_requests = Column(Integer, default=0, nullable=False)
    rate_limit_reset_at = Column(DateTime, nullable=True)
    
    # Metadata
    user_agent = Column(String(500), nullable=True)  # Last used user agent

    # Relationships
    user = relationship("User", foreign_keys="[ApiKey.user_id]", back_populates="api_keys")


class AuthSession(BaseModel):
    """Authentication sessions holding both access and refresh tokens as a pair"""
    __prefix__ = "AS"
    __tablename__ = 'auth_sessions'
    __table_args__ = (
        UniqueConstraint('access_token_jti', name='_access_token_jti_unique'),
        UniqueConstraint('refresh_token_jti', name='_refresh_token_jti_unique'),
    )

    # Relationships - Owner user
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Access Token - Short-lived token for API access
    access_token_jti = Column(String(100), nullable=False, unique=True, index=True)
    access_token_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    access_token_expires_at = Column(DateTime, nullable=False, index=True)
    access_token_last_used_at = Column(DateTime, nullable=True)
    
    # Refresh Token - Long-lived token for obtaining new access tokens
    refresh_token_jti = Column(String(100), nullable=False, unique=True, index=True)
    refresh_token_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    refresh_token_expires_at = Column(DateTime, nullable=False, index=True)
    refresh_token_last_used_at = Column(DateTime, nullable=True)

    # Revocation - Session invalidation
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Session tracking - Device and location information
    device_name = Column(String(100), nullable=True)  # e.g., 'iPhone 13', 'Chrome on Windows'
    device_type = Column(String(50), nullable=True)  # 'mobile', 'desktop', 'tablet', 'api'
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length

    # Geographic information
    country = Column(String(2), nullable=True)  # ISO country code
    city = Column(String(100), nullable=True)
    
    # Usage statistics
    total_requests = Column(Integer, default=0, nullable=False)
    last_activity_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys="[AuthSession.user_id]", back_populates="auth_sessions")


# Event listeners for optimistic locking
@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):  # pylint: disable=unused-argument
    """Increment version number on update for optimistic locking"""
    # mapper and connection are required by SQLAlchemy event listener signature
    _ = mapper, connection  # Mark as intentionally unused
    # Increment version for optimistic locking (prevents concurrent modification conflicts)
    target.version_number += 1