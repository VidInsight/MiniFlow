from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone, timedelta

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import AuthSession
from .base_crud import BaseCRUD


class AuthSessionCRUD(BaseCRUD[AuthSession]):
    def __init__(self):
        super().__init__(AuthSession)
        self.model_fields = {column.name for column in AuthSession.__table__.columns}
        self.required_fields = {'user_id', 'access_token_jti', 'access_token_expires_at', 
                               'refresh_token_jti', 'refresh_token_expires_at'}
        self.protected_fields = {'user_id', 'access_token_jti', 'refresh_token_jti', 
                                'revoked_at', 'revoked_by', 'total_requests'}

    def _create(self, session: Session, **kwargs) -> AuthSession:
        """Create a new authentication session with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate user_id
        user_id = kwargs.get('user_id')
        if user_id:
            kwargs['user_id'] = validators._validate_id(user_id)
        
        # Validate access_token_jti
        access_token_jti = kwargs.get('access_token_jti')
        if access_token_jti:
            if not isinstance(access_token_jti, str) or len(access_token_jti) < 10:
                raise ValueError("Access token JTI must be at least 10 characters")
            # Check uniqueness
            self._validate_jti_uniqueness(session, access_token_jti, 'access')
        
        # Validate refresh_token_jti
        refresh_token_jti = kwargs.get('refresh_token_jti')
        if refresh_token_jti:
            if not isinstance(refresh_token_jti, str) or len(refresh_token_jti) < 10:
                raise ValueError("Refresh token JTI must be at least 10 characters")
            # Check uniqueness
            self._validate_jti_uniqueness(session, refresh_token_jti, 'refresh')
        
        # Validate expiration dates
        access_expires = kwargs.get('access_token_expires_at')
        if access_expires and isinstance(access_expires, datetime):
            if access_expires <= datetime.now(timezone.utc):
                raise ValueError("Access token expiration must be in the future")
        
        refresh_expires = kwargs.get('refresh_token_expires_at')
        if refresh_expires and isinstance(refresh_expires, datetime):
            if refresh_expires <= datetime.now(timezone.utc):
                raise ValueError("Refresh token expiration must be in the future")
            # Refresh token should expire after access token
            if access_expires and refresh_expires <= access_expires:
                raise ValueError("Refresh token must expire after access token")
        
        # Validate IP address if provided
        ip_address = kwargs.get('ip_address')
        if ip_address:
            kwargs['ip_address'] = self._validate_ip_address(ip_address)
        
        # Validate country code if provided
        country = kwargs.get('country')
        if country:
            kwargs['country'] = self._validate_country_code(country)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        auth_session = super()._create(session, **kwargs)
        return auth_session

    def _update(self, session: Session, record_id: str, **kwargs) -> AuthSession:
        """Update auth session with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Validate IP address if being updated
        if 'ip_address' in kwargs and kwargs['ip_address']:
            kwargs['ip_address'] = self._validate_ip_address(kwargs['ip_address'])
        
        # Validate country code if being updated
        if 'country' in kwargs and kwargs['country']:
            kwargs['country'] = self._validate_country_code(kwargs['country'])
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        auth_session = super()._update(session, record_id, **kwargs)
        return auth_session

    def _validate_jti_uniqueness(self, session: Session, jti: str, token_type: str):
        """Validate that token JTI is unique."""
        if token_type == 'access':
            existing = session.query(self.model).filter(
                and_(
                    self.model.access_token_jti == jti,
                    self.model.is_deleted == False
                )
            ).first()
        else:  # refresh
            existing = session.query(self.model).filter(
                and_(
                    self.model.refresh_token_jti == jti,
                    self.model.is_deleted == False
                )
            ).first()
        
        if existing:
            context = ErrorContext(operation='validate_jti_uniqueness', component=self.model_name,
                                 additional_info={'jti': jti, 'type': token_type, 'existing_id': existing.id})
            raise ValidationError(f"{token_type.title()} token JTI already exists",
                                context=context, severity=ErrorSeverity.HIGH)

    def _validate_ip_address(self, ip_address: str) -> str:
        """Validate IP address format."""
        import ipaddress as ip_module
        try:
            ip_module.ip_address(ip_address)
            return ip_address
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_address}")

    def _validate_country_code(self, country: str) -> str:
        """Validate ISO country code (2 letters)."""
        if not isinstance(country, str) or len(country) != 2:
            raise ValueError("Country code must be 2 characters (ISO format)")
        return country.upper()

    def _revoke(self, session: Session, record_id: str, revoked_by: str, reason: Optional[str] = None) -> AuthSession:
        """Revoke an authentication session."""
        auth_session = self._get_by_id(session, record_id)
        if not auth_session:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        # Validate revoked_by
        revoked_by = validators._validate_id(revoked_by)
        
        auth_session.is_revoked = True
        auth_session.revoked_at = datetime.now(timezone.utc)
        auth_session.revoked_by = revoked_by
        
        if reason:
            auth_session.revocation_reason = reason
        
        session.add(auth_session)
        session.flush()
        return auth_session

    def _revoke_all_user_sessions(self, session: Session, user_id: str, revoked_by: str, 
                                  reason: Optional[str] = None) -> List[AuthSession]:
        """Revoke all active sessions for a user."""
        user_id = validators._validate_id(user_id)
        revoked_by = validators._validate_id(revoked_by)
        
        active_sessions = self._get_active_sessions_by_user(session, user_id)
        
        revoked_sessions = []
        for auth_session in active_sessions:
            auth_session.is_revoked = True
            auth_session.revoked_at = datetime.now(timezone.utc)
            auth_session.revoked_by = revoked_by
            if reason:
                auth_session.revocation_reason = reason
            session.add(auth_session)
            revoked_sessions.append(auth_session)
        
        session.flush()
        return revoked_sessions

    def _refresh_access_token(self, session: Session, record_id: str, new_access_token_jti: str, 
                              new_access_expires_at: datetime) -> AuthSession:
        """
        Update access token when refreshing (without rotating refresh token).
        
        Note: For better security, consider using _rotate_tokens() instead,
        which implements refresh token rotation.
        """
        auth_session = self._get_by_id(session, record_id)
        if not auth_session:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        # Validate new JTI
        if not isinstance(new_access_token_jti, str) or len(new_access_token_jti) < 10:
            raise ValueError("Access token JTI must be at least 10 characters")
        
        # Check uniqueness of new JTI
        self._validate_jti_uniqueness(session, new_access_token_jti, 'access')
        
        # Validate expiration
        if new_access_expires_at <= datetime.now(timezone.utc):
            raise ValueError("Access token expiration must be in the future")
        
        # Update access token info
        auth_session.access_token_jti = new_access_token_jti
        auth_session.access_token_created_at = datetime.now(timezone.utc)
        auth_session.access_token_expires_at = new_access_expires_at
        auth_session.access_token_last_used_at = datetime.now(timezone.utc)
        auth_session.refresh_token_last_used_at = datetime.now(timezone.utc)
        auth_session.last_activity_at = datetime.now(timezone.utc)
        
        session.add(auth_session)
        session.flush()
        return auth_session

    def _rotate_tokens(self, session: Session, record_id: str, 
                      new_access_token_jti: str, new_access_expires_at: datetime,
                      new_refresh_token_jti: str, new_refresh_expires_at: datetime) -> AuthSession:
        """
        Rotate both access and refresh tokens (JWT best practice).
        
        This implements refresh token rotation for enhanced security:
        - When refresh token is used, both tokens are rotated
        - Prevents refresh token reuse attacks
        - Recommended for production environments
        
        Args:
            session: Database session
            record_id: Auth session ID
            new_access_token_jti: New access token JTI
            new_access_expires_at: New access token expiration
            new_refresh_token_jti: New refresh token JTI
            new_refresh_expires_at: New refresh token expiration
        
        Returns:
            Updated AuthSession with new tokens
        """
        auth_session = self._get_by_id(session, record_id)
        if not auth_session:
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                severity=ErrorSeverity.MEDIUM)
        
        # Validate new access token JTI
        if not isinstance(new_access_token_jti, str) or len(new_access_token_jti) < 10:
            raise ValueError("Access token JTI must be at least 10 characters")
        self._validate_jti_uniqueness(session, new_access_token_jti, 'access')
        
        # Validate new refresh token JTI
        if not isinstance(new_refresh_token_jti, str) or len(new_refresh_token_jti) < 10:
            raise ValueError("Refresh token JTI must be at least 10 characters")
        self._validate_jti_uniqueness(session, new_refresh_token_jti, 'refresh')
        
        # Validate expiration dates
        now = datetime.now(timezone.utc)
        if new_access_expires_at <= now:
            raise ValueError("Access token expiration must be in the future")
        if new_refresh_expires_at <= now:
            raise ValueError("Refresh token expiration must be in the future")
        if new_refresh_expires_at <= new_access_expires_at:
            raise ValueError("Refresh token must expire after access token")
        
        # Rotate both tokens
        auth_session.access_token_jti = new_access_token_jti
        auth_session.access_token_created_at = now
        auth_session.access_token_expires_at = new_access_expires_at
        auth_session.access_token_last_used_at = now
        
        auth_session.refresh_token_jti = new_refresh_token_jti
        auth_session.refresh_token_created_at = now
        auth_session.refresh_token_expires_at = new_refresh_expires_at
        auth_session.refresh_token_last_used_at = now
        
        auth_session.last_activity_at = now
        
        session.add(auth_session)
        session.flush()
        return auth_session

    def _update_access_token_usage(self, session: Session, access_token_jti: str, 
                                   ip_address: Optional[str] = None) -> Optional[AuthSession]:
        """Update last used time for access token."""
        try:
            auth_session = session.query(self.model).filter(
                and_(
                    self.model.access_token_jti == access_token_jti,
                    self.model.is_deleted == False
                )
            ).first()
            
            if not auth_session:
                return None
            
            now = datetime.now(timezone.utc)
            auth_session.access_token_last_used_at = now
            auth_session.last_activity_at = now
            auth_session.total_requests += 1
            
            if ip_address:
                auth_session.ip_address = ip_address
            
            session.add(auth_session)
            session.flush()
            return auth_session
            
        except Exception as e:
            # Log error but don't fail the request
            return None

    def _check_access_token_valid(self, session: Session, access_token_jti: str) -> Optional[AuthSession]:
        """
        Check if access token is valid.
        Returns session if valid, None otherwise.
        """
        try:
            now = datetime.now(timezone.utc)
            
            auth_session = session.query(self.model).filter(
                and_(
                    self.model.access_token_jti == access_token_jti,
                    self.model.is_revoked == False,
                    self.model.is_deleted == False,
                    self.model.access_token_expires_at > now
                )
            ).first()
            
            return auth_session
            
        except Exception:
            # For security, return None on any error
            return None

    def _check_refresh_token_valid(self, session: Session, refresh_token_jti: str) -> Optional[AuthSession]:
        """
        Check if refresh token is valid.
        Returns session if valid, None otherwise.
        """
        try:
            now = datetime.now(timezone.utc)
            
            auth_session = session.query(self.model).filter(
                and_(
                    self.model.refresh_token_jti == refresh_token_jti,
                    self.model.is_revoked == False,
                    self.model.is_deleted == False,
                    self.model.refresh_token_expires_at > now
                )
            ).first()
            
            return auth_session
            
        except Exception:
            # For security, return None on any error
            return None

    def _get_by_user(self, session: Session, user_id: str, skip: int = 0, limit: int = None) -> List[AuthSession]:
        """Get all sessions for a specific user with pagination."""
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
                self.model.last_activity_at.desc().nullslast(),
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

    def _get_active_sessions_by_user(self, session: Session, user_id: str) -> List[AuthSession]:
        """Get all active (non-revoked, non-expired) sessions for a user."""
        try:
            user_id = validators._validate_id(user_id)
            now = datetime.now(timezone.utc)
            
            sessions = session.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_revoked == False,
                    self.model.is_deleted == False,
                    or_(
                        self.model.access_token_expires_at > now,
                        self.model.refresh_token_expires_at > now
                    )
                )
            ).order_by(
                self.model.last_activity_at.desc().nullslast()
            ).all()
            
            return sessions
            
        except Exception as e:
            context = ErrorContext(operation='get_active_sessions_by_user', component=self.model_name,
                                 additional_info={'user_id': user_id})
            raise DatabaseQueryError(f"Failed to get active {self.model_name} records: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_expired_sessions(self, session: Session, limit: int = 100) -> List[AuthSession]:
        """Get expired sessions for cleanup."""
        try:
            now = datetime.now(timezone.utc)
            
            sessions = session.query(self.model).filter(
                and_(
                    self.model.is_deleted == False,
                    self.model.access_token_expires_at < now,
                    self.model.refresh_token_expires_at < now
                )
            ).order_by(
                self.model.refresh_token_expires_at.asc()
            ).limit(limit).all()
            
            return sessions
            
        except Exception as e:
            context = ErrorContext(operation='get_expired_sessions', component=self.model_name,
                                 additional_info={'limit': limit})
            raise DatabaseQueryError(f"Failed to get expired {self.model_name} records: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _cleanup_expired_sessions(self, session: Session, batch_size: int = 100) -> int:
        """
        Soft delete expired sessions.
        Returns number of sessions deleted.
        """
        try:
            expired = self._get_expired_sessions(session, limit=batch_size)
            
            deleted_count = 0
            for auth_session in expired:
                self._delete(session, auth_session.id)
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            context = ErrorContext(operation='cleanup_expired_sessions', component=self.model_name,
                                 additional_info={'batch_size': batch_size})
            raise DatabaseQueryError(f"Failed to cleanup expired {self.model_name} records: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_sessions_by_device(self, session: Session, user_id: str, device_type: str) -> List[AuthSession]:
        """Get sessions by user and device type."""
        try:
            user_id = validators._validate_id(user_id)
            
            if device_type not in ['mobile', 'desktop', 'tablet', 'api']:
                raise ValueError(f"Invalid device type: {device_type}")
            
            sessions = session.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.device_type == device_type,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.last_activity_at.desc().nullslast()
            ).all()
            
            return sessions
            
        except Exception as e:
            context = ErrorContext(operation='get_sessions_by_device', component=self.model_name,
                                 additional_info={'user_id': user_id, 'device_type': device_type})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by device: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_session_count_by_user(self, session: Session, user_id: str, active_only: bool = False) -> int:
        """Get session count for a user."""
        try:
            user_id = validators._validate_id(user_id)
            
            query = session.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_deleted == False
                )
            )
            
            if active_only:
                now = datetime.now(timezone.utc)
                query = query.filter(
                    and_(
                        self.model.is_revoked == False,
                        or_(
                            self.model.access_token_expires_at > now,
                            self.model.refresh_token_expires_at > now
                        )
                    )
                )
            
            count = query.count()
            return count
            
        except Exception as e:
            context = ErrorContext(operation='get_session_count_by_user', component=self.model_name,
                                 additional_info={'user_id': user_id, 'active_only': active_only})
            raise DatabaseQueryError(f"Failed to count {self.model_name} records: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_sessions_by_country(self, session: Session, country_code: str, limit: int = 100) -> List[AuthSession]:
        """Get sessions from a specific country."""
        try:
            country_code = self._validate_country_code(country_code)
            
            sessions = session.query(self.model).filter(
                and_(
                    self.model.country == country_code,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.last_activity_at.desc().nullslast()
            ).limit(limit).all()
            
            return sessions
            
        except Exception as e:
            context = ErrorContext(operation='get_sessions_by_country', component=self.model_name,
                                 additional_info={'country': country_code, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by country: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

