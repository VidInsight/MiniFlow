from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone, timedelta
import ipaddress

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import ApiKey
from .base_crud import BaseCRUD


class ApiKeyCRUD(BaseCRUD[ApiKey]):
    def __init__(self):
        super().__init__(ApiKey)
        self.model_fields = {column.name for column in ApiKey.__table__.columns}
        self.required_fields = {'user_id', 'name', 'key_hash', 'key_prefix'}
        self.protected_fields = {'user_id', 'key_hash', 'revoked_at', 'revoked_by', 
                                'total_requests', 'current_hour_requests', 'current_day_requests'}

    def _create(self, session: Session, **kwargs) -> ApiKey:
        """Create a new API key with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate user_id
        user_id = kwargs.get('user_id')
        if user_id:
            kwargs['user_id'] = validators._validate_id(user_id)
        
        # Validate name
        name = kwargs.get('name')
        if name:
            kwargs['name'] = validators._validate_name(name)
        
        # Validate key_hash
        key_hash = kwargs.get('key_hash')
        if key_hash:
            if not isinstance(key_hash, str) or len(key_hash) < 32:
                raise ValueError("Key hash must be a string with at least 32 characters")
            # Check uniqueness
            self._validate_key_hash_uniqueness(session, key_hash)
        
        # Validate key_prefix
        key_prefix = kwargs.get('key_prefix')
        if key_prefix:
            if not isinstance(key_prefix, str) or len(key_prefix) < 4:
                raise ValueError("Key prefix must be at least 4 characters")
        
        # Validate scopes if provided
        scopes = kwargs.get('scopes')
        if scopes is not None:
            if not isinstance(scopes, list):
                raise ValueError("Scopes must be a list")
            kwargs['scopes'] = self._validate_scopes(scopes)
        
        # Validate allowed_ips if provided
        allowed_ips = kwargs.get('allowed_ips')
        if allowed_ips is not None:
            if not isinstance(allowed_ips, list):
                raise ValueError("Allowed IPs must be a list")
            kwargs['allowed_ips'] = self._validate_ip_list(allowed_ips)
        
        # Validate rate limits
        if 'rate_limit_per_hour' in kwargs:
            self._validate_rate_limit(kwargs['rate_limit_per_hour'], 'hour')
        
        if 'rate_limit_per_day' in kwargs:
            self._validate_rate_limit(kwargs['rate_limit_per_day'], 'day')
        
        # Validate expires_at if provided
        if 'expires_at' in kwargs and kwargs['expires_at']:
            expires_at = kwargs['expires_at']
            if isinstance(expires_at, datetime) and expires_at <= datetime.now(timezone.utc):
                raise ValueError("Expiration date must be in the future")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        api_key = super()._create(session, **kwargs)
        return api_key

    def _update(self, session: Session, record_id: str, **kwargs) -> ApiKey:
        """Update API key with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Validate name if being updated
        if 'name' in kwargs and kwargs['name']:
            kwargs['name'] = validators._validate_name(kwargs['name'])
        
        # Validate scopes if being updated
        if 'scopes' in kwargs and kwargs['scopes'] is not None:
            if not isinstance(kwargs['scopes'], list):
                raise ValueError("Scopes must be a list")
            kwargs['scopes'] = self._validate_scopes(kwargs['scopes'])
        
        # Validate allowed_ips if being updated
        if 'allowed_ips' in kwargs and kwargs['allowed_ips'] is not None:
            if not isinstance(kwargs['allowed_ips'], list):
                raise ValueError("Allowed IPs must be a list")
            kwargs['allowed_ips'] = self._validate_ip_list(kwargs['allowed_ips'])
        
        # Validate rate limits
        if 'rate_limit_per_hour' in kwargs:
            self._validate_rate_limit(kwargs['rate_limit_per_hour'], 'hour')
        
        if 'rate_limit_per_day' in kwargs:
            self._validate_rate_limit(kwargs['rate_limit_per_day'], 'day')
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        api_key = super()._update(session, record_id, **kwargs)
        return api_key

    def _validate_key_hash_uniqueness(self, session: Session, key_hash: str):
        """Validate that key hash is unique."""
        existing = session.query(self.model).filter(
            and_(
                self.model.key_hash == key_hash,
                self.model.is_deleted == False
            )
        ).first()
        
        if existing:
            context = ErrorContext(operation='validate_key_hash_uniqueness', component=self.model_name,
                                 additional_info={'existing_id': existing.id})
            raise ValidationError("API key already exists",
                                context=context, severity=ErrorSeverity.HIGH)

    def _validate_scopes(self, scopes: List[str]) -> List[str]:
        """Validate scopes list."""
        if not all(isinstance(scope, str) for scope in scopes):
            raise ValueError("All scopes must be strings")
        
        # Remove duplicates
        return list(set(scopes))

    def _validate_ip_list(self, ip_list: List[str]) -> List[str]:
        """Validate IP address list."""
        validated_ips = []
        
        for ip in ip_list:
            if not isinstance(ip, str):
                raise ValueError(f"IP address must be a string: {ip}")
            
            try:
                # Validate IPv4 or IPv6 address
                ipaddress.ip_address(ip)
                validated_ips.append(ip)
            except ValueError:
                raise ValueError(f"Invalid IP address: {ip}")
        
        return validated_ips

    def _validate_rate_limit(self, limit: Optional[int], period: str):
        """Validate rate limit value."""
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError(f"Rate limit per {period} must be a positive integer")

    def _revoke(self, session: Session, record_id: str, revoked_by: str, reason: Optional[str] = None) -> ApiKey:
        """Revoke an API key."""
        api_key = self._get_by_id(session, record_id)
        if not api_key:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        # Validate revoked_by
        revoked_by = validators._validate_id(revoked_by)
        
        api_key.is_revoked = True
        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.revoked_by = revoked_by
        
        if reason:
            api_key.revocation_reason = reason
        
        session.add(api_key)
        session.flush()
        return api_key

    def _activate(self, session: Session, record_id: str) -> ApiKey:
        """Activate an API key (only if not revoked)."""
        api_key = self._get_by_id(session, record_id)
        if not api_key:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        if api_key.is_revoked:
            raise ValidationError("Cannot activate a revoked API key. Create a new one instead.",
                                severity=ErrorSeverity.MEDIUM)
        
        api_key.is_active = True
        session.add(api_key)
        session.flush()
        return api_key

    def _deactivate(self, session: Session, record_id: str) -> ApiKey:
        """Temporarily deactivate an API key."""
        api_key = self._get_by_id(session, record_id)
        if not api_key:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        api_key.is_active = False
        session.add(api_key)
        session.flush()
        return api_key

    def _check_expiration(self, api_key: ApiKey) -> bool:
        """Check if API key is expired."""
        if not api_key.expires_at:
            return False  # No expiration set
        
        return datetime.now(timezone.utc) > api_key.expires_at

    def _check_rate_limit(self, api_key: ApiKey) -> Dict[str, Any]:
        """
        Check if API key has exceeded rate limits.
        
        Returns:
            Dict with 'exceeded' (bool), 'period' (str), and 'reset_at' (datetime)
        """
        now = datetime.now(timezone.utc)
        
        # Check if rate limit reset is needed
        if api_key.rate_limit_reset_at and now > api_key.rate_limit_reset_at:
            # Reset counters (this should be done in a separate call)
            pass
        
        # Check hourly limit
        if api_key.rate_limit_per_hour:
            if api_key.current_hour_requests >= api_key.rate_limit_per_hour:
                return {
                    'exceeded': True,
                    'period': 'hour',
                    'limit': api_key.rate_limit_per_hour,
                    'current': api_key.current_hour_requests,
                    'reset_at': api_key.rate_limit_reset_at
                }
        
        # Check daily limit
        if api_key.rate_limit_per_day:
            if api_key.current_day_requests >= api_key.rate_limit_per_day:
                return {
                    'exceeded': True,
                    'period': 'day',
                    'limit': api_key.rate_limit_per_day,
                    'current': api_key.current_day_requests,
                    'reset_at': api_key.rate_limit_reset_at
                }
        
        return {'exceeded': False}

    def _increment_usage(self, session: Session, record_id: str, ip_address: Optional[str] = None, 
                        user_agent: Optional[str] = None) -> ApiKey:
        """Increment usage counters and update last used info."""
        api_key = self._get_by_id(session, record_id)
        if not api_key:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        now = datetime.now(timezone.utc)
        
        # Check if we need to reset counters
        if api_key.rate_limit_reset_at and now > api_key.rate_limit_reset_at:
            # Reset hourly/daily counters
            api_key.current_hour_requests = 0
            api_key.current_day_requests = 0
            # Set next reset time (1 hour from now)
            api_key.rate_limit_reset_at = now + timedelta(hours=1)
        
        # Initialize reset time if not set
        if not api_key.rate_limit_reset_at:
            api_key.rate_limit_reset_at = now + timedelta(hours=1)
        
        # Increment counters
        api_key.total_requests += 1
        api_key.current_hour_requests += 1
        api_key.current_day_requests += 1
        
        # Update last used info
        api_key.last_used_at = now
        
        if ip_address:
            api_key.last_used_ip = ip_address
        
        if user_agent:
            api_key.user_agent = user_agent
        
        session.add(api_key)
        session.flush()
        return api_key

    def _reset_rate_limits(self, session: Session, record_id: str) -> ApiKey:
        """Reset rate limit counters."""
        api_key = self._get_by_id(session, record_id)
        if not api_key:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        api_key.current_hour_requests = 0
        api_key.current_day_requests = 0
        api_key.rate_limit_reset_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        session.add(api_key)
        session.flush()
        return api_key

    def _check_ip_allowed(self, api_key: ApiKey, ip_address: str) -> bool:
        """Check if IP address is in the whitelist."""
        # Empty list means all IPs are allowed
        if not api_key.allowed_ips:
            return True
        
        return ip_address in api_key.allowed_ips

    def _check_scope(self, api_key: ApiKey, required_scope: str) -> bool:
        """Check if API key has the required scope."""
        # Empty scopes means all scopes are allowed
        if not api_key.scopes:
            return True
        
        return required_scope in api_key.scopes

    def _get_by_user(self, session: Session, user_id: str, skip: int = 0, limit: int = None) -> List[ApiKey]:
        """Get API keys for a specific user with pagination."""
        try:
            user_id = validators._validate_id(user_id)
            
            # Validate pagination parameters
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.desc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_user', component=self.model_name,
                                 additional_info={'user_id': user_id, 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by user: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_active_keys(self, session: Session, user_id: Optional[str] = None) -> List[ApiKey]:
        """Get all active and non-expired API keys."""
        try:
            now = datetime.now(timezone.utc)
            
            query = session.query(self.model).filter(
                and_(
                    self.model.is_active == True,
                    self.model.is_revoked == False,
                    self.model.is_deleted == False,
                    or_(
                        self.model.expires_at == None,
                        self.model.expires_at > now
                    )
                )
            )
            
            if user_id:
                user_id = validators._validate_id(user_id)
                query = query.filter(self.model.user_id == user_id)
            
            results = query.order_by(self.model.created_at.desc()).all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_active_keys', component=self.model_name,
                                 additional_info={'user_id': user_id})
            raise DatabaseQueryError(f"Failed to get active {self.model_name} records: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_key_prefix(self, session: Session, key_prefix: str) -> Optional[ApiKey]:
        """Get API key by prefix."""
        try:
            if not key_prefix or len(key_prefix) < 4:
                raise ValueError("Key prefix must be at least 4 characters")
            
            api_key = session.query(self.model).filter(
                and_(
                    self.model.key_prefix == key_prefix,
                    self.model.is_deleted == False
                )
            ).first()
            
            return api_key
            
        except Exception as e:
            context = ErrorContext(operation='get_by_key_prefix', component=self.model_name,
                                 additional_info={'key_prefix': key_prefix})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by prefix: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _validate_key(self, session: Session, key_hash: str) -> Optional[ApiKey]:
        """
        Validate API key and return it if valid.
        Checks: exists, active, not revoked, not expired.
        """
        try:
            if not key_hash or len(key_hash) < 32:
                return None
            
            now = datetime.now(timezone.utc)
            
            api_key = session.query(self.model).filter(
                and_(
                    self.model.key_hash == key_hash,
                    self.model.is_active == True,
                    self.model.is_revoked == False,
                    self.model.is_deleted == False,
                    or_(
                        self.model.expires_at == None,
                        self.model.expires_at > now
                    )
                )
            ).first()
            
            return api_key
            
        except Exception as e:
            # For security, return None on any error
            return None

