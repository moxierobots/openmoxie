#!/usr/bin/env python3
"""
Test script for DJ MIX configuration
Verifies that all DJ MIX commands are properly configured and can generate valid markup
"""

import sys
import os

# Add the site directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openmoxie.settings')

import django
django.setup()

from hive.dj_mix_config import (
    DJ_MIX_COMMANDS,
    DJ_MIX_CATEGORIES,
    get_dj_mix_command,
    get_dj_mix_commands_by_category,
    generate_dj_mix_markup,
    get_dj_mix_command_info
)

def test_dj_mix_configuration():
    """Test DJ MIX configuration and functionality"""
    print("🎧 Testing DJ MIX Configuration")
    print("=" * 50)

    # Test 1: Verify all commands exist
    print("\n1. Testing DJ MIX Commands:")
    total_commands = len(DJ_MIX_COMMANDS)
    print(f"   Total commands configured: {total_commands}")

    if total_commands == 0:
        print("   ❌ No DJ MIX commands found!")
        return False

    print("   ✅ DJ MIX commands loaded successfully")

    # Test 2: Verify categories
    print("\n2. Testing Categories:")
    total_categories = len(DJ_MIX_CATEGORIES)
    print(f"   Total categories: {total_categories}")

    for category_key, category_info in DJ_MIX_CATEGORIES.items():
        print(f"   📂 {category_key}: {category_info['name']} {category_info['icon']}")

    # Test 3: Test each command
    print("\n3. Testing Individual Commands:")
    success_count = 0

    for command_key, command_info in DJ_MIX_COMMANDS.items():
        try:
            # Test basic info retrieval
            info = get_dj_mix_command_info(command_key)
            if not info:
                print(f"   ❌ {command_key}: Failed to get command info")
                continue

            # Test markup generation
            markup = generate_dj_mix_markup(command_key)
            if not markup:
                print(f"   ❌ {command_key}: Failed to generate markup")
                continue

            # Verify markup contains both audio and behavior commands
            if 'cmd:playaudio' not in markup:
                print(f"   ❌ {command_key}: Missing audio command in markup")
                continue

            if 'cmd:behaviour-tree' not in markup:
                print(f"   ❌ {command_key}: Missing behavior command in markup")
                continue

            print(f"   ✅ {command_key}: {info['name']} ({info['bpm']} BPM, {info['duration']}s)")
            success_count += 1

        except Exception as e:
            print(f"   ❌ {command_key}: Error - {str(e)}")

    print(f"\n   Commands tested: {success_count}/{total_commands}")

    # Test 4: Test category filtering
    print("\n4. Testing Category Filtering:")
    for category_key in DJ_MIX_CATEGORIES.keys():
        commands_in_category = get_dj_mix_commands_by_category(category_key)
        count = len(commands_in_category)
        print(f"   📁 {category_key}: {count} commands")

    # Test 5: Sample markup output
    print("\n5. Sample Markup Output:")
    sample_command = 'zaygo_long_140'
    if sample_command in DJ_MIX_COMMANDS:
        sample_markup = generate_dj_mix_markup(sample_command)
        print(f"   Command: {sample_command}")
        print(f"   Markup length: {len(sample_markup)} characters")
        print(f"   First 100 chars: {sample_markup[:100]}...")

    # Test 6: Verify all required fields
    print("\n6. Testing Required Fields:")
    required_fields = ['name', 'description', 'audio_command', 'behavior_command', 'category', 'bpm', 'duration']
    field_errors = 0

    for command_key, command_info in DJ_MIX_COMMANDS.items():
        for field in required_fields:
            if field not in command_info:
                print(f"   ❌ {command_key}: Missing required field '{field}'")
                field_errors += 1

    if field_errors == 0:
        print("   ✅ All commands have required fields")
    else:
        print(f"   ❌ Found {field_errors} missing field errors")

    # Summary
    print("\n" + "=" * 50)
    success_rate = (success_count / total_commands * 100) if total_commands > 0 else 0
    print(f"🎵 DJ MIX Test Summary:")
    print(f"   Total Commands: {total_commands}")
    print(f"   Successful: {success_count}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Categories: {total_categories}")
    print(f"   Field Errors: {field_errors}")

    overall_success = (success_count == total_commands and field_errors == 0 and total_commands > 0)

    if overall_success:
        print("   🎉 All tests passed! DJ MIX is ready to rock!")
    else:
        print("   ⚠️  Some tests failed. Please check the configuration.")

    return overall_success

def show_command_details():
    """Show detailed information about each DJ MIX command"""
    print("\n🎼 Detailed Command Information")
    print("=" * 50)

    for category_key, category_info in DJ_MIX_CATEGORIES.items():
        print(f"\n📂 {category_info['icon']} {category_info['name']}")
        print(f"   {category_info['description']}")
        print(f"   Color: {category_info['color']}")

        commands = get_dj_mix_commands_by_category(category_key)
        for command_key, command_info in commands.items():
            print(f"   🎵 {command_key}:")
            print(f"      Name: {command_info['name']}")
            print(f"      BPM: {command_info['bpm']} | Duration: {command_info['duration']}s")
            print(f"      Description: {command_info['description']}")

if __name__ == "__main__":
    print("🎧 OpenMoxie DJ MIX Test Suite")
    print("Testing DJ MIX configuration and functionality...")

    try:
        # Run the main test
        success = test_dj_mix_configuration()

        # Show detailed information if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--details":
            show_command_details()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're running this from the openmoxie directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)
