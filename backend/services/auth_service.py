import jwt
import bcrypt
import redis
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from functools import wraps
from collections import defaultdict
import time
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class AuthService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_hours = int(os.getenv("JWT_EXPIRATION", "24"))
        
        # Rate limiting configuration
        self.rate_limits = {
            'login': {'max_attempts': 5, 'window_minutes': 15},
            'register': {'max_attempts': 3, 'window_minutes': 60},
            'api': {'max_requests': 100, 'window_minutes': 1}
        }
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established for AuthService")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _get_rate_limit_key(self, action: str, identifier: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{action}:{identifier}"
    
    def _check_rate_limit(self, action: str, identifier: str) -> bool:
        """Check if rate limit is exceeded"""
        if not self.redis_client:
            return True  # Allow if Redis is not available
        
        try:
            limit_config = self.rate_limits.get(action, {'max_attempts': 10, 'window_minutes': 1})
            key = self._get_rate_limit_key(action, identifier)
            current_time = time.time()
            window_seconds = limit_config['window_minutes'] * 60
            
            # Get current attempts
            attempts = self.redis_client.zrangebyscore(key, current_time - window_seconds, current_time)
            
            if len(attempts) >= limit_config['max_attempts']:
                logger.warning(f"Rate limit exceeded for {action} by {identifier}")
                return False
            
            # Add current attempt
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, window_seconds)
            
            return True
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow if error occurs
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return text
        
        # Remove potentially dangerous characters
        text = text.replace("'", "").replace('"', "").replace(";", "").replace("--", "")
        text = text.replace("<script>", "").replace("</script>", "")
        text = text.replace("javascript:", "").replace("onerror=", "").replace("onload=", "")
        
        return text.strip()
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user with validation and rate limiting"""
        try:
            # Check rate limit
            if not self._check_rate_limit('register', username):
                return {"success": False, "error": "Registration rate limit exceeded"}
            
            # Sanitize inputs
            username = self._sanitize_input(username)
            email = self._sanitize_input(email)
            
            # Validate inputs
            if not username or len(username) < 3:
                return {"success": False, "error": "Username must be at least 3 characters"}
            
            if not email or '@' not in email:
                return {"success": False, "error": "Invalid email address"}
            
            if not password or len(password) < 8:
                return {"success": False, "error": "Password must be at least 8 characters"}
            
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Here you would typically save to database
            # For now, we'll simulate user creation
            user_id = f"user_{int(time.time())}"
            user = User(
                id=user_id,
                username=username,
                email=email,
                is_active=True,
                created_at=datetime.now()
            )
            
            # Store user data (in production, this would be in database)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': hashed_password,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat()
            }
            
            if self.redis_client:
                self.redis_client.setex(
                    f"user:{user.id}",
                    3600,  # 1 hour TTL
                    str(user_data)
                )
            
            logger.info(f"User registered: {username}")
            return {"success": True, "user": user_data}
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "error": "Registration failed"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login user with rate limiting and JWT token generation"""
        try:
            # Check rate limit
            if not self._check_rate_limit('login', username):
                return {"success": False, "error": "Login rate limit exceeded"}
            
            # Sanitize inputs
            username = self._sanitize_input(username)
            
            # Get user data (in production, this would be from database)
            if not self.redis_client:
                return {"success": False, "error": "Authentication service unavailable"}
            
            # Find user by username
            user_keys = self.redis_client.keys("user:*")
            user_data = None
            
            for key in user_keys:
                stored_data = self.redis_client.get(key)
                if stored_data and username in stored_data:
                    user_data = eval(stored_data)  # In production, use proper JSON parsing
                    break
            
            if not user_data:
                return {"success": False, "error": "Invalid credentials"}
            
            # Verify password
            if not self._verify_password(password, user_data['password_hash']):
                return {"success": False, "error": "Invalid credentials"}
            
            # Check if user is active
            if not user_data.get('is_active', True):
                return {"success": False, "error": "Account is deactivated"}
            
            # Generate JWT token
            token = self._generate_token(user_data['id'], user_data['username'])
            
            # Update last login
            user_data['last_login'] = datetime.now().isoformat()
            self.redis_client.setex(
                f"user:{user_data['id']}",
                3600,
                str(user_data)
            )
            
            logger.info(f"User logged in: {username}")
            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user_data['id'],
                    "username": user_data['username'],
                    "email": user_data['email']
                }
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "error": "Login failed"}
    
    def _generate_token(self, user_id: str, username: str) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh JWT token"""
        try:
            payload = self.verify_token(token)
            if payload:
                # Generate new token with extended expiration
                return self._generate_token(payload['user_id'], payload['username'])
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
        return None
    
    def logout_user(self, token: str) -> bool:
        """Logout user by blacklisting token"""
        try:
            if self.redis_client:
                # Add token to blacklist
                self.redis_client.setex(
                    f"blacklist:{token}",
                    self.expiration_hours * 3600,  # Same as token expiration
                    "blacklisted"
                )
                logger.info("User logged out")
                return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
        return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"blacklist:{token}") > 0
        except Exception as e:
            logger.error(f"Blacklist check error: {e}")
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            if not self.redis_client:
                return None
            
            user_data = self.redis_client.get(f"user:{user_id}")
            if user_data:
                data = eval(user_data)  # In production, use proper JSON parsing
                return User(
                    id=data['id'],
                    username=data['username'],
                    email=data['email'],
                    is_active=data.get('is_active', True),
                    created_at=datetime.fromisoformat(data['created_at']),
                    last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
                )
        except Exception as e:
            logger.error(f"Get user error: {e}")
        return None
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user information"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Update allowed fields
            allowed_fields = ['email', 'is_active']
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    user_data[field] = value
            
            if self.redis_client:
                self.redis_client.setex(
                    f"user:{user_id}",
                    3600,
                    str(user_data)
                )
            
            logger.info(f"Updated user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Update user error: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user_data = self.redis_client.get(f"user:{user_id}")
            if not user_data:
                return False
            
            data = eval(user_data)
            
            # Verify old password
            if not self._verify_password(old_password, data['password_hash']):
                return False
            
            # Hash new password
            new_hash = self._hash_password(new_password)
            data['password_hash'] = new_hash
            
            # Update user data
            self.redis_client.setex(
                f"user:{user_id}",
                3600,
                str(data)
            )
            
            logger.info(f"Password changed for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Change password error: {e}")
            return False
    
    def get_rate_limit_info(self, action: str, identifier: str) -> Dict[str, Any]:
        """Get rate limit information for monitoring"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            limit_config = self.rate_limits.get(action, {})
            key = self._get_rate_limit_key(action, identifier)
            current_time = time.time()
            window_seconds = limit_config.get('window_minutes', 1) * 60
            
            attempts = self.redis_client.zrangebyscore(key, current_time - window_seconds, current_time)
            
            return {
                "action": action,
                "identifier": identifier,
                "current_attempts": len(attempts),
                "max_attempts": limit_config.get('max_attempts', 10),
                "window_minutes": limit_config.get('window_minutes', 1),
                "remaining_attempts": max(0, limit_config.get('max_attempts', 10) - len(attempts))
            }
        except Exception as e:
            logger.error(f"Rate limit info error: {e}")
            return {"error": str(e)}
    
    def clear_rate_limits(self, action: str, identifier: str) -> bool:
        """Clear rate limits for testing purposes"""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_rate_limit_key(action, identifier)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Clear rate limits error: {e}")
            return False

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This would be implemented in the FastAPI dependency injection
        # For now, it's a placeholder
        return f(*args, **kwargs)
    return decorated_function

def require_rate_limit(action: str):
    """Decorator to require rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented in the FastAPI dependency injection
            # For now, it's a placeholder
            return f(*args, **kwargs)
        return decorated_function
    return decorator 