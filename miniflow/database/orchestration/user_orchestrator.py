from typing import Dict, Any

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
    def create(self, session, **kwargs) -> Dict[str, Any]:
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
        user = self.user_crud._create(session, **kwargs)
        return self._serialize_single_result(user)

    @with_orchestration_errors('update_user')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        """
        Kullanıcı bilgilerini günceller.
        
        Note: hashed_password ve güvenlik alanları protected'dır.
        """
        result = self.user_crud._update(session, record_id, **kwargs)
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

