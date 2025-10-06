from typing import Dict, Any, List, Optional

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class UserOrchestrator(BaseOrchestrator):
    """
    User orchestrator for user account management.
    
    Provides:
    - User CRUD operations
    - Account activation/deactivation
    - Account locking/unlocking
    - Security features
    """

    def _get_primary_crud(self):
        return self.user_crud

    @with_orchestration_errors('create_user')
    @with_session
    def create(self, session, *, created_by: str = None, **kwargs) -> Dict[str, Any]:
        """
        Yeni kullanıcı oluşturur.
        
        Kullanım Amacı:
            - User registration: Yeni kullanıcı kaydı
            - Admin user creation: Admin tarafından kullanıcı oluşturma
            - System user setup: Sistem kullanıcıları
        
        Args:
            username: Kullanıcı adı (unique, 3-50 karakter)
            hashed_password: Hash'lenmiş şifre
            email: (Optional) Email adresi (unique)
            first_name: (Optional) Ad
            last_name: (Optional) Soyad
            **kwargs: Diğer user fields
        
        Returns:
            Dict: Oluşturulan user kaydı
        
        Example:
            >>> user = user_orch.create(
            ...     username="john_doe",
            ...     hashed_password="$2b$12$...",
            ...     email="john@example.com"
            ... )
        """
        # created_by optional for self-registration (user creates themselves)
        # For admin-created users, pass admin's user_id
        if created_by:
            created_by = self._validate_user_exist(session, created_by)
        
        user = self.user_crud._create(
            session,
            created_by=created_by,
            **kwargs
        )
        return self._serialize_single_result(user)

    @with_orchestration_errors('update_user')
    @with_session
    def update(self, session, *, record_id: str, updated_by: str, **kwargs) -> Dict[str, Any]:
        """
        Kullanıcı bilgilerini günceller.
        
        Note: hashed_password ve güvenlik alanları protected'dır.
        """
        record_id = self._validate_user_exist(session, record_id)
        updated_by = self._validate_user_exist(session, updated_by)
        
        result = self.user_crud._update(
            session,
            record_id,
            updated_by=updated_by,
            **kwargs
        )
        return self._serialize_single_result(result)

    @with_orchestration_errors('activate_user')
    @with_session
    def activate(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcı hesabını aktif eder.
        
        Kullanım Amacı:
            - Email verification: Email doğrulama sonrası aktivasyon
            - Admin approval: Admin onayı sonrası
            - Account reactivation: Deaktif hesabı tekrar aktif etme
        
        Example:
            >>> user_orch.activate(user_id="USR_123")
        """
        self._validate_user_exist(session, user_id)
        
        result = self.user_crud._activate(session, user_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('deactivate_user')
    @with_session
    def deactivate(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcı hesabını deaktif eder.
        
        Kullanım Amacı:
            - Temporary suspension: Geçici hesap askıya alma
            - User request: Kullanıcı isteği ile
            - Security measure: Güvenlik tedbiri
        
        Example:
            >>> user_orch.deactivate(user_id="USR_123")
        """
        self._validate_user_exist(session, user_id)
        
        result = self.user_crud._deactivate(session, user_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('lock_user_account')
    @with_session
    def lock_account(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcı hesabını kilitler.
        
        Kullanım Amacı:
            - Failed login attempts: Çok fazla başarısız giriş
            - Security breach: Güvenlik ihlali şüphesi
            - Admin action: Admin kararı
        
        Example:
            >>> user_orch.lock_account(user_id="USR_123")
        """
        self._validate_user_exist(session, user_id)
        
        result = self.user_crud._lock_account(session, user_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('unlock_user_account')
    @with_session
    def unlock_account(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kilitli kullanıcı hesabını açar.
        
        Kullanım Amacı:
            - Password reset: Şifre sıfırlama sonrası
            - Admin unlock: Admin tarafından kilidi açma
            - Security clearance: Güvenlik kontrolü sonrası
        
        Example:
            >>> user_orch.unlock_account(user_id="USR_123")
        """
        self._validate_user_exist(session, user_id)
        
        result = self.user_crud._unlock_account(session, user_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_user_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, requesting_user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get user by ID - Only own profile.
        Users can only access their own user record for privacy.
        """
        record_id = self._validate_user_exist(session, record_id)
        requesting_user_id = self._validate_user_exist(session, requesting_user_id)
        
        # Users can only view their own profile
        if record_id != requesting_user_id:
            self._raise_permission_denied('access', requesting_user_id, record_id, 'user')
        
        result = self.user_crud._get_by_id(
            session,
            record_id,
            include_relationships=include_relationships
        )
        
        return self._serialize_single_result(
            result,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_users')
    @with_session
    def get_all(self, session, *, user_id: str, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all users - Only own record.
        Users can only access their own user data.
        Returns a list with single item (own profile).
        """
        user_id = self._validate_user_exist(session, user_id)
        
        from sqlalchemy import select
        
        # Only return the requesting user's own record
        query = select(self.user_crud.model).where(
            self.user_crud.model.id == user_id
        )
        
        if not include_deleted:
            query = query.where(self.user_crud.model.is_deleted == False)
        
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results,
            include_relationships=False,
            exclude_fields=exclude_fields
        )

