import uuid
import enum
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean, Enum, UniqueConstraint


class WorkflowStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"

class ScriptType(str, enum.Enum):
    PYTHON = "PY"
    BASH = "SH"

class ScriptTestStatus(str, enum.Enum):
    UNTESTED = "UNTESTED"
    PASSED = "PASSED"
    FAILED = "FAILED"

class CredentialType(str, enum.Enum):
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BASIC_AUTH = "BASIC_AUTH"
    TOKEN = "TOKEN"
    CERTIFICATE = "CERTIFICATE"

class CredentialProvider(str, enum.Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    SLACK = "SLACK"
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    AWS = "AWS"
    AZURE = "AZURE"
    CUSTOM = "CUSTOM"

class ValidationStatus(str, enum.Enum):
    UNTESTED = "UNTESTED"
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    ERROR = "ERROR"

class ConditionType(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ALWAYS = "ALWAYS"
    CONDITIONAL = "CONDITIONAL"

class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ExecutionOutputStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELED"

class ArchiveReason(str, enum.Enum):
    AUTO_CLEANUP = "AUTO CLEANUP"
    MANUAL_ARCHIVE = "MANUEL ARCHIVE"
    RETENTION_POLICY = "RETENTION POLICY"
    SYSTEM_CLEANUP = "SYSTEM CLEANUP"

class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    ARCHIVE = "ARCHIVE"

class VariableScope(str, enum.Enum):
    GLOBAL = "global"
    WORKFLOW = "workflow"
    TRIGGER = "trigger"
    USER = "user"
    NODE = "node"

class VariableType(str, enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    SECRET = "secret"
    CREDENTIAL = "credential"
    FILE_PATH = "file_path"
    URL = "url"

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    @classmethod
    def _generate_id(cls):
        prefix = getattr(cls, '__prefix__', 'XX')
        uuid_suffix = str(uuid.uuid4()).replace('-', '')[:17].upper()
        return f"{prefix}-{uuid_suffix}"

    id = Column(String(20), primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, **kwargs):
        """Initialize the model with auto-generated ID if not provided"""
        if 'id' not in kwargs or kwargs['id'] is None:
            kwargs['id'] = self._generate_id()
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        result = {}

        for column in self.__table__.columns:
            value = getattr(self, column.name)

            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            elif hasattr(value, 'to_dict'):
                value = value.to_dict()

            result[column.name] = value

        return result

class EnvironmentVariable(BaseModel):
    __prefix__ = "EV"
    __tablename__ = 'environment_variables'

    # Temel bilgiler
    name = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Tip ve kapsam
    variable_type = Column(Enum(VariableType), default=VariableType.STRING, nullable=False, index=True)
    scope = Column(Enum(VariableScope), default=VariableScope.GLOBAL, nullable=False, index=True)

    # Metadata
    last_accessed_at = Column(DateTime, nullable=True, index=True)
    access_count = Column(Integer, default=0, nullable=False)
    last_modified_by = Column(String(20), nullable=True)

class FileUpload(BaseModel):
    __prefix__ = "FU"
    __tablename__ = 'file_uploads'

    # Temel bilgiler
    name = Column(String(255),unique=True, nullable=False, index=True)  # file_name.file_extension format
    filename = Column(String(255), nullable=False)  # Base filename without extension
    file_extension = Column(String(20), nullable=True)  # File extension (.pdf, .txt, etc.)
    file_path = Column(Text, unique=True, nullable=False)  # Absolute path to file
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)
    # uploaded_by = Column(String(20), ForeignKey('users.id'), nullable=True)
    is_temporary = Column(Boolean, default=True)

class Script(BaseModel):
    __prefix__ = "SC"
    __tablename__ = 'scripts'

    # Temel bilgiler
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0", nullable=False)
    language = Column(Enum(ScriptType), nullable=False, index=True)
    
    # Category information  
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True, index=True)
    
    # File information
    file_extension = Column(String(10), nullable=True)  # .py, .sh, .js, etc.
    file_path = Column(Text, nullable=True)  # scripts/category/subcategory/filename.ext
    file_size = Column(Integer, nullable=True)  # File size in bytes
    content = Column(String, nullable=True) 
    
    # Environment
    required_packages = Column(JSON, default=list, nullable=False)  # ["requests==2.28.0"]

    # Input/Output tanımları
    input_schema = Column(JSON, default=dict, nullable=False)  # JSON Schema
    output_schema = Column(JSON, default=dict, nullable=False)  # JSON Schema
    test_input_params = Column(JSON, default=dict, nullable=False)  # Backward compatibility
    test_output_params = Column(JSON, default=dict, nullable=False)  # Backward compatibility

    # Test ve kalite
    test_status = Column(Enum(ScriptTestStatus), default=ScriptTestStatus.UNTESTED, nullable=False, index=True)
    test_coverage = Column(Integer, nullable=True)  # Yüzde olarak
    last_test_run_at = Column(DateTime, nullable=True, index=True)
    test_results = Column(JSON, default=dict, nullable=False)

    # Performans metrikleri
    avg_execution_time = Column(Float, nullable=True)
    min_execution_time = Column(Float, nullable=True)
    max_execution_time = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)  # 0.0 - 1.0
    total_executions = Column(Integer, default=0, nullable=False)

    # Metadata
    tags = Column(JSON, default=list, nullable=False)  # ["email", "pdf", "urgent"]
    author = Column(String(100), nullable=True)
    documentation_url = Column(String(500), nullable=True)