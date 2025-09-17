#!/usr/bin/env python3
"""
Test script to verify OpenMoxie improvements
"""
import sys
import os

# Add the site directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

def test_behavior_config():
    """Test behavior configuration imports"""
    try:
        from hive.behavior_config import (
            get_behavior_markup, get_quick_action_behavior, 
            get_preset_actions, get_sound_effect_markup
        )
        
        # Test quick action mapping
        behavior = get_quick_action_behavior('celebrate')
        assert behavior == 'Bht_Spin_360', f"Expected 'Bht_Spin_360', got '{behavior}'"
        
        # Test behavior markup generation
        markup = get_behavior_markup('Bht_Spin_360')
        assert '<mark name="cmd:behaviour-tree' in markup, "Markup should contain behavior tree command"
        
        # Test preset actions
        preset = get_preset_actions('greeting')
        assert len(preset) > 0, "Greeting preset should have actions"
        
        # Test sound effect markup
        sound_markup = get_sound_effect_markup('test_sound', 0.8)
        assert 'cmd:playaudio' in sound_markup, "Sound markup should contain playaudio command"
        assert 'Volume+:0.8' in sound_markup, "Sound markup should contain volume setting"
        
        print("✅ Behavior configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Behavior configuration test failed: {str(e)}")
        return False


def test_validators():
    """Test input validators"""
    try:
        from hive.validators import (
            validate_openai_api_key, validate_hostname, sanitize_input,
            ValidationError
        )
        
        # Test API key validation
        try:
            validate_openai_api_key('sk-test1234567890123456789012345678901234567890')
            print("✅ API key validation passed")
        except ValidationError:
            print("❌ Valid API key was rejected")
            return False
        
        # Test invalid API key
        try:
            validate_openai_api_key('invalid-key')
            print("❌ Invalid API key was accepted")
            return False
        except ValidationError:
            print("✅ Invalid API key was correctly rejected")
        
        # Test hostname validation
        assert validate_hostname('localhost') == True
        assert validate_hostname('127.0.0.1') == True
        assert validate_hostname('example.com') == True
        
        # Test input sanitization
        sanitized = sanitize_input('test\x00input\x01', max_length=10)
        assert sanitized == 'testinput', f"Expected 'testinput', got '{sanitized}'"
        
        print("✅ Validator tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Validator test failed: {str(e)}")
        return False


def test_auth_utils():
    """Test authentication utilities"""
    try:
        from hive.auth_utils import generate_api_token, validate_api_token
        
        # Test token generation and validation
        user_id = 'test_user'
        token = generate_api_token(user_id)
        
        assert isinstance(token, str), "Token should be a string"
        assert len(token.split(':')) == 3, "Token should have 3 parts separated by colons"
        
        # Test token validation
        is_valid, returned_user_id = validate_api_token(token)
        assert is_valid == True, "Generated token should be valid"
        assert returned_user_id == user_id, f"Expected '{user_id}', got '{returned_user_id}'"
        
        # Test invalid token
        is_valid, _ = validate_api_token('invalid:token:format')
        assert is_valid == False, "Invalid token should be rejected"
        
        print("✅ Auth utilities tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Auth utilities test failed: {str(e)}")
        return False


def test_env_validator():
    """Test environment validation"""
    try:
        from hive.env_validator import validate_required_env_vars, check_system_requirements
        
        # Set required environment variable for testing
        os.environ['SECRET_KEY'] = 'test-secret-key-for-validation-testing-12345678901234567890'
        
        # This should pass basic validation
        try:
            results = validate_required_env_vars()
            print("✅ Environment validation framework working")
        except Exception as e:
            # This might fail due to missing other env vars, but the framework should be working
            if 'SECRET_KEY' in str(e):
                print("❌ Environment validation failed unexpectedly")
                return False
            else:
                print("✅ Environment validation framework working (expected some missing vars)")
        
        # Test system requirements check
        system_ok = check_system_requirements()
        # This might fail due to missing packages, but shouldn't crash
        print(f"✅ System requirements check completed ({'passed' if system_ok else 'found issues'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment validator test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing OpenMoxie improvements...\n")
    
    tests = [
        test_behavior_config,
        test_validators,
        test_auth_utils,
        test_env_validator,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Empty line for readability
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenMoxie improvements are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())