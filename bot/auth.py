"""
Authentication service for the bot
"""


class AuthService:
    """Handles authentication and authorization"""
    
    def __init__(self, owner_id: int):
        """
        Initialize AuthService with owner ID
        
        Args:
            owner_id: Telegram user ID of the bot owner
        """
        self.owner_id = owner_id
    
    def is_owner(self, user_id: int) -> bool:
        """
        Check if a user is the bot owner
        
        Args:
            user_id: Telegram user ID to check
            
        Returns:
            True if user is the owner, False otherwise
        """
        return user_id == self.owner_id
