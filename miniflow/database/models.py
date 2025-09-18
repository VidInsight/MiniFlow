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


class ScriptTestStatus(str, enum.Enum):
    UNTESTED = "UNTESTED"
    PASSED = "PASSED"
    FAILED = "FAILED"


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
    CANCELLED = "CANCELLED"  # Tutarlılık için düzeltildi


class ArchiveReason(str, enum.Enum):
    AUTO_CLEANUP = "AUTO CLEANUP"
    MANUAL_ARCHIVE = "MANUAL ARCHIVE"  # "MANUEL" -> "MANUAL" düzeltildi
    RETENTION_POLICY = "RETENTION POLICY"
    SYSTEM_CLEANUP = "SYSTEM CLEANUP"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    ARCHIVE = "ARCHIVE"


class VariableScope(str, enum.Enum):
    GLOBAL = "GLOBAL"
    WORKFLOW = "WORKFLOW"
    TRIGGER = "TRIGGER"
    USER = "USER"
    NODE = "NODE"


class VariableType(str, enum.Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    SECRET = "SECRET"
    CREDENTIAL = "CREDENTIAL"
    FILE_PATH = "FILE_PATH"
    URL = "URL"


class TriggerType(str, enum.Enum):
    MANUAL = "MANUAL"           # Manuel tetikleme
    SCHEDULED = "SCHEDULED"     # Zaman bazlı (cron/interval)
    WEBHOOK = "WEBHOOK"         # HTTP webhook endpoint


class TriggerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"           # Çalışıyor
    INACTIVE = "INACTIVE"       # Durdurulmuş
    ERROR = "ERROR"             # Hata durumunda


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

    def to_dict(self, include_relationships=False, exclude_fields=None) -> dict:

        result = {}
        exclude_fields = exclude_fields or []

        # Process table columns
        for column in self.__table__.columns:
            field_name = column.name
            if field_name in exclude_fields:
                continue

            try:
                value = getattr(self, field_name)
                result[field_name] = self._serialize_value(value)
            except Exception:
                # Skip problematic fields silently
                continue

        # Process relationships if requested
        if include_relationships:
            for relationship_name in self.__mapper__.relationships.keys():
                if relationship_name in exclude_fields:
                    continue

                try:
                    relationship_value = getattr(self, relationship_name)
                    result[relationship_name] = self._serialize_relationship(relationship_value)
                except Exception:
                    # Skip problematic relationships
                    continue

        return result

    def _serialize_value(self, value):
        """Serialize individual values"""
        if value is None:
            return None
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, enum.Enum):
            return value.value
        elif isinstance(value, (int, float, str, bool, list, dict)):
            return value
        else:
            # Try to convert to string for unknown types
            try:
                return str(value)
            except Exception:
                return None

    def _serialize_relationship(self, relationship_value):
        """Serialize relationship values safely"""
        if relationship_value is None:
            return None
        elif hasattr(relationship_value, '__iter__') and not isinstance(relationship_value, (str, dict)):
            # Collection relationship (one-to-many, many-to-many)
            return [
                item.to_dict(include_relationships=False) if hasattr(item, 'to_dict') else str(item)
                for item in relationship_value
            ]
        else:
            # Single relationship (one-to-one, many-to-one)
            return (
                relationship_value.to_dict(include_relationships=False)
                if hasattr(relationship_value, 'to_dict')
                else str(relationship_value)
            )


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


class FileUpload(BaseModel):
    __prefix__ = "FU"
    __tablename__ = 'file_uploads'

    # Temel bilgiler
    name = Column(String(255), unique=True, nullable=False, index=True)  # file_name.file_extension format
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
    test_coverage = Column(Float, nullable=True)  # Yüzde olarak
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

    # Relationships
    nodes = relationship("Node", back_populates="script")


class Workflow(BaseModel):
    __prefix__ = "WF"
    __tablename__ = 'workflows'

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=0, nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False)
    status_message = Column(Text, nullable=True, default='Currently no error context is avaliable')

    # Workflow Statistics
    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    cancelled_executions = Column(Integer, default=0, nullable=False)
    avg_execution_duration = Column(Float, nullable=True)  # seconds
    min_execution_duration = Column(Float, nullable=True)  # seconds
    max_execution_duration = Column(Float, nullable=True)  # seconds
    last_executed_at = Column(DateTime, nullable=True, index=True)
    last_successful_execution_at = Column(DateTime, nullable=True)
    last_failed_execution_at = Column(DateTime, nullable=True)
    
    # Computed properties available as methods
    @property
    def success_rate(self) -> float:
        """Calculate workflow success rate"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    @property
    def failure_rate(self) -> float:
        """Calculate workflow failure rate"""
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions

    # Relationships
    nodes = relationship("Node", back_populates="workflow")
    edges = relationship("Edge", back_populates="workflow")
    executions = relationship("Execution", back_populates="workflow")
    triggers = relationship("Trigger", back_populates="workflow", cascade="all, delete-orphan")


class Node(BaseModel):
    __prefix__ = "ND"
    __tablename__ = 'nodes'

    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    script_id = Column(String(20), ForeignKey('scripts.id', ondelete='SET NULL'), nullable=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    params = Column(JSON, nullable=True, default=dict)
    meta_data = Column(JSON, default=dict, nullable=True)
    max_retries = Column(Integer, default=3, nullable=False)
    timeout_seconds = Column(Integer, default=300, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")
    script = relationship("Script", back_populates="nodes")

    # Edge relationships
    outgoing_edges = relationship("Edge", foreign_keys="Edge.from_node_id", back_populates="from_node")
    incoming_edges = relationship("Edge", foreign_keys="Edge.to_node_id", back_populates="to_node")

    # Execution relationships
    execution_inputs = relationship("ExecutionInput", back_populates="node")
    execution_outputs = relationship("ExecutionOutput", back_populates="node")


class Edge(BaseModel):
    __prefix__ = "ED"
    __tablename__ = 'edges'

    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    from_node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)
    to_node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)

    condition_type = Column(Enum(ConditionType), default=ConditionType.SUCCESS, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")
    from_node = relationship("Node", foreign_keys=[from_node_id], back_populates="outgoing_edges")
    to_node = relationship("Node", foreign_keys=[to_node_id], back_populates="incoming_edges")


class Execution(BaseModel):
    __prefix__ = "EX"
    __tablename__ = 'executions'

    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)

    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    pending_nodes = Column(Integer, default=0, nullable=False)
    executed_nodes = Column(Integer, default=0, nullable=False)
    results = Column(JSON, default=dict, nullable=False)
    error_details = Column(JSON, default=dict, nullable=False)  # Detailed error information
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    # Computed properties for execution analytics
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds"""
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0.0
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is in a completed state"""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully"""
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def node_success_rate(self) -> float:
        """Calculate success rate of nodes within this execution"""
        total_attempted = self.executed_nodes
        if total_attempted == 0:
            return 0.0
        return self.successful_nodes / total_attempted
    
    @property
    def total_nodes(self) -> int:
        """Total number of nodes in this execution"""
        return self.pending_nodes + self.executed_nodes
    
    @property
    def progress_percentage(self) -> float:
        """Calculate execution progress as percentage"""
        total = self.total_nodes
        if total == 0:
            return 0.0
        return (self.executed_nodes / total) * 100.0

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    execution_inputs = relationship("ExecutionInput", back_populates="execution", cascade="all, delete-orphan")
    execution_outputs = relationship("ExecutionOutput", back_populates="execution", cascade="all, delete-orphan")


