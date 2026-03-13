"""
Unit tests for Auth Service
"""

import pytest
from bot.auth import AuthService


class TestAuthService:
    """Test suite for AuthService"""
    
    def test_successful_owner_authorization(self):
        """Test successful authorization of the owner"""
        owner_id = 12345
        auth_service = AuthService(owner_id=owner_id)
        
        assert auth_service.is_owner(owner_id) is True
    
    def test_reject_unauthorized_user(self):
        """Test rejection of unauthorized user"""
        owner_id = 12345
        unauthorized_id = 67890
        auth_service = AuthService(owner_id=owner_id)
        
        assert auth_service.is_owner(unauthorized_id) is False
    
    def test_reject_zero_user_id(self):
        """Test rejection of zero user ID"""
        owner_id = 12345
        auth_service = AuthService(owner_id=owner_id)
        
        assert auth_service.is_owner(0) is False
    
    def test_reject_negative_user_id(self):
        """Test rejection of negative user ID"""
        owner_id = 12345
        auth_service = AuthService(owner_id=owner_id)
        
        assert auth_service.is_owner(-1) is False
