#!/usr/bin/env python3
"""
Test script for Claude integration in OpenMoxie

This script tests the Claude service integration to ensure it's properly
configured and working before using it in the main application.
"""

import os
import sys
from dotenv import load_dotenv

# Add site directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

# Load environment variables
load_dotenv()

def test_claude_integration():
    """Test the Claude integration setup"""
    
    print("🤖 Testing Claude Integration for OpenMoxie")
    print("=" * 50)
    
    # Check environment variables
    print("1. Checking environment configuration...")
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    claude_model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
    
    if not anthropic_key or anthropic_key == 'your-anthropic-api-key-here':
        print("   ❌ ANTHROPIC_API_KEY not set or using placeholder value")
        print("   ℹ️  Please set your Anthropic API key in .env file:")
        print("   ℹ️  ANTHROPIC_API_KEY=your_actual_api_key_here")
        return False
    
    print(f"   ✅ ANTHROPIC_API_KEY is set")
    print(f"   ✅ CLAUDE_MODEL: {claude_model}")
    
    # Test imports
    print("\n2. Testing imports...")
    try:
        from anthropic import Anthropic
        print("   ✅ anthropic package imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import anthropic: {e}")
        print("   ℹ️  Run: pip install 'anthropic>=0.40.0'")
        return False
    
    # Test AI factory
    print("\n3. Testing AI factory...")
    try:
        from hive.mqtt.ai_factory import create_claude, set_anthropic_key, get_claude_model
        set_anthropic_key(anthropic_key)
        client = create_claude()
        print("   ✅ Claude client created successfully")
        print(f"   ✅ Model configuration: {get_claude_model()}")
    except Exception as e:
        print(f"   ❌ Failed to create Claude client: {e}")
        return False
    
    # Test Claude service
    print("\n4. Testing Claude service...")
    try:
        from hive.mqtt.claude_service import ClaudeService, initialize_claude_service
        
        # Initialize service
        service = initialize_claude_service()
        print("   ✅ Claude service initialized")
        
        # Test simple conversation
        print("\n5. Testing simple conversation...")
        system_prompt = "You are a helpful assistant for testing AI integration in OpenMoxie."
        test_message = "Hello! Can you confirm you're working correctly?"
        
        response = service.create_simple_chat(
            system_prompt=system_prompt,
            user_message=test_message,
            max_tokens=100
        )
        
        print(f"   ✅ Test conversation successful!")
        print(f"   📝 Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        # Test conversation management
        print("\n6. Testing conversation management...")
        conversation = service.create_conversation(system_prompt)
        
        response1 = service.generate_response(conversation, "What's 2+2?")
        response2 = service.generate_response(conversation, "What about 3+3?")
        
        summary = service.get_conversation_summary(conversation)
        print(f"   ✅ Conversation management working!")
        print(f"   📊 Summary: {summary['total_messages']} messages, {summary['total_characters']} chars")
        
        print("\n🎉 All Claude integration tests passed!")
        print("\n📋 Next steps:")
        print("   1. Your Claude integration is ready to use")
        print("   2. You can now use both OpenAI and Claude in your application")
        print("   3. Check the Claude service documentation for usage examples")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Claude service test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples for the Claude integration"""
    
    print("\n" + "=" * 50)
    print("🔧 Claude Integration Usage Examples")
    print("=" * 50)
    
    examples = [
        ("Simple Chat", """
from hive.mqtt.claude_service import get_claude_service

service = get_claude_service()
service.initialize()

response = service.create_simple_chat(
    system_prompt="You are a helpful Moxie robot assistant.",
    user_message="How can I help my Moxie robot learn new things?"
)
print(response)
"""),
        ("Conversation Management", """
from hive.mqtt.claude_service import get_claude_service

service = get_claude_service()
service.initialize()

# Create a conversation
conversation = service.create_conversation(
    system_prompt="You are Moxie, a friendly robot companion."
)

# Have a multi-turn conversation
response1 = service.generate_response(conversation, "Hello Moxie!")
response2 = service.generate_response(conversation, "Tell me a joke")

# Get conversation summary
summary = service.get_conversation_summary(conversation)
print(f"Total messages: {summary['total_messages']}")
"""),
        ("Configuration", """
# In your .env file:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Available models:
# - claude-3-5-sonnet-20241022 (recommended)
# - claude-3-opus-20240229
# - claude-3-haiku-20240307
""")
    ]
    
    for title, code in examples:
        print(f"\n{title}:")
        print("-" * len(title))
        print(code.strip())

if __name__ == "__main__":
    success = test_claude_integration()
    
    if success:
        show_usage_examples()
        sys.exit(0)
    else:
        print("\n❌ Claude integration test failed!")
        print("Please fix the issues above and try again.")
        sys.exit(1)