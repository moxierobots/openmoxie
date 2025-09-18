"""
Claude AI Service for OpenMoxie

This module provides integration with Anthropic's Claude API for AI conversations
similar to the OpenAI integration. It includes conversation management, response
generation, and error handling specific to Claude.
"""

import logging
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
from anthropic.types import Message
from .ai_factory import create_claude, get_claude_model

logger = logging.getLogger(__name__)


class ClaudeConversationError(Exception):
    """Custom exception for Claude conversation errors"""
    pass


class ClaudeService:
    """Service class for managing Claude AI conversations"""
    
    def __init__(self):
        self.client = None
        self.model = get_claude_model()
        self.max_tokens = 4000  # Default max tokens for responses
        self.temperature = 0.7  # Default temperature
        
    def initialize(self):
        """Initialize the Claude client"""
        try:
            self.client = create_claude()
            logger.info("Claude service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude service: {e}")
            raise ClaudeConversationError(f"Claude initialization failed: {e}")
    
    def create_conversation(self, 
                          system_prompt: str,
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Create a new conversation context with system prompt
        
        Args:
            system_prompt: System message to set conversation context
            max_tokens: Maximum tokens for responses (optional)
            temperature: Response randomness (0-1, optional)
            
        Returns:
            Dict containing conversation metadata
        """
        return {
            'system_prompt': system_prompt,
            'messages': [],
            'max_tokens': max_tokens or self.max_tokens,
            'temperature': temperature or self.temperature,
            'model': self.model
        }
    
    def add_message(self, conversation: Dict[str, Any], role: str, content: str):
        """
        Add a message to the conversation history
        
        Args:
            conversation: Conversation context dict
            role: 'user' or 'assistant'
            content: Message content
        """
        if role not in ['user', 'assistant']:
            raise ClaudeConversationError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
            
        conversation['messages'].append({
            'role': role,
            'content': content
        })
    
    def generate_response(self, conversation: Dict[str, Any], user_message: str) -> str:
        """
        Generate a response from Claude for the given conversation and user message
        
        Args:
            conversation: Conversation context dict
            user_message: New message from user
            
        Returns:
            Claude's response as a string
            
        Raises:
            ClaudeConversationError: If generation fails
        """
        if not self.client:
            raise ClaudeConversationError("Claude client not initialized. Call initialize() first.")
        
        try:
            # Add user message to conversation
            self.add_message(conversation, 'user', user_message)
            
            # Prepare messages for Claude API
            # Claude expects separate system parameter and messages array
            messages = conversation['messages'].copy()
            
            logger.debug(f"Sending request to Claude model: {conversation['model']}")
            logger.debug(f"System prompt: {conversation['system_prompt']}")
            logger.debug(f"Message count: {len(messages)}")
            
            # Make API call to Claude
            response = self.client.messages.create(
                model=conversation['model'],
                max_tokens=conversation['max_tokens'],
                temperature=conversation['temperature'],
                system=conversation['system_prompt'],
                messages=messages
            )
            
            # Extract response text
            if response.content and len(response.content) > 0:
                response_text = response.content[0].text
                
                # Add assistant response to conversation history
                self.add_message(conversation, 'assistant', response_text)
                
                logger.info(f"Claude response generated successfully. Length: {len(response_text)}")
                return response_text
            else:
                raise ClaudeConversationError("Empty response received from Claude")
                
        except Exception as e:
            logger.error(f"Error generating Claude response: {e}")
            raise ClaudeConversationError(f"Response generation failed: {e}")
    
    def create_simple_chat(self, 
                          system_prompt: str, 
                          user_message: str,
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None) -> str:
        """
        Simple one-off chat with Claude (no conversation history)
        
        Args:
            system_prompt: System message for context
            user_message: User's message
            max_tokens: Maximum tokens for response (optional)
            temperature: Response randomness (0-1, optional)
            
        Returns:
            Claude's response as a string
        """
        conversation = self.create_conversation(
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return self.generate_response(conversation, user_message)
    
    def get_conversation_summary(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary information about a conversation
        
        Args:
            conversation: Conversation context dict
            
        Returns:
            Dict with conversation statistics
        """
        messages = conversation['messages']
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        total_chars = sum(len(msg['content']) for msg in messages)
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_characters': total_chars,
            'model': conversation['model'],
            'system_prompt_length': len(conversation['system_prompt'])
        }


# Global service instance
_claude_service = None

def get_claude_service() -> ClaudeService:
    """Get or create global Claude service instance"""
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service

def initialize_claude_service():
    """Initialize the global Claude service"""
    service = get_claude_service()
    service.initialize()
    return service