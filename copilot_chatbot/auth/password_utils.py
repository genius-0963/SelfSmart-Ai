"""
Password utilities for authentication
"""

from passlib.context import CryptContext
from typing import Optional
import re

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Validate password strength and return feedback
        Returns a dict with 'is_valid' and 'errors' keys
        """
        errors = []
        
        # Minimum length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Maximum length
        if len(password) > 128:
            errors.append("Password must be less than 128 characters long")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        common_patterns = [
            'password', '123456', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_patterns:
            errors.append("Password is too common and easily guessable")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'strength_score': PasswordUtils._calculate_strength_score(password)
        }
    
    @staticmethod
    def _calculate_strength_score(password: str) -> int:
        """
        Calculate password strength score (0-100)
        """
        score = 0
        
        # Length contribution (up to 40 points)
        length_score = min(len(password) * 2, 40)
        score += length_score
        
        # Character variety (up to 40 points)
        if re.search(r'[a-z]', password):
            score += 8
        if re.search(r'[A-Z]', password):
            score += 8
        if re.search(r'\d', password):
            score += 8
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 8
        if re.search(r'[^a-zA-Z0-9!@#$%^&*(),.?":{}|<>]', password):
            score += 8
        
        # Complexity bonus (up to 20 points)
        unique_chars = len(set(password))
        complexity_score = min(unique_chars * 2, 20)
        score += complexity_score
        
        return min(score, 100)

    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """
        Generate a secure random password
        """
        import secrets
        import string
        
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*(),.?":{}|<>'
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)

    @staticmethod
    def check_password_breached(password: str) -> bool:
        """
        Check if password has been breached (simplified version)
        In production, integrate with HaveIBeenPwned API
        """
        # This is a simplified check - in production, use the actual HIBP API
        common_breached_passwords = {
            '123456', 'password', '123456789', '12345678', '12345',
            '1234567', '1234567890', '1234', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            '1234567890', 'password1', 'qwerty123', 'iloveyou',
            'princess', 'admin123', 'welcome123', 'monkey123'
        }
        
        return password.lower() in common_breached_passwords
