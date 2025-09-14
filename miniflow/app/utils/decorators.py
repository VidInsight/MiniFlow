"""
API Error Handling Decorator

Bu modül API endpoint'leri için unified exception handling ve logging
yapısını sağlayan decorator içerir. MiniFlow naming convention'ına uygun
olarak 'with_' prefix kullanır.
"""
import functools
from typing import Callable, Any, Optional

from fastapi import HTTPException

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import (
    MiniflowException, ValidationError, ResourceNotFound, 
    DatabaseError, OrchestrationError
)


def with_api_error_handling(
    func: Callable = None,
    *,
    operation: Optional[str] = None,
    logger_name: Optional[str] = None,
    success_message: Optional[str] = None,
    log_start: bool = True,
    log_success: bool = True
):
    """
    Advanced API error handling and logging decorator.
    
    Bu decorator:
    1. Endpoint başlangıcında log kaydı tutar (opsiyonel)
    2. Başarılı işlemlerde success log yazar (opsiyonel)
    3. Tüm yaygın exception'ları yakalar ve uygun HTTP status code'ları döner
    4. Automatic correlation ID tracking yapar
    5. Tutarlı error response formatı sağlar
    6. Hem parametresiz hem parametreli kullanım destekler
    
    Args:
        operation: İşlem adı (logging context için). Default: fonksiyon adı
        logger_name: Özel logger adı. Default: modül adından türetilir
        success_message: Başarı durumunda özel log mesajı. Default: genel mesaj
        log_start: İşlem başlangıcını logla. Default: True
        log_success: Başarılı işlemleri logla. Default: True
    
    Usage:
        # Basit kullanım (parametresiz)
        @with_api_error_handling
        async def get_workflow(workflow_id, actions, correlation_id):
            result = await actions.get_workflow_record(workflow_id)
            return APIResponse(data=result, correlation_id=correlation_id)
            
        # Gelişmiş kullanım (parametreli)
        @with_api_error_handling(
            operation="create_workflow",
            success_message="Workflow başarıyla oluşturuldu",
            log_start=True
        )
        async def create_workflow(request, actions, correlation_id):
            result = await actions.create_workflow(request)
            return APIResponse(data=result, correlation_id=correlation_id)
            
        # Orta seviye kullanım
        @with_api_error_handling(operation="delete_workflow")
        async def delete_workflow(workflow_id, actions, correlation_id):
            result = await actions.delete_workflow(workflow_id)
            return APIResponse(data=result, correlation_id=correlation_id)
    """
    def decorator(fn: Callable) -> Callable:
        # Logger adını belirle - ya verilen ad ya da fonksiyon modül adı
        actual_logger_name = logger_name or fn.__module__.split('.')[-1]
        logger = get_logger(actual_logger_name)
        op_name = operation or fn.__name__
        
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            # Get correlation_id from kwargs (FastAPI dependency injection)
            correlation_id = kwargs.get('correlation_id', 'unknown')
            
            try:
                # İşlem başlangıcını logla (opsiyonel)
                if log_start and logger:
                    logger.info(f"[{correlation_id}] Starting {op_name}")
                
                # Endpoint fonksiyonunu çalıştır
                result = await fn(*args, **kwargs)
                
                # Başarı durumunu logla (opsiyonel)
                if log_success and logger:
                    if success_message:
                        logger.info(f"[{correlation_id}] {success_message}")
                    else:
                        logger.info(f"[{correlation_id}] {op_name} completed successfully")
                
                # If result is APIResponse, convert to dict for FastAPI
                if hasattr(result, 'model_dump'):
                    return result.model_dump()
                elif hasattr(result, 'dict'):
                    return result.dict()
                else:
                    return result
                
            except ResourceNotFound as e:
                if logger:
                    logger.warning(f"[{correlation_id}] Resource not found in {op_name}: {str(e)}")
                raise HTTPException(status_code=404, detail=str(e))
                
            except ValidationError as e:
                if logger:
                    logger.error(f"[{correlation_id}] Validation error in {op_name}: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
                
            except DatabaseError as e:
                if logger:
                    logger.error(f"[{correlation_id}] Database error in {op_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
                
            except OrchestrationError as e:
                if logger:
                    logger.error(f"[{correlation_id}] Orchestration error in {op_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
                
            except MiniflowException as e:
                # Genel MiniflowException handler
                if logger:
                    logger.error(f"[{correlation_id}] MiniFlow error in {op_name}: {str(e)}")
                raise HTTPException(status_code=e.status_code, detail=str(e))
                
            except Exception as e:
                # Beklenmeyen exception'lar
                if logger:
                    logger.error(f"[{correlation_id}] Unexpected error in {op_name}: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        return wrapper
    
    # Decorator'ın hem @with_api_error_handling hem de @with_api_error_handling() şeklinde kullanımını destekle
    if func is None:
        return decorator
    else:
        return decorator(func)
