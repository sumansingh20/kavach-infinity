"""
KAVACH-INFINITY Security Module
JWT Authentication, Password Hashing, RBAC
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import hashlib
import secrets

from jose import jwt, JWTError
from passlib.context import CryptContext
import structlog

from app.config import settings
from app.models.schemas import UserRole

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Password hashing utilities"""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password needs rehashing"""
        return pwd_context.needs_update(hashed_password)


class TokenManager:
    """JWT Token management"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_hex(16)  # Unique token ID
        })
        
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning("Token decode failed", error=str(e))
            return None
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()


class RBACManager:
    """Role-Based Access Control"""
    
    # Permission definitions
    PERMISSIONS = {
        UserRole.SUPER_ADMIN: {
            "users": ["create", "read", "update", "delete", "manage_roles"],
            "sites": ["create", "read", "update", "delete", "configure"],
            "sensors": ["create", "read", "update", "delete", "configure"],
            "alerts": ["create", "read", "update", "delete", "acknowledge", "resolve", "assign"],
            "reports": ["create", "read", "export"],
            "settings": ["read", "update"],
            "audit": ["read", "export"],
            "safety": ["override", "emergency_stop"],
            "ai": ["train", "deploy", "configure"]
        },
        UserRole.ADMIN: {
            "users": ["create", "read", "update"],
            "sites": ["create", "read", "update", "configure"],
            "sensors": ["create", "read", "update", "configure"],
            "alerts": ["read", "update", "acknowledge", "resolve", "assign"],
            "reports": ["create", "read", "export"],
            "settings": ["read", "update"],
            "audit": ["read"],
            "safety": ["emergency_stop"],
            "ai": ["configure"]
        },
        UserRole.OPERATOR: {
            "sites": ["read"],
            "sensors": ["read", "update"],
            "alerts": ["read", "acknowledge", "resolve"],
            "reports": ["read"],
            "safety": ["emergency_stop"]
        },
        UserRole.ANALYST: {
            "sites": ["read"],
            "sensors": ["read"],
            "alerts": ["read"],
            "reports": ["create", "read", "export"],
            "audit": ["read"]
        },
        UserRole.VIEWER: {
            "sites": ["read"],
            "sensors": ["read"],
            "alerts": ["read"],
            "reports": ["read"]
        }
    }
    
    @classmethod
    def has_permission(
        cls,
        role: UserRole,
        resource: str,
        action: str
    ) -> bool:
        """Check if role has permission for action on resource"""
        role_perms = cls.PERMISSIONS.get(role, {})
        resource_perms = role_perms.get(resource, [])
        return action in resource_perms
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> Dict[str, List[str]]:
        """Get all permissions for a role"""
        return cls.PERMISSIONS.get(role, {})
    
    @classmethod
    def can_access_site(cls, role: UserRole, site_id: UUID) -> bool:
        """Check if role can access specific site"""
        # For now, all authenticated users can access all sites
        # In production, implement site-based access control
        return cls.has_permission(role, "sites", "read")
    
    @classmethod
    def can_perform_safety_action(cls, role: UserRole, action: str) -> bool:
        """Check if role can perform safety-critical action"""
        return cls.has_permission(role, "safety", action)


class SecurityUtils:
    """General security utilities"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate API key for external integrations"""
        return f"kavach_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def generate_mfa_secret() -> str:
        """Generate MFA secret for TOTP"""
        import base64
        return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')
    
    @staticmethod
    def verify_mfa_code(secret: str, code: str) -> bool:
        """Verify TOTP MFA code"""
        # Simplified - in production use pyotp
        import hmac
        import time
        
        # This is a placeholder - use pyotp in production
        return len(code) == 6 and code.isdigit()
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input to prevent injection"""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
        result = input_str
        for char in dangerous_chars:
            result = result.replace(char, '')
        return result.strip()
    
    @staticmethod
    def generate_confirmation_code() -> str:
        """Generate confirmation code for safety overrides"""
        return secrets.token_hex(3).upper()  # 6 character hex code


# Export instances
password_hasher = PasswordHasher()
token_manager = TokenManager()
rbac = RBACManager()
security_utils = SecurityUtils()
