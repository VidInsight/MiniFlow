# Logger Usage Examples

## Basic Usage

### 1. Simple Logging

```python
from miniflow.core.logger import get_logger

# Get logger instance
logger = get_logger("my_service")

# Basic logging
logger.info("Service started successfully")
logger.warning("Configuration file not found, using defaults")
logger.error("Database connection failed")
logger.critical("System is shutting down")
```

### 2. Structured Logging with Context

```python
logger = get_logger("user_service")

# Log with extra context
logger.info(
    "User login successful",
    extra={
        "user_id": "12345",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "login_method": "oauth"
    }
)

# Log with correlation ID
from miniflow.core.logger.context import set_correlation_id

set_correlation_id("req-2023-001")

logger.info("Processing user request")
# Correlation ID automatically included
```

### 3. Error Logging with Exception Details
```python
logger = get_logger("payment_service")

try:
    process_payment(amount, card_info)
except PaymentException as e:
    logger.error(
        "Payment processing failed",
        extra={
            "error_code": e.code,
            "amount": amount,
            "transaction_id": e.transaction_id,
            "error_details": str(e)
        },
        exc_info=True  # Include stack trace
    )
except Exception as e:
    logger.critical(
        "Unexpected error in payment processing",
        extra={
            "amount": amount,
            "error_type": type(e).__name__
        },
        exc_info=True
    )
```

## Advanced Usage

### 4. Custom Logger Configuration

```python
from miniflow.core import get_logger_registry
from miniflow import ModuleLoggerConfig

# Create custom configuration
config = ModuleLoggerConfig(
    module_name="analytics_service",
    level="DEBUG",
    filename="logs/analytics.log",
    max_size_mb=500,  # Large log files for analytics
    max_files=10,
    console_output=True,
    console_level="WARNING",
    file_formatter="json",
    console_formatter="plain",
    enabled=True,
    tags={"service", "analytics", "data-processing"},
    custom_fields={
        "service_version": "1.2.3",
        "environment": "production",
        "datacenter": "us-east-1"
    }
)

# Register configuration
registry = get_logger_registry()
registry.register_module_config(config)

# Use configured logger
logger = get_logger("analytics_service")
logger.debug("Starting data analysis pipeline")
```

### 5. Performance-Critical Logging
```python
logger = get_logger("high_frequency_trading")

# High-frequency logging with minimal overhead
def process_trade(trade_data):
    # Quick level check before expensive operations
    if logger.isEnabledFor("DEBUG"):
        logger.debug(
            "Processing trade",
            extra={
                "symbol": trade_data.symbol,
                "quantity": trade_data.quantity,
                "price": trade_data.price,
                "timestamp": trade_data.timestamp.isoformat()
            }
        )
    
    # Process trade...
    
    # Always log critical events
    logger.info(
        "Trade executed",
        extra={
            "trade_id": trade_data.id,
            "symbol": trade_data.symbol,
            "pnl": calculate_pnl(trade_data)
        }
    )
```

### 6. Multi-Handler Configuration

```python
from miniflow.core.logger.handlers import ConsoleHandler, RotatingFileHandler
from miniflow.core.logger.formatters import JSONFormatter, PlainTextFormatter
from miniflow.core import LogLevel

# Create custom logger with multiple handlers
logger_name = "custom_service"
logger = get_logger(logger_name)

# Console handler for development
console_handler = ConsoleHandler()
console_handler.set_level(LogLevel.WARNING)
console_handler.set_formatter(PlainTextFormatter())

# File handler for production logs
file_handler = RotatingFileHandler(
    filename="logs/service.log",
    max_size_bytes=100 * 1024 * 1024,  # 100MB
    backup_count=5
)
file_handler.set_level(LogLevel.INFO)
file_handler.set_formatter(JSONFormatter())

# Add handlers
logger.add_handler(console_handler)
logger.add_handler(file_handler)

# Use logger
logger.info("Service configuration completed")
```

## FastAPI Integration

### 7. Request/Response Logging Middleware

```python
from fastapi import FastAPI, Request
from miniflow.core.logger import get_logger
from miniflow.core.logger.context import set_correlation_id
import uuid
import time

app = FastAPI()
logger = get_logger("api")


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)

    # Log request
    start_time = time.time()
    logger.info(
        "API Request",
        extra={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host
        }
    )

    # Process request
    try:
        response = await call_next(request)

        # Log successful response
        process_time = time.time() - start_time
        logger.info(
            "API Response",
            extra={
                "status_code": response.status_code,
                "process_time": process_time
            }
        )

        return response

    except Exception as e:
        # Log error response
        process_time = time.time() - start_time
        logger.error(
            "API Error",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "process_time": process_time
            },
            exc_info=True
        )
        raise
```

### 8. Endpoint-Specific Logging

```python
from fastapi import APIRouter, HTTPException
from miniflow.core.logger import get_logger

router = APIRouter()
logger = get_logger("user_api")


@router.post("/users/")
async def create_user(user_data: UserCreate):
    logger.info(
        "Creating new user",
        extra={
            "email": user_data.email,
            "role": user_data.role
        }
    )

    try:
        user = await user_service.create_user(user_data)

        logger.info(
            "User created successfully",
            extra={
                "user_id": user.id,
                "email": user.email
            }
        )

        return user

    except UserExistsException:
        logger.warning(
            "User creation failed - user already exists",
            extra={"email": user_data.email}
        )
        raise HTTPException(status_code=409, detail="User already exists")

    except Exception as e:
        logger.error(
            "User creation failed with unexpected error",
            extra={
                "email": user_data.email,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Business Logic Integration

### 9. Service Layer Logging

```python
from miniflow.core.logger import get_logger


class PaymentService:
    def __init__(self):
        self.logger = get_logger("payment_service")

    async def process_payment(self, payment_request):
        self.logger.info(
            "Payment processing started",
            extra={
                "amount": payment_request.amount,
                "currency": payment_request.currency,
                "payment_method": payment_request.method
            }
        )

        # Validate payment
        validation_result = await self._validate_payment(payment_request)
        if not validation_result.is_valid:
            self.logger.warning(
                "Payment validation failed",
                extra={
                    "validation_errors": validation_result.errors,
                    "amount": payment_request.amount
                }
            )
            raise PaymentValidationException(validation_result.errors)

        # Process with payment provider
        try:
            payment_result = await self._charge_payment(payment_request)

            self.logger.info(
                "Payment processed successfully",
                extra={
                    "payment_id": payment_result.id,
                    "amount": payment_request.amount,
                    "provider_reference": payment_result.provider_reference
                }
            )

            return payment_result

        except PaymentProviderException as e:
            self.logger.error(
                "Payment provider error",
                extra={
                    "provider": e.provider,
                    "error_code": e.code,
                    "amount": payment_request.amount
                }
            )
            raise
```

### 10. Database Operations Logging

```python
from miniflow.core.logger import get_logger


class UserRepository:
    def __init__(self):
        self.logger = get_logger("user_repository")

    async def find_user_by_email(self, email: str):
        self.logger.debug(
            "Searching user by email",
            extra={"email": email}
        )

        start_time = time.time()
        try:
            user = await self.db.users.find_one({"email": email})
            query_time = time.time() - start_time

            if user:
                self.logger.debug(
                    "User found",
                    extra={
                        "user_id": str(user["_id"]),
                        "email": email,
                        "query_time": query_time
                    }
                )
            else:
                self.logger.debug(
                    "User not found",
                    extra={
                        "email": email,
                        "query_time": query_time
                    }
                )

            return user

        except Exception as e:
            query_time = time.time() - start_time
            self.logger.error(
                "Database query failed",
                extra={
                    "email": email,
                    "query_time": query_time,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
```

## Testing and Development

### 11. Testing with Mock Loggers

```python
import pytest
from unittest.mock import Mock, patch
from miniflow.core.logger import get_logger


class TestUserService:
    @patch('miniflow.core.logger.get_logger')
    def test_user_creation_logging(self, mock_get_logger):
        # Setup mock logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Test service
        service = UserService()
        user_data = UserCreate(email="test@example.com", name="Test User")

        # Execute
        result = service.create_user(user_data)

        # Verify logging calls
        mock_logger.info.assert_called_with(
            "User created successfully",
            extra={
                "user_id": result.id,
                "email": "test@example.com"
            }
        )
```

### 12. Development Debug Logging

```python
from miniflow.core.logger import get_logger
from miniflow.core import LogLevel

# Development logger with debug output
logger = get_logger("development")

# Temporarily set debug level for development
logger.set_level(LogLevel.DEBUG)


def debug_user_workflow(user_id):
    logger.debug("Starting user workflow debug", extra={"user_id": user_id})

    # Step-by-step debugging
    user = get_user(user_id)
    logger.debug("User retrieved", extra={"user": user.to_dict()})

    permissions = get_user_permissions(user_id)
    logger.debug("Permissions loaded", extra={"permissions": permissions})

    profile = build_user_profile(user, permissions)
    logger.debug("Profile built", extra={"profile_size": len(profile)})

    logger.debug("User workflow completed", extra={"user_id": user_id})
    return profile
```

## Production Scenarios

### 13. High-Volume Logging

```python
from miniflow.core.logger import get_logger
import asyncio

logger = get_logger("batch_processor")


async def process_batch_data(batch_data):
    batch_id = batch_data.id
    total_records = len(batch_data.records)

    logger.info(
        "Batch processing started",
        extra={
            "batch_id": batch_id,
            "total_records": total_records
        }
    )

    processed = 0
    errors = 0

    for record in batch_data.records:
        try:
            await process_record(record)
            processed += 1

            # Log progress every 1000 records
            if processed % 1000 == 0:
                logger.info(
                    "Batch processing progress",
                    extra={
                        "batch_id": batch_id,
                        "processed": processed,
                        "total": total_records,
                        "progress_pct": (processed / total_records) * 100
                    }
                )

        except Exception as e:
            errors += 1
            # Log error but continue processing
            logger.error(
                "Record processing failed",
                extra={
                    "batch_id": batch_id,
                    "record_id": record.id,
                    "error": str(e)
                }
            )

    logger.info(
        "Batch processing completed",
        extra={
            "batch_id": batch_id,
            "total_records": total_records,
            "processed": processed,
            "errors": errors,
            "success_rate": (processed / total_records) * 100
        }
    )
```

### 14. Security Event Logging

```python
from miniflow.core.logger import get_logger

security_logger = get_logger("security")


class SecurityService:
    def log_login_attempt(self, user_email, ip_address, success, failure_reason=None):
        if success:
            security_logger.info(
                "Successful login",
                extra={
                    "event_type": "login_success",
                    "user_email": user_email,
                    "ip_address": ip_address,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            security_logger.warning(
                "Failed login attempt",
                extra={
                    "event_type": "login_failure",
                    "user_email": user_email,
                    "ip_address": ip_address,
                    "failure_reason": failure_reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    def log_permission_violation(self, user_id, requested_resource, permission_required):
        security_logger.critical(
            "Permission violation detected",
            extra={
                "event_type": "permission_violation",
                "user_id": user_id,
                "requested_resource": requested_resource,
                "permission_required": permission_required,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

## Configuration Examples

### 15. Environment-Specific Configuration

```python
# config/logging.py
from miniflow import ModuleLoggerConfig
import os


def get_logging_config():
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        return ModuleLoggerConfig(
            module_name="app",
            level="INFO",
            filename="logs/app.log",
            max_size_mb=1000,
            max_files=20,
            console_output=False,  # No console in production
            file_formatter="json",
            custom_fields={
                "environment": "production",
                "service_name": "miniflow-api"
            }
        )

    elif environment == "staging":
        return ModuleLoggerConfig(
            module_name="app",
            level="DEBUG",
            filename="logs/app-staging.log",
            max_size_mb=500,
            max_files=10,
            console_output=True,
            console_level="WARNING",
            file_formatter="json",
            console_formatter="plain"
        )

    else:  # development
        return ModuleLoggerConfig(
            module_name="app",
            level="DEBUG",
            console_output=True,
            console_level="DEBUG",
            console_formatter="plain",
            file_formatter="json"
        )
```

These examples demonstrate the flexibility and power of the MiniFlow logger system, from simple basic usage to complex production scenarios. The logger is designed to scale from development to high-volume production environments while maintaining consistency and reliability.