class ExecutionInput(BaseModel):
    __prefix__ = "EI"
    __tablename__ = 'execution_inputs'

    execution_id = Column(String(20), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)
    trigger_id = Column(String(20), ForeignKey('triggers.id', ondelete='SET NULL'), nullable=True, index=True)
    correlation_id = Column(String(50), nullable=True)

    priority = Column(Integer, default=0, nullable=False)
    dependency_count = Column(Integer, default=0, nullable=False)
    wait_factor = Column(Integer, default=0, nullable=False)

    # Denormalized fields for performance (scheduler optimization)
    node_name = Column(String(100), nullable=False)
    script_name = Column(String(100), nullable=True)
    script_path = Column(Text, nullable=True)
    node_params = Column(JSON, default=dict, nullable=False)

    # Relationships
    execution = relationship("Execution", back_populates="execution_inputs")
    workflow = relationship("Workflow")
    node = relationship("Node", back_populates="execution_inputs")
    trigger = relationship("Trigger", back_populates="execution_inputs")


class ExecutionOutput(BaseModel):
    __prefix__ = "EO"
    __tablename__ = 'execution_outputs'

    execution_id = Column(String(20), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)
    correlation_id = Column(String(50), nullable=True)

    status = Column(Enum(ExecutionOutputStatus), nullable=False)
    result_data = Column(JSON, nullable=True, default=dict)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    execution = relationship("Execution", back_populates="execution_outputs")
    workflow = relationship("Workflow")
    node = relationship("Node", back_populates="execution_outputs")


class Trigger(BaseModel):
    __prefix__ = "TR"
    __tablename__ = 'triggers'

    # ==========================================
    # TEMEL BİLGİLER
    # ==========================================
    
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    # Hangi workflow'u tetikleyecek - CASCADE: workflow silinince trigger'lar da silinir
    
    name = Column(String(100), nullable=False)
    # Trigger'ın kullanıcı dostu ismi
    
    description = Column(Text, nullable=True)
    # Trigger'ın ne yaptığının açıklaması (isteğe bağlı)
    
    trigger_type = Column(Enum(TriggerType), nullable=False, index=True)
    # MANUAL, SCHEDULED, WEBHOOK - sık filtrelenecek
    
    status = Column(Enum(TriggerStatus), default=TriggerStatus.ACTIVE, nullable=False, index=True)
    # ACTIVE, INACTIVE, ERROR - aktif trigger'lar sık sorgulanacak
    
    # ==========================================
    # KONFIGÜRASYON
    # ==========================================
    
    config = Column(JSON, default=dict, nullable=False)
    # Trigger tipine göre özel ayarlar:
    # MANUAL: {}
    # SCHEDULED: {"cron": "0 9 * * *", "timezone": "UTC"}
    # WEBHOOK: {"webhook_id": "payment-hook", "secret": "..."}
    
    input_mapping = Column(JSON, default=dict, nullable=True)
    # Basit key-value mapping:
    # {"order_id": "id", "customer_email": "email", "priority": "high"}
    # null ise raw data direkt geçer
    
    # ==========================================
    # CONSTRAINTS
    # ==========================================
    
    __table_args__ = (
        # Aynı workflow'da aynı isimde trigger olamaz
        UniqueConstraint('workflow_id', 'name', name='_workflow_trigger_name_unique'),
    )
    
    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    
    workflow = relationship("Workflow", back_populates="triggers")
    execution_inputs = relationship("ExecutionInput", back_populates="trigger")
    
    # ==========================================
    # COMPUTED PROPERTIES
    # ==========================================
    
    @property
    def webhook_endpoint(self) -> str:
        """Webhook endpoint URL'i (webhook trigger'lar için)"""
        if self.trigger_type != TriggerType.WEBHOOK:
            return None
        
        webhook_id = self.config.get('webhook_id')
        if webhook_id:
            return f"/api/bff/triggers/webhook/{webhook_id}"
        return None
    
    @property
    def is_active(self) -> bool:
        """Trigger aktif mi?"""
        return self.status == TriggerStatus.ACTIVE