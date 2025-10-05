import enum

class WorkflowStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"

class ScriptStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ScriptTestStatus(str, enum.Enum):
    UNTESTED = "UNTESTED"
    PASSED = "PASSED"
    FAILED = "FAILED"

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
    CANCELLED = "CANCELLED"

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
    FILE_PATH = "FILE_PATH"
    URL = "URL"

class TriggerType(str, enum.Enum):
    API = "API"
    SCHEDULED = "SCHEDULED"
    WEBHOOK = "WEBHOOK"

class Roles(str, enum.Enum):
    OWNER = "OWNER"
    VIEWER = "VIEWER"
    CONTRIBUTOR = "CONTRIBUTOR"
    EDITOR = "EDITOR"

class Plans(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"