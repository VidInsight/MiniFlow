"""
Base BFF Actions

Abstract base class for all BFF action classes providing common CRUD operations
and standardized error handling, logging, and response formatting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import (ErrorContext, ErrorSeverity, DatabaseError, ValidationError, ResourceNotFound, OrchestrationError)

# Generic type for orchestrator
T = TypeVar('T')


class BaseBFFOperations(ABC, Generic[T]):
    """
    Abstract base class for BFF Actions providing common operations.
    
    This class implements the common CRUD operations that are shared across
    all BFF action classes:
    - CREATE
    - GET
    - UPDATE
    - DELETE
    - GET ALL
    - COUNT
    - FILTER  
    
    Each concrete action class should inherit from this and implement the
    abstract methods to provide entity-specific behavior.
    """

    def __init__(self, orchestrator: T, entity_name: str, logger_name: str = "miniflow_api"):
        self.orchestrator = orchestrator
        self.entity_name = entity_name
        self.logger = get_logger(logger_name)

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """
        Daha iyi hata takibi için hata bağlamı (context) oluşturur

        Argümanlar:
            operation: Gerçekleştirilen işlem
            **kwargs: Ek bağlam bilgileri

        Dönüş değeri:
            ErrorContext: Hata bağlamı nesnesi

        """
        return ErrorContext(operation=operation, component=self.__class__.__name__, additional_info=kwargs)

    # CAPABILITY FLAGS - Override in subclasses to control available operations
    @property
    def supports_create(self) -> bool:
        """Whether this entity supports CREATE operations"""
        return True
    
    @property 
    def supports_update(self) -> bool:
        """Whether this entity supports UPDATE operations"""
        return True
    
    @property
    def supports_delete(self) -> bool:
        """Whether this entity supports DELETE operations"""
        return True
    
    @property
    def supports_filter(self) -> bool:
        """Whether this entity supports FILTER operations"""
        return True
    
    def _validate_operation_support(self, operation: str, capability_flag: bool):
        """
        İşlemin desteklenip desteklenmediğini kontrol et ve desteklenmiyorsa hata fırlat

        Argümanlar:
            operation: İşlemin adı (örneğin, "oluştur", "güncelle")
            capability_flag: İşlemin desteklenip desteklenmediğini belirten Boole değeri

        Hatalar:
            ValidationError: İşlem desteklenmiyorsa
        """
        if not capability_flag:
            context = self._create_error_context("unsupported_operation", requested_operation=operation)
            raise ValidationError(f"{operation.title()} operation is not supported for {self.entity_name}", context=context, severity=ErrorSeverity.MEDIUM)
    
    # TEMEL CRUD OPERASYONLARI
    async def _create_record(self, **kwargs) -> Dict[str, Any]:
        """
        Doğrulanmış verilerle yeni bir kayıt oluşturur

        Argümanlar:
            **kwargs: pydantic istek modelinden gelen doğrulanmış veriler

        Dönüş değeri:
            Dict: Oluşturulan varlık verileri

        Hatalar:
            ValidationError: Doğrulama başarısız olursa veya işlem desteklenmiyorsa
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        # CREATE operasyonu destekleniyor mu kontrol et
        self._validate_operation_support("create", self.supports_create)

        try:
            operation = f"create_{self.entity_name}_record"
            self.logger.info(f"Creating {self.entity_name} record")

            # Orchestrator katmanı üzerinden kaydı oluştur
            record = self.orchestrator.create(**kwargs)

            self.logger.info(f"Successfully created {self.entity_name} record")
            return record
        except (OrchestrationError, ValidationError):
            raise
        except Exception as e:
            context = self._create_error_context(operation, **kwargs)
            self.logger.error(f"Failed to create {self.entity_name}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.entity_name}: {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)
    
    async def _get_record(self, entity_id: str) -> Dict[str, Any]:
        """
        Kimliğe göre tek bir kayıt alır
        
        Argümanlar:
            entity_id: Varlığın kimliği
            
        Dönüş değeri:
            Dict: Varlık verileri
            
        Hatalar:
            ResourceNotFound: Varlık bulunamazsa
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        try:
            self.logger.info(f"Getting {self.entity_name} record: {entity_id}")
            
            # Get entity via orchestrator
            record = self.orchestrator.get_by_id(entity_id)
            if not record:
                context = self._create_error_context("get_record_by_id", entity_id=entity_id)
                raise ResourceNotFound(f"{self.entity_name.title()} '{entity_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)
            
            return record
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_record_by_id", entity_id=entity_id)
            self.logger.error(f"Failed to get {self.entity_name} '{entity_id}': {str(e)}")
            raise DatabaseError(f"Failed to retrieve {self.entity_name} '{entity_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)

    async def _update_record(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        """
         Doğrulanmış verilerle kaydı günceller
        
        Argümanlar:
            entity_id: Güncellenecek varlığın kimliği
            **kwargs: pydantic istek modelinden gelen doğrulanmış veriler
            
        Dönüş değeri:
            Dict: Güncellenen varlık verileri
            
        Hatalar:
            ResourceNotFound: Varlık bulunamazsa
            ValidationError: Doğrulama başarısız olursa veya işlem desteklenmiyorsa
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        # UPDATE operasyonu destekleniyor mu kontrol et
        self._validate_operation_support("update", self.supports_update)

        try:
            operation = f"update_{self.entity_name}_record"
            self.logger.info(f"Updating {self.entity_name}: {entity_id}")
            
            # Filter out None values to avoid updating with None
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            
            if not update_data:
                context = self._create_error_context(operation, entity_id=entity_id)
                raise ValidationError("No update data provided", context=context, severity=ErrorSeverity.MEDIUM)

         # Update entity via orchestrator
            updated_record = self.orchestrator.update(entity_id, **update_data)
            
            self.logger.info(f"Successfully updated {self.entity_name}: {entity_id}")
            return updated_record
            
        except (OrchestrationError, ValidationError, ResourceNotFound):
            raise
        except Exception as e:
            context = self._create_error_context(operation, entity_id=entity_id, **kwargs)
            self.logger.error(f"Failed to update {self.entity_name} '{entity_id}': {str(e)}")
            raise DatabaseError(f"Failed to update {self.entity_name} '{entity_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)    

    async def _delete_record(self, entity_id: str) -> Dict[str, Any]:
        """
        Kimliğe göre kaydı siler
        
        Argümanlar:
            entity_id: Silinecek varlığın kimliği
            
        Dönüş değeri:
            Dict: Silme yanıtı
            
        Hatalar:
            ResourceNotFound: Varlık bulunamazsa
            ValidationError: İşlem desteklenmiyorsa
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        try:
            operation = f"delete_{self.entity_name}_record"
            self.logger.info(f"Deleting {self.entity_name}: {entity_id}")
            
            # Delete the entity
            deleted_result = self.orchestrator.delete(entity_id)         
            return deleted_result
            
        except (ResourceNotFound, ValidationError):
            raise
        except Exception as e:
            context = self._create_error_context(operation, entity_id=entity_id)
            self.logger.error(f"Failed to delete {self.entity_name} '{entity_id}': {str(e)}")
            raise DatabaseError(f"Failed to delete {self.entity_name} '{entity_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)

    async def _get_all_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sayfalama ile tüm kayıtları getirir
        
        Argümanlar:
            skip: Atlanacak kayıt sayısı
            limit: Döndürülecek maksimum kayıt sayısı
            order_by: Sıralama yapılacak alan
            include_relationships: İlişkili varlıkların dahil edilip edilmeyeceği
            exclude_fields: Yanıttan hariç tutulacak alanlar
            
        Dönüş değeri:
            Dict: Sayfalanmış varlık listesi
            
        Hatalar:
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        try:
            operation = f"get_all_{self.entity_name}_records"
            self.logger.info(f"Getting all {self.entity_name} records (skip={skip}, limit={limit})")
            
            # Get entities via orchestrator
            items = self.orchestrator.get_all(skip, limit, order_by, include_relationships, exclude_fields)
            total = self.orchestrator.count()
            
            self.logger.info(f"Retrieved {len(items)} {self.entity_name} records")
            
            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except (OrchestrationError, ValidationError):
            raise
        except Exception as e:
            context = self._create_error_context(operation, skip=skip, limit=limit)
            self.logger.error(f"Failed to get {self.entity_name} records: {str(e)}")
            raise DatabaseError(f"Failed to retrieve {self.entity_name} records: {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)

    async def _count_records(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
         İsteğe bağlı filtrelerle kayıtları sayar
        
        Argümanlar:
            filters: Uygulanacak isteğe bağlı filtreler
            
        Dönüş değeri:
            int: Kayıt sayısı
            
        Hatalar:
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        try:
            operation = f"count_{self.entity_name}_records"
            self.logger.info(f"Counting {self.entity_name} records" + (f" with filters" if filters else ""))
            
            if filters:
                count = self.orchestrator.count_with_filter(filters)
            else:
                count = self.orchestrator.count()
            
            self.logger.info(f"Found {count} {self.entity_name} records")
            return count
            
        except (OrchestrationError, ValidationError):
            raise
        except Exception as e:
            context = self._create_error_context(operation, filters=filters)
            self.logger.error(f"Failed to count {self.entity_name} records: {str(e)}")
            raise DatabaseError(f"Failed to count {self.entity_name} records: {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)
        
    async def _filter_records(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100, order_by_field: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Gelişmiş filtreleme ile kayıtları filtreler

        Argümanlar:
            filters: Uygulanacak filtreler
            skip: Atlanacak kayıt sayısı
            limit: Döndürülecek maksimum kayıt sayısı
            order_by_field: Sıralama yapılacak alan
            include_relationships: İlişkili varlıkların dahil edilip edilmeyeceği
            exclude_fields: Yanıttan hariç tutulacak alanlar

        Dönüş değeri:
            Dict: Filtrelenmiş ve sayfalanmış varlık listesi

        Hatalar:
            ValidationError: İşlem desteklenmiyorsa
            DatabaseError: Veritabanı işlemi başarısız olursa
        """
        # Check if FILTER is supported
        self._validate_operation_support("filter", self.supports_filter)

        try:
            operation = f"filter_{self.entity_name}_records"
            self.logger.info(f"Filtering {self.entity_name} records with {len(filters)} filters")
            
            # Get filtered entities
            items = self.orchestrator.filter(filters, skip, limit, order_by_field, include_relationships, exclude_fields)
            total = self.orchestrator.count_with_filter(filters)
            
            self.logger.info(f"Found {len(items)} filtered {self.entity_name} records")
            
            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "filters_applied": filters
            }
            
        except (OrchestrationError, ValidationError):
            raise
        except Exception as e:
            context = self._create_error_context(operation, filters=filters)
            self.logger.error(f"Failed to filter {self.entity_name} records: {str(e)}")
            raise DatabaseError(f"Failed to filter {self.entity_name} records: {str(e)}", context=context, severity=ErrorSeverity.HIGH,source_error=e)