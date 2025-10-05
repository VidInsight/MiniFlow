import re
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone, timedelta

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import User
from .base_crud import BaseCRUD


class UserCRUD(BaseCRUD[User]):
    def __init__(self):
        super().__init__(User)
        self.model_fields = {column.name for column in User.__table__.columns}
        self.required_fields = {'username', 'hashed_password'}
        self.protected_fields = {'hashed_password', 'failed_login_attempts', 'is_locked', 
                                'last_login_at', 'email_verified_at', 'password_changed_at'}

    # ========================================================================================= VALIDATION HELPERS =====
    def _validate_username(self, username: str) -> str:
        """Validate username format."""
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")

        username = username.strip()

        if len(username) < 3:
            raise ValueError(f"Username too short: {len(username)} chars (min 3)")

        if len(username) > 50:
            raise ValueError(f"Username too long: {len(username)} chars (max 50)")

        # Allow only alphanumeric, underscore, and hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")

        return username

    def _validate_username_uniqueness(self, session: Session, username: str, exclude_id: Optional[str] = None):
        """Validate that username is unique."""
        query = session.query(self.model).filter(
            and_(
                self.model.username == username,
                self.model.is_deleted == False
            )
        )

        if exclude_id:
            query = query.filter(self.model.id != exclude_id)

        existing = query.first()

        if existing:
            context = ErrorContext(operation='validate_username_uniqueness', component=self.model_name,additional_info={'username': username, 'existing_id': existing.id})
            raise ValidationError(f"Username '{username}' already exists", context=context, severity=ErrorSeverity.HIGH)

    def _validate_email(self, email: str) -> str:
        """Validate email format."""
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")

        email = email.strip().lower()

        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError(f"Invalid email format: {email}")

        return email

    def _validate_email_uniqueness(self, session: Session, email: str, exclude_id: Optional[str] = None):
        """Validate that email is unique."""
        query = session.query(self.model).filter(
            and_(
                self.model.email == email,
                self.model.is_deleted == False
            )
        )

        if exclude_id:
            query = query.filter(self.model.id != exclude_id)

        existing = query.first()

        if existing:
            context = ErrorContext(operation='validate_email_uniqueness', component=self.model_name,
                                   additional_info={'email': email, 'existing_id': existing.id})
            raise ValidationError(f"Email '{email}' already exists",
                                  context=context, severity=ErrorSeverity.HIGH)

    def _validate_phone(self, country_code: Optional[str], phone_number: Optional[str]):
        """Validate phone number format."""
        if (country_code and not phone_number) or (phone_number and not country_code):
            raise ValueError("Both country_code and phone_number must be provided together")

        if country_code:
            if not isinstance(country_code, str) or len(country_code) != 2:
                raise ValueError("Country code must be a 2-character string (ISO 3166-1 alpha-2)")

        if phone_number:
            if not isinstance(phone_number, str):
                raise ValueError("Phone number must be a string")

            # Remove common separators
            import re
            cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)

            if not cleaned.isdigit():
                raise ValueError("Phone number can only contain digits and separators")

            if len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError(f"Phone number length invalid: {len(cleaned)} digits (min 7, max 15)")

    def _validate_phone_uniqueness(self, session: Session, country_code: Optional[str], phone_number: Optional[str], exclude_id: Optional[str] = None):
        """Validate that phone number combination is unique."""
        if not country_code or not phone_number:
            return  # Skip if phone is not provided

        query = session.query(self.model).filter(
            and_(
                self.model.country_code == country_code,
                self.model.phone_number == phone_number,
                self.model.is_deleted == False
            )
        )

        if exclude_id:
            query = query.filter(self.model.id != exclude_id)

        existing = query.first()

        if existing:
            context = ErrorContext(operation='validate_phone_uniqueness', component=self.model_name,
                                   additional_info={
                                       'country_code': country_code,
                                       'phone_number': phone_number,
                                       'existing_id': existing.id
                                   })
            raise ValidationError(f"Phone number {country_code} {phone_number} already exists",
                                  context=context, severity=ErrorSeverity.HIGH)

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> User:
        """Create a new user with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate username
        username = kwargs.get('username')
        if username:
            username = self._validate_username(username)
            # Check uniqueness
            self._validate_username_uniqueness(session, username)
            kwargs['username'] = username
        
        # Validate email if provided
        email = kwargs.get('email')
        if email:
            email = self._validate_email(email)
            # Check uniqueness
            self._validate_email_uniqueness(session, email)
            kwargs['email'] = email
        
        # Validate phone if provided
        country_code = kwargs.get('country_code')
        phone_number = kwargs.get('phone_number')
        if country_code or phone_number:
            self._validate_phone(country_code, phone_number)
            # Check uniqueness
            self._validate_phone_uniqueness(session, country_code, phone_number)
        
        # Validate hashed_password
        hashed_password = kwargs.get('hashed_password')
        if hashed_password and not isinstance(hashed_password, str):
            raise ValueError("Hashed password must be a string")
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        user = super()._create(session, **kwargs)
        return user

    def _update(self, session: Session, record_id: str, **kwargs) -> User:
        """Update user with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Get existing user
        existing = self._get_by_id(session, record_id)
        if not existing:
            context = ErrorContext(operation='update', component=self.model_name,
                                 additional_info={'record_id': record_id})
            raise ValidationError(f"{self.model_name} with ID {record_id} not found",
                                context=context, severity=ErrorSeverity.MEDIUM)
        
        # Validate username if being updated
        if 'username' in kwargs and kwargs['username']:
            username = self._validate_username(kwargs['username'])
            # Check uniqueness (excluding current user)
            self._validate_username_uniqueness(session, username, exclude_id=record_id)
            kwargs['username'] = username
        
        # Validate email if being updated
        if 'email' in kwargs and kwargs['email']:
            email = self._validate_email(kwargs['email'])
            # Check uniqueness (excluding current user)
            self._validate_email_uniqueness(session, email, exclude_id=record_id)
            kwargs['email'] = email
        
        # Validate phone if being updated
        if 'country_code' in kwargs or 'phone_number' in kwargs:
            country_code = kwargs.get('country_code', existing.country_code)
            phone_number = kwargs.get('phone_number', existing.phone_number)
            if country_code or phone_number:
                self._validate_phone(country_code, phone_number)
                # Check uniqueness (excluding current user)
                self._validate_phone_uniqueness(session, country_code, phone_number, exclude_id=record_id)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        user = super()._update(session, record_id, **kwargs)
        return user

    # =================================================================================== ORCHESTRATION OPERATIONS =====
    def _activate(self, session: Session, record_id: str) -> User:
        """Activate user account."""
        return self._update(session, record_id, is_active=True)

    def _deactivate(self, session: Session, record_id: str) -> User:
        """Deactivate user account."""
        return self._update(session, record_id, is_active=False)

    def _lock_account(self, session: Session, record_id: str, reason: Optional[str] = None) -> User:
        """Lock user account."""
        user = self._get_by_id(session, record_id)
        if not user:
            self._raise_not_found_error(operation='lock_account', component=self.model_name,)
        
        user.is_locked = True
        session.add(user)
        session.flush()
        return user

    def _unlock_account(self, session: Session, record_id: str) -> User:
        """Unlock user account and reset failed login attempts."""
        user = self._get_by_id(session, record_id)
        if not user:
            self._raise_not_found_error(operation='unlock_account', component=self.model_name,)
        
        user.is_locked = False
        user.failed_login_attempts = 0
        session.add(user)
        session.flush()
        return user