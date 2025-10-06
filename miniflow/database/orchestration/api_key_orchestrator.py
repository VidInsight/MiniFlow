from typing import Dict, Any, List, Optional

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class ApiKeyOrchestrator(BaseOrchestrator):
    """
    API Key orchestrator for API key lifecycle management.
    
    Provides:
    - API key CRUD operations
    - Rate limiting
    - IP whitelisting
    - Scope management
    - Expiration handling
    """

    def _get_primary_crud(self):
        return self.api_key_crud

    @with_orchestration_errors('create_api_key')
    @with_session
    def create(self, session, *, user_id: str, created_by: str, **kwargs) -> Dict[str, Any]:
        """
        Yeni API key oluşturur.
        
        Kullanım Amacı:
            - API access: Programmatic API erişimi
            - Integration: 3rd party entegrasyonlar
            - Service accounts: Servis hesapları
        
        Args:
            user_id: API key sahibi kullanıcı
            name: API key adı
            key_hash: Hash'lenmiş key
            key_prefix: Key prefix (gösterim için)
            scopes: (Optional) İzin verilen scope'lar
            allowed_ips: (Optional) İzinli IP'ler
            rate_limit_per_hour: (Optional) Saatlik rate limit
            rate_limit_per_day: (Optional) Günlük rate limit
        
        Example:
            >>> api_key = api_key_orch.create(
            ...     user_id="USR_123",
            ...     name="Production API",
            ...     key_hash="$2b$12$...",
            ...     key_prefix="mkf_prod_",
            ...     scopes=["read", "write"],
            ...     rate_limit_per_hour=1000
            ... )
        """
        self._validate_user_exist(session, user_id)
        created_by = self._validate_user_exist(session, created_by)
        
        api_key = self.api_key_crud._create(
            session, 
            user_id=user_id,
            created_by=created_by,
            **kwargs
        )
        return self._serialize_single_result(api_key)

    @with_orchestration_errors('update_api_key')
    @with_session
    def update(self, session, *, record_id: str, updated_by: str, **kwargs) -> Dict[str, Any]:
        """API key bilgilerini günceller."""
        updated_by = self._validate_user_exist(session, updated_by)
        record_id = self._validate_api_key_exist(session, record_id)
        
        result = self.api_key_crud._update(
            session, 
            record_id,
            updated_by=updated_by,
            **kwargs
        )
        return self._serialize_single_result(result)

    @with_orchestration_errors('revoke_api_key')
    @with_session
    def revoke(self, session, api_key_id: str, revoked_by: str) -> Dict[str, Any]:
        """
        API key'i iptal eder.
        
        Kullanım Amacı:
            - Security breach: Güvenlik ihlali
            - Key rotation: Periyodik key değişimi
            - Access revocation: Erişim iptali
        """
        self._validate_api_key_exist(session, api_key_id)
        self._validate_user_exist(session, revoked_by)
        
        result = self.api_key_crud._revoke(session, api_key_id, revoked_by)
        return self._serialize_single_result(result)

    @with_orchestration_errors('activate_api_key')
    @with_session
    def activate(self, session, api_key_id: str) -> Dict[str, Any]:
        """API key'i aktif eder."""
        self._validate_api_key_exist(session, api_key_id)
        
        result = self.api_key_crud._activate(session, api_key_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('deactivate_api_key')
    @with_session
    def deactivate(self, session, api_key_id: str) -> Dict[str, Any]:
        """API key'i deaktif eder."""
        self._validate_api_key_exist(session, api_key_id)
        
        result = self.api_key_crud._deactivate(session, api_key_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('check_api_key_expiration')
    @with_session
    def check_expiration(self, session, api_key_id: str) -> Dict[str, Any]:
        """
        API key'in süresinin dolup dolmadığını kontrol eder.
        
        Returns:
            Dict with 'is_expired' boolean
        """
        self._validate_api_key_exist(session, api_key_id)
        
        is_expired = self.api_key_crud._check_expiration(session, api_key_id)
        return {'api_key_id': api_key_id, 'is_expired': is_expired}

    @with_orchestration_errors('check_api_key_rate_limit')
    @with_session
    def check_rate_limit(self, session, api_key_id: str) -> Dict[str, Any]:
        """
        Rate limit kontrolü yapar.
        
        Returns:
            Dict with 'allowed' boolean and limit info
        """
        self._validate_api_key_exist(session, api_key_id)
        
        result = self.api_key_crud._check_rate_limit(session, api_key_id)
        return result

    @with_orchestration_errors('increment_api_key_usage')
    @with_session
    def increment_usage(self, session, api_key_id: str) -> Dict[str, Any]:
        """API key kullanım sayacını arttırır."""
        self._validate_api_key_exist(session, api_key_id)
        
        result = self.api_key_crud._increment_usage(session, api_key_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('reset_api_key_rate_limits')
    @with_session
    def reset_rate_limits(self, session, api_key_id: str) -> Dict[str, Any]:
        """Rate limit sayaçlarını sıfırlar."""
        self._validate_api_key_exist(session, api_key_id)
        
        result = self.api_key_crud._reset_rate_limits(session, api_key_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('check_ip_allowed')
    @with_session
    def check_ip_allowed(self, session, api_key_id: str, ip_address: str) -> Dict[str, Any]:
        """
        IP adresinin izinli olup olmadığını kontrol eder.
        
        Returns:
            Dict with 'allowed' boolean
        """
        self._validate_api_key_exist(session, api_key_id)
        
        allowed = self.api_key_crud._check_ip_allowed(session, api_key_id, ip_address)
        return {'api_key_id': api_key_id, 'ip_address': ip_address, 'allowed': allowed}

    @with_orchestration_errors('check_api_key_scope')
    @with_session
    def check_scope(self, session, api_key_id: str, required_scope: str) -> Dict[str, Any]:
        """
        Scope iznini kontrol eder.
        
        Returns:
            Dict with 'has_scope' boolean
        """
        self._validate_api_key_exist(session, api_key_id)
        
        has_scope = self.api_key_crud._check_scope(session, api_key_id, required_scope)
        return {'api_key_id': api_key_id, 'scope': required_scope, 'has_scope': has_scope}

    @with_orchestration_errors('get_user_api_keys')
    @with_session
    def get_by_user(self, session, user_id: str) -> Dict[str, Any]:
        """Kullanıcının tüm API key'lerini listeler."""
        self._validate_user_exist(session, user_id)
        
        keys = self.api_key_crud._get_by_user(session, user_id)
        return self._serialize_list_result(keys, len(keys))

    @with_orchestration_errors('get_active_api_keys')
    @with_session
    def get_active_keys(self, session, user_id: str) -> Dict[str, Any]:
        """Kullanıcının aktif API key'lerini listeler."""
        self._validate_user_exist(session, user_id)
        
        keys = self.api_key_crud._get_active_keys(session, user_id)
        return self._serialize_list_result(keys, len(keys))

    @with_orchestration_errors('get_api_key_by_prefix')
    @with_session
    def get_by_key_prefix(self, session, key_prefix: str) -> Dict[str, Any]:
        """Key prefix ile API key bulur."""
        key = self.api_key_crud._get_by_key_prefix(session, key_prefix)
        if key:
            return self._serialize_single_result(key)
        else:
            return {'found': False, 'key_prefix': key_prefix}

    @with_orchestration_errors('get_api_key_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get API key by ID - Only own API keys.
        Users can only access their own API keys.
        """
        record_id = self._validate_api_key_exist(session, record_id)
        user_id = self._validate_user_exist(session, user_id)
        
        # Get API key to check ownership
        api_key = self.api_key_crud._get_by_id(session, record_id)
        if not api_key:
            return None
        
        # Users can only view their own API keys
        if api_key.created_by != user_id:
            self._raise_permission_denied('access', user_id, record_id, 'api_key')
        
        return self._serialize_single_result(
            api_key,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_api_keys')
    @with_session
    def get_all(self, session, *, user_id: str, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all API keys - Only own API keys.
        Users can only access their own API keys.
        """
        user_id = self._validate_user_exist(session, user_id)
        
        from sqlalchemy import select
        
        # Only return the requesting user's own API keys
        query = select(self.api_key_crud.model).where(
            self.api_key_crud.model.created_by == user_id
        )
        
        if not include_deleted:
            query = query.where(self.api_key_crud.model.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(self.api_key_crud.model, key):
                query = query.where(getattr(self.api_key_crud.model, key) == value)
        
        if order_by and hasattr(self.api_key_crud.model, order_by):
            order_column = getattr(self.api_key_crud.model, order_by)
            query = query.order_by(order_column.desc() if order_desc else order_column)
        
        query = query.offset(skip).limit(limit)
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results,
            include_relationships=False,
            exclude_fields=exclude_fields
        )

