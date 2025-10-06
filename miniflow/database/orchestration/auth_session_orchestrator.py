from typing import Dict, Any, List, Optional

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class AuthSessionOrchestrator(BaseOrchestrator):
    """
    Authentication Session orchestrator for JWT session management.
    
    Provides:
    - Session CRUD operations
    - Token validation
    - Token refresh/rotation
    - Session revocation
    - Multi-device session management
    """

    def _get_primary_crud(self):
        return self.auth_session_crud

    @with_orchestration_errors('create_auth_session')
    @with_session
    def create(self, session, *, user_id: str, created_by: str, **kwargs) -> Dict[str, Any]:
        """
        Yeni authentication session oluşturur.
        
        Kullanım Amacı:
            - User login: Kullanıcı girişi
            - Token generation: JWT token üretimi
            - Session tracking: Oturum takibi
        
        Args:
            user_id: Kullanıcı ID
            access_token_jti: Access token JTI (JWT ID)
            access_token_expires_at: Access token süre sonu
            refresh_token_jti: Refresh token JTI
            refresh_token_expires_at: Refresh token süre sonu
            ip_address: (Optional) IP adresi
            user_agent: (Optional) Browser/device bilgisi
        
        Example:
            >>> session = auth_session_orch.create(
            ...     user_id="USR_123",
            ...     access_token_jti="jti_abc123",
            ...     access_token_expires_at=datetime.now() + timedelta(hours=1),
            ...     refresh_token_jti="jti_xyz789",
            ...     refresh_token_expires_at=datetime.now() + timedelta(days=7)
            ... )
        """
        self._validate_user_exist(session, user_id)
        created_by = self._validate_user_exist(session, created_by)
        
        auth_session = self.auth_session_crud._create(
            session,
            user_id=user_id,
            created_by=created_by,
            **kwargs
        )
        return self._serialize_single_result(auth_session)

    @with_orchestration_errors('update_auth_session')
    @with_session
    def update(self, session, *, record_id: str, updated_by: str, **kwargs) -> Dict[str, Any]:
        """Session bilgilerini günceller."""
        updated_by = self._validate_user_exist(session, updated_by)
        record_id = self._validate_auth_session_exist(session, record_id)
        
        result = self.auth_session_crud._update(
            session,
            record_id,
            updated_by=updated_by,
            **kwargs
        )
        return self._serialize_single_result(result)

    @with_orchestration_errors('revoke_auth_session')
    @with_session
    def revoke(self, session, session_id: str, revoked_by: str) -> Dict[str, Any]:
        """
        Authentication session'ı iptal eder (logout).
        
        Kullanım Amacı:
            - User logout: Kullanıcı çıkış
            - Security action: Güvenlik önlemi
            - Admin revocation: Admin tarafından iptal
        """
        self._validate_auth_session_exist(session, session_id)
        self._validate_user_exist(session, revoked_by)
        
        result = self.auth_session_crud._revoke(session, session_id, revoked_by)
        return self._serialize_single_result(result)

    @with_orchestration_errors('revoke_all_user_sessions')
    @with_session
    def revoke_all_user_sessions(self, session, user_id: str, revoked_by: str) -> Dict[str, Any]:
        """
        Kullanıcının tüm session'larını iptal eder.
        
        Kullanım Amacı:
            - Logout from all devices: Tüm cihazlardan çıkış
            - Password change: Şifre değişikliği sonrası
            - Security breach: Güvenlik ihlali
        
        Example:
            >>> auth_session_orch.revoke_all_user_sessions(
            ...     user_id="USR_123",
            ...     revoked_by="USR_123"  # Self or admin
            ... )
        """
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, revoked_by)
        
        result = self.auth_session_crud._revoke_all_user_sessions(session, user_id, revoked_by)
        return {'revoked_count': result, 'user_id': user_id}

    @with_orchestration_errors('refresh_access_token')
    @with_session
    def refresh_access_token(self, session, session_id: str, new_access_token_jti: str, new_access_token_expires_at) -> Dict[str, Any]:
        """
        Access token'ı yeniler (refresh).
        
        Kullanım Amacı:
            - Token refresh: Access token süresi dolduğunda
            - Session extension: Oturum uzatma
        """
        self._validate_auth_session_exist(session, session_id)
        
        result = self.auth_session_crud._refresh_access_token(
            session,
            session_id,
            new_access_token_jti,
            new_access_token_expires_at
        )
        return self._serialize_single_result(result)

    @with_orchestration_errors('rotate_tokens')
    @with_session
    def rotate_tokens(self, session, session_id: str, new_access_jti: str, new_access_expires,
                     new_refresh_jti: str, new_refresh_expires) -> Dict[str, Any]:
        """
        Hem access hem refresh token'ları yeniler (rotation).
        
        Kullanım Amacı:
            - Token rotation: Güvenlik için periyodik rotation
            - Refresh token rotation: Refresh kullanıldığında yenileme
        """
        self._validate_auth_session_exist(session, session_id)
        
        result = self.auth_session_crud._rotate_tokens(
            session,
            session_id,
            new_access_jti,
            new_access_expires,
            new_refresh_jti,
            new_refresh_expires
        )
        return self._serialize_single_result(result)

    @with_orchestration_errors('update_access_token_usage')
    @with_session
    def update_access_token_usage(self, session, session_id: str) -> Dict[str, Any]:
        """Access token kullanım sayacını arttırır."""
        self._validate_auth_session_exist(session, session_id)
        
        result = self.auth_session_crud._update_access_token_usage(session, session_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('check_access_token_valid')
    @with_session
    def check_access_token_valid(self, session, session_id: str, jti: str) -> Dict[str, Any]:
        """
        Access token'ın geçerli olup olmadığını kontrol eder.
        
        Returns:
            Dict with 'is_valid' boolean and reason if invalid
        """
        self._validate_auth_session_exist(session, session_id)
        
        result = self.auth_session_crud._check_access_token_valid(session, session_id, jti)
        return result

    @with_orchestration_errors('check_refresh_token_valid')
    @with_session
    def check_refresh_token_valid(self, session, session_id: str, jti: str) -> Dict[str, Any]:
        """
        Refresh token'ın geçerli olup olmadığını kontrol eder.
        
        Returns:
            Dict with 'is_valid' boolean and reason if invalid
        """
        self._validate_auth_session_exist(session, session_id)
        
        result = self.auth_session_crud._check_refresh_token_valid(session, session_id, jti)
        return result

    @with_orchestration_errors('get_user_sessions')
    @with_session
    def get_by_user(self, session, user_id: str) -> Dict[str, Any]:
        """Kullanıcının tüm session'larını listeler."""
        self._validate_user_exist(session, user_id)
        
        sessions = self.auth_session_crud._get_by_user(session, user_id)
        return self._serialize_list_result(sessions, len(sessions))

    @with_orchestration_errors('get_active_user_sessions')
    @with_session
    def get_active_sessions_by_user(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcının aktif session'larını listeler.
        
        Kullanım Amacı:
            - Active sessions page: Aktif oturumlar sayfası
            - Security monitoring: Güvenlik takibi
            - Multi-device view: Tüm cihazları görme
        """
        self._validate_user_exist(session, user_id)
        
        sessions = self.auth_session_crud._get_active_sessions_by_user(session, user_id)
        return self._serialize_list_result(sessions, len(sessions))

    @with_orchestration_errors('get_expired_sessions')
    @with_session
    def get_expired_sessions(self, session, limit: int = 100) -> Dict[str, Any]:
        """Süresi dolmuş session'ları listeler."""
        sessions = self.auth_session_crud._get_expired_sessions(session, limit)
        return self._serialize_list_result(sessions, len(sessions))

    @with_orchestration_errors('cleanup_expired_sessions')
    @with_session
    def cleanup_expired_sessions(self, session, days_old: int = 30) -> Dict[str, Any]:
        """
        Eski ve süresi dolmuş session'ları temizler.
        
        Kullanım Amacı:
            - Database cleanup: Veritabanı temizliği
            - Scheduled job: Periyodik temizlik job'ı
            - Storage optimization: Depolama optimizasyonu
        
        Args:
            days_old: Kaç günden eski session'lar silinsin
        
        Example:
            >>> result = auth_session_orch.cleanup_expired_sessions(days_old=30)
            >>> print(f"Cleaned up {result['deleted_count']} sessions")
        """
        deleted_count = self.auth_session_crud._cleanup_expired_sessions(session, days_old)
        return {'deleted_count': deleted_count, 'days_old': days_old}

    @with_orchestration_errors('get_sessions_by_device')
    @with_session
    def get_sessions_by_device(self, session, user_id: str, device_info: str) -> Dict[str, Any]:
        """Device bilgisine göre session'ları listeler."""
        self._validate_user_exist(session, user_id)
        
        sessions = self.auth_session_crud._get_sessions_by_device(session, user_id, device_info)
        return self._serialize_list_result(sessions, len(sessions))

    @with_orchestration_errors('get_session_count_by_user')
    @with_session
    def get_session_count_by_user(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcının toplam session sayısını döner.
        
        Kullanım Amacı:
            - Session limit: Maksimum session kontrolü
            - Monitoring: İzleme ve raporlama
        """
        self._validate_user_exist(session, user_id)
        
        count = self.auth_session_crud._get_session_count_by_user(session, user_id)
        return {'user_id': user_id, 'session_count': count}

    @with_orchestration_errors('get_sessions_by_country')
    @with_session
    def get_sessions_by_country(self, session, user_id: str, country_code: str) -> Dict[str, Any]:
        """Ülke koduna göre session'ları listeler."""
        self._validate_user_exist(session, user_id)
        
        sessions = self.auth_session_crud._get_sessions_by_country(session, user_id, country_code)
        return self._serialize_list_result(sessions, len(sessions))

    @with_orchestration_errors('get_auth_session_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get auth session by ID - Only own sessions.
        Users can only access their own authentication sessions.
        """
        record_id = self._validate_auth_session_exist(session, record_id)
        user_id = self._validate_user_exist(session, user_id)
        
        # Get session to check ownership
        auth_session = self.auth_session_crud._get_by_id(session, record_id)
        if not auth_session:
            return None
        
        # Users can only view their own sessions
        if auth_session.user_id != user_id:
            self._raise_permission_denied('access', user_id, record_id, 'auth_session')
        
        return self._serialize_single_result(
            auth_session,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_auth_sessions')
    @with_session
    def get_all(self, session, *, user_id: str, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all auth sessions - Only own sessions.
        Users can only access their own authentication sessions.
        """
        user_id = self._validate_user_exist(session, user_id)
        
        from sqlalchemy import select
        
        # Only return the requesting user's own sessions
        query = select(self.auth_session_crud.model).where(
            self.auth_session_crud.model.user_id == user_id
        )
        
        if not include_deleted:
            query = query.where(self.auth_session_crud.model.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(self.auth_session_crud.model, key):
                query = query.where(getattr(self.auth_session_crud.model, key) == value)
        
        if order_by and hasattr(self.auth_session_crud.model, order_by):
            order_column = getattr(self.auth_session_crud.model, order_by)
            query = query.order_by(order_column.desc() if order_desc else order_column)
        
        query = query.offset(skip).limit(limit)
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results,
            include_relationships=False,
            exclude_fields=exclude_fields
        )

