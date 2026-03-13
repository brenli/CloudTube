"""
Property-based tests for Auth Service
"""

import pytest
from hypothesis import given, strategies as st
from bot.auth import AuthService


class TestAuthServiceProperties:
    """Property-based tests for AuthService"""
    
    # Feature: youtube-webdav-bot, Property 1: Отклонение неавторизованных пользователей
    @given(
        owner_id=st.integers(min_value=1, max_value=999999999),
        unauthorized_id=st.integers(min_value=1, max_value=999999999)
    )
    def test_reject_unauthorized_users(self, owner_id: int, unauthorized_id: int):
        """
        **Validates: Requirements 1.2**
        
        Для любого пользователя с Telegram ID, отличным от ID владельца,
        is_owner() должен возвращать False
        """
        # Skip if IDs are the same (this would be the owner)
        if owner_id == unauthorized_id:
            return
        
        auth_service = AuthService(owner_id=owner_id)
        
        # Any user ID different from owner_id should be rejected
        assert auth_service.is_owner(unauthorized_id) is False
    
    @given(owner_id=st.integers(min_value=1, max_value=999999999))
    def test_owner_always_authorized(self, owner_id: int):
        """
        **Validates: Requirements 1.3**
        
        Для любого владельца с валидным Telegram ID,
        is_owner() должен возвращать True для его ID
        """
        auth_service = AuthService(owner_id=owner_id)
        
        # Owner should always be authorized
        assert auth_service.is_owner(owner_id) is True
