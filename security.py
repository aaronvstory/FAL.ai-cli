#!/usr/bin/env python3
"""
Security utilities for FAL.AI Video Generator
Handles input validation, sanitization, and secure configuration
"""

import os
import re
import logging
import hashlib
import secrets
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
import validators
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SecurityRateLimiter:
    """Advanced rate limiting with memory cleanup"""
    
    def __init__(self, cleanup_interval: int = 300):
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = defaultdict(float)
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        
    def is_rate_limited(self, identifier: str, max_requests: int, window: int) -> bool:
        """Check if identifier is rate limited"""
        current_time = time.time()
        
        # Clean up old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup(current_time)
            
        # Check if IP is temporarily blocked
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier]:
                return True
            else:
                del self.blocked_ips[identifier]
        
        # Clean old requests outside window
        request_times = self.requests[identifier]
        while request_times and current_time - request_times[0] > window:
            request_times.popleft()
            
        # Check rate limit
        if len(request_times) >= max_requests:
            # Block IP for 5 minutes after exceeding limit
            self.blocked_ips[identifier] = current_time + 300
            return True
            
        # Record this request
        request_times.append(current_time)
        return False
        
    def _cleanup(self, current_time: float):
        """Clean up old entries to prevent memory leaks"""
        # Remove old request records
        for identifier in list(self.requests.keys()):
            request_times = self.requests[identifier]
            while request_times and current_time - request_times[0] > 3600:  # 1 hour
                request_times.popleft()
            if not request_times:
                del self.requests[identifier]
                
        # Remove expired blocks
        expired_blocks = [ip for ip, expire_time in self.blocked_ips.items() 
                         if current_time >= expire_time]
        for ip in expired_blocks:
            del self.blocked_ips[ip]
            
        self.last_cleanup = current_time


class InputValidator:
    """Enhanced input validation and sanitization utilities"""
    
    # File path validation patterns
    SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\./\\: ]+$')
    
    # Enhanced dangerous patterns for prompts
    DANGEROUS_PATTERNS = [
        r'<script.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'eval\(',
        r'exec\(',
        r'import\s+os',
        r'import\s+subprocess',
        r'__import__',
        r'\${.*}',  # Template injection
        r'\{\{.*\}\}',  # Template injection
        r'<\?php.*\?>',  # PHP injection
        r'<%.*%>',  # ASP/JSP injection
        r'UNION\s+SELECT',  # SQL injection
        r'DROP\s+TABLE',  # SQL injection
        r'/\*.*\*/',  # SQL comments
        r'--.*',  # SQL comments
    ]
    
    PROMPT_BLACKLIST = re.compile('|'.join(DANGEROUS_PATTERNS), re.IGNORECASE)
    
    # File type validation
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/bmp', 'image/tiff'
    }
    
    MAGIC_NUMBERS = {
        b'\xff\xd8\xff': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'RIFF': 'image/webp',  # Needs additional validation
        b'BM': 'image/bmp',
    }
    
    @classmethod
    def validate_file_path(cls, path: str) -> bool:
        """Enhanced file path security validation"""
        if not path or len(path) > 1000:  # Reasonable length limit
            return False
            
        # Normalize path to detect traversal attempts
        normalized = os.path.normpath(path)
        
        # Check for path traversal attempts
        if '..' in normalized or normalized.startswith('/') and not normalized.startswith('/tmp/'):
            return False
            
        # Additional security checks
        dangerous_patterns = ['/etc/', '/proc/', '/sys/', '/dev/', '/root/', '/home/']
        if any(dangerous in normalized.lower() for dangerous in dangerous_patterns):
            return False
            
        # Validate characters
        if not cls.SAFE_PATH_PATTERN.match(path):
            return False
            
        return True
    
    @classmethod
    def sanitize_file_path(cls, path: str) -> Optional[str]:
        """Sanitize and validate file path"""
        if not path:
            return None
            
        # Basic sanitization
        path = path.strip()
        path = os.path.normpath(path)
        
        # Validate
        if not cls.validate_file_path(path):
            logger.warning(f"Invalid file path rejected: {path}")
            return None
            
        # Check if file exists
        if not Path(path).exists():
            logger.warning(f"File not found: {path}")
            return None
            
        return path
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> bool:
        """Enhanced prompt validation for dangerous content"""
        if not prompt or len(prompt) > 2000:  # Stricter length limit
            return False
            
        # Check for dangerous patterns
        if cls.PROMPT_BLACKLIST.search(prompt):
            return False
            
        # Additional checks for suspicious patterns
        suspicious_chars = ['<', '>', '{', '}', '$', '%', ';', '|', '&']
        if sum(prompt.count(char) for char in suspicious_chars) > 10:
            return False
            
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in prompt if not c.isalnum() and c not in ' .,!?-') / len(prompt)
        if special_char_ratio > 0.3:  # More than 30% special chars
            return False
            
        return True
    
    @classmethod
    def sanitize_prompt(cls, prompt: str) -> Optional[str]:
        """Sanitize prompt text"""
        if not prompt:
            return None
            
        # Basic sanitization
        prompt = prompt.strip()
        
        # Validate
        if not cls.validate_prompt(prompt):
            logger.warning("Dangerous prompt content detected and rejected")
            return None
            
        return prompt
    
    @classmethod
    def validate_duration(cls, duration: Any) -> Optional[int]:
        """Validate and sanitize duration input"""
        if duration is None:
            return None
            
        try:
            duration = int(duration)
            if 1 <= duration <= 60:  # Reasonable duration limits
                return duration
        except (ValueError, TypeError):
            pass
            
        logger.warning(f"Invalid duration: {duration}")
        return None
    
    @classmethod
    def validate_aspect_ratio(cls, ratio: str) -> Optional[str]:
        """Validate aspect ratio format"""
        if not ratio:
            return None
            
        ratio = ratio.strip()
        
        # Valid aspect ratios for video generation
        valid_ratios = [
            "1:1", "4:3", "3:4", "16:9", "9:16", 
            "21:9", "9:21", "2:3", "3:2"
        ]
        
        if ratio in valid_ratios:
            return ratio
            
        logger.warning(f"Invalid aspect ratio: {ratio}")
        return None
    
    @classmethod
    def validate_cfg_scale(cls, scale: Any) -> Optional[float]:
        """Validate CFG scale parameter"""
        if scale is None:
            return None
            
        try:
            scale = float(scale)
            if 0.0 <= scale <= 1.0:
                return scale
        except (ValueError, TypeError):
            pass
            
        logger.warning(f"Invalid CFG scale: {scale}")
        return None
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Enhanced URL validation with security checks"""
        if not url or len(url) > 2000:
            return False
            
        # Basic URL validation
        if not validators.url(url):
            return False
            
        # Additional security checks
        parsed_url = url.lower()
        
        # Block local/private addresses
        blocked_patterns = [
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
            '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
            'file://', 'ftp://', 'ftps://'
        ]
        
        if any(pattern in parsed_url for pattern in blocked_patterns):
            return False
            
        # Must be HTTPS in production
        if os.getenv('PRODUCTION', 'false').lower() == 'true' and not parsed_url.startswith('https://'):
            return False
            
        return True
    
    @classmethod
    def validate_file_content(cls, content: bytes, declared_type: str) -> bool:
        """Validate file content matches declared type using magic numbers"""
        if not content or len(content) < 8:
            return False
            
        # Check magic numbers
        for magic, file_type in cls.MAGIC_NUMBERS.items():
            if content.startswith(magic):
                if file_type == declared_type:
                    return True
                if file_type == 'image/webp' and declared_type == 'image/webp':
                    # Additional WebP validation
                    return b'WEBP' in content[:12]
                    
        return False
    
    @classmethod
    def generate_secure_filename(cls, original_filename: str, user_id: str = None) -> str:
        """Generate secure filename with hash"""
        # Extract extension safely
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', original_filename)
        name, ext = os.path.splitext(safe_name)
        
        # Generate unique hash
        timestamp = str(int(time.time()))
        user_part = user_id or 'anonymous'
        hash_input = f"{name}{timestamp}{user_part}{secrets.token_hex(8)}"
        file_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        return f"{file_hash}{ext.lower()}"


class SecureConfig:
    """Secure configuration management"""
    
    def __init__(self, config_path: str = "./config/settings.json"):
        self.config_path = Path(config_path)
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_path = Path("./.encryption_key")
        
        if key_path.exists():
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            # Make key file read-only
            os.chmod(key_path, 0o600)
            return key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def get_api_key_secure(self) -> Optional[str]:
        """Get API key from secure sources"""
        # Priority: Environment variable > encrypted config > user input
        
        # 1. Try environment variable
        api_key = os.getenv("FAL_KEY")
        if api_key:
            logger.info("API key loaded from environment variable")
            return api_key
        
        # 2. Try encrypted config file
        encrypted_key_path = Path("./config/encrypted_api_key")
        if encrypted_key_path.exists():
            try:
                with open(encrypted_key_path, 'r') as f:
                    encrypted_key = f.read()
                api_key = self.decrypt_sensitive_data(encrypted_key)
                logger.info("API key loaded from encrypted storage")
                return api_key
            except Exception as e:
                logger.error(f"Failed to decrypt API key: {e}")
        
        # 3. Prompt user and store securely
        while True:
            api_key = input("Enter your FAL API key (will be stored securely): ").strip()
            
            if not api_key:
                print("API key is required to continue.")
                continue
                
            # Basic validation
            if len(api_key) < 10 or not re.match(r'^[a-zA-Z0-9\-:_]+$', api_key):
                print("Invalid API key format. Please check and try again.")
                continue
                
            # Store encrypted
            try:
                encrypted_key = self.encrypt_sensitive_data(api_key)
                encrypted_key_path.parent.mkdir(parents=True, exist_ok=True)
                with open(encrypted_key_path, 'w') as f:
                    f.write(encrypted_key)
                os.chmod(encrypted_key_path, 0o600)
                logger.info("API key stored securely")
                return api_key
            except Exception as e:
                logger.error(f"Failed to store API key securely: {e}")
                return api_key  # Return but don't store if encryption fails


class SecurityManager:
    """Enhanced central security management"""
    
    def __init__(self):
        self.validator = InputValidator()
        self.config = SecureConfig()
        self.rate_limiter = SecurityRateLimiter()
        self.failed_attempts = defaultdict(int)
        self.last_failed_attempt = defaultdict(float)
        
    def check_rate_limit(self, identifier: str, max_requests: int = 60, window: int = 60) -> bool:
        """Check if request should be rate limited"""
        return self.rate_limiter.is_rate_limited(identifier, max_requests, window)
        
    def log_failed_attempt(self, identifier: str):
        """Log failed authentication/validation attempt"""
        current_time = time.time()
        
        # Reset counter if more than 1 hour since last attempt
        if current_time - self.last_failed_attempt[identifier] > 3600:
            self.failed_attempts[identifier] = 0
            
        self.failed_attempts[identifier] += 1
        self.last_failed_attempt[identifier] = current_time
        
        # Log suspicious activity
        if self.failed_attempts[identifier] > 5:
            logger.warning(f"Multiple failed attempts from {identifier}: {self.failed_attempts[identifier]}")
            
    def is_suspicious_activity(self, identifier: str) -> bool:
        """Check if identifier shows suspicious activity patterns"""
        return self.failed_attempts.get(identifier, 0) > 10
        
    def validate_and_sanitize_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize all inputs"""
        validated = {}
        
        # Enhanced file path validation
        if 'image_path' in kwargs:
            validated['image_path'] = self.validator.sanitize_file_path(kwargs['image_path'])
            if validated['image_path'] is None:
                self.log_failed_attempt("file_validation")
                raise ValueError("Invalid or missing image file")
                
            # Additional file content validation if available
            if 'file_content' in kwargs and 'content_type' in kwargs:
                if not self.validator.validate_file_content(kwargs['file_content'], kwargs['content_type']):
                    self.log_failed_attempt("file_content")
                    raise ValueError("File content does not match declared type")
                
        if 'tail_image_path' in kwargs and kwargs['tail_image_path']:
            validated['tail_image_path'] = self.validator.sanitize_file_path(kwargs['tail_image_path'])
            if validated['tail_image_path'] is None:
                raise ValueError("Invalid tail image file")
        
        # Enhanced prompt validation
        if 'prompt' in kwargs:
            validated['prompt'] = self.validator.sanitize_prompt(kwargs['prompt'])
            if validated['prompt'] is None:
                self.log_failed_attempt("prompt_validation")
                raise ValueError("Invalid or dangerous prompt content")
                
            # Additional prompt security checks
            if len(validated['prompt']) < 10:
                raise ValueError("Prompt too short (minimum 10 characters)")
                
            # Check for repetitive patterns (potential spam)
            words = validated['prompt'].split()
            if len(set(words)) < len(words) * 0.5:  # Less than 50% unique words
                self.log_failed_attempt("prompt_spam")
                raise ValueError("Prompt appears to be spam or repetitive")
        
        if 'negative_prompt' in kwargs and kwargs['negative_prompt']:
            validated['negative_prompt'] = self.validator.sanitize_prompt(kwargs['negative_prompt'])
            if validated['negative_prompt'] is None:
                raise ValueError("Invalid negative prompt content")
        
        # Numeric validation
        if 'duration' in kwargs:
            validated['duration'] = self.validator.validate_duration(kwargs['duration'])
            if validated['duration'] is None:
                raise ValueError("Invalid duration (must be 1-60 seconds)")
        
        if 'cfg_scale' in kwargs and kwargs['cfg_scale'] is not None:
            validated['cfg_scale'] = self.validator.validate_cfg_scale(kwargs['cfg_scale'])
            if validated['cfg_scale'] is None:
                raise ValueError("Invalid CFG scale (must be 0.0-1.0)")
        
        # Aspect ratio validation
        if 'aspect_ratio' in kwargs:
            validated['aspect_ratio'] = self.validator.validate_aspect_ratio(kwargs['aspect_ratio'])
            if validated['aspect_ratio'] is None:
                raise ValueError("Invalid aspect ratio")
        
        # Log successful validation
        logger.info(f"Successfully validated inputs: {list(validated.keys())}")
        return validated
    
    def get_secure_api_key(self) -> str:
        """Get API key securely"""
        api_key = self.config.get_api_key_secure()
        if not api_key:
            raise ValueError("API key is required")
        return api_key


# Global security manager instance
security_manager = SecurityManager()