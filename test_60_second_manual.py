#!/usr/bin/env python3
"""
Manual Test for 60-Second Laugh Functionality

This script provides a manual testing interface for the 60-second laugh
functionality, allowing developers to test both approaches interactively.
"""

import os
import sys
import django
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openmoxie.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-purposes-12345678901234567890')
os.environ.setdefault('SKIP_ENV_VALIDATION', 'true')

# Add the site directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

django.setup()

from hive.behavior_config import create_laugh_60_second_sequence
from hive.views import dj_handle_laugh_60_seconds, dj_handle_repeated_behavior
from unittest.mock import Mock, patch


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_sequence_generation():
    """Test and display the generated 60-second laugh sequence"""
    print_header("Testing Sequence Generation")

    try:
        sequence = create_laugh_60_second_sequence()

        print(f"✅ Sequence generated successfully")
        print(f"   Length: {len(sequence)} characters")
        print(f"   Laugh count: {sequence.count('Bht_Vg_Laugh_Big_Fourcount')}")
        print(f"   Break count: {sequence.count('<break time=\"0.5s\"/>')}")

        # Calculate estimated duration
        laugh_count = sequence.count('Bht_Vg_Laugh_Big_Fourcount')
        break_count = sequence.count('<break time="0.5s"/>')
        duration = (laugh_count * 1.5) + (break_count * 0.5)
        print(f"   Estimated duration: {duration} seconds")

        # Show sample of the sequence
        print(f"\n📋 Sample of generated sequence:")
        sample = sequence[:200] + "..." + sequence[-100:] if len(sequence) > 300 else sequence
        print(f"   {sample}")

        return True

    except Exception as e:
        print(f"❌ Error generating sequence: {e}")
        return False


def test_dj_handlers():
    """Test both DJ handler approaches with mocked server"""
    print_header("Testing DJ Handlers")

    test_device_id = "manual_test_device"

    # Test Option A: Pre-built sequence
    print("\n🧪 Testing Option A: Pre-built Sequence Handler")
    try:
        with patch('hive.views.get_instance') as mock_get_instance:
            mock_server = Mock()
            mock_get_instance.return_value = mock_server

            dj_handle_laugh_60_seconds(test_device_id)

            # Verify the call
            mock_server.send_telehealth_markup.assert_called_once()
            call_args = mock_server.send_telehealth_markup.call_args[0]

            print(f"   ✅ Handler executed successfully")
            print(f"   ✅ Device ID: {call_args[0]}")
            print(f"   ✅ Sequence length: {len(call_args[1])} characters")

    except Exception as e:
        print(f"   ❌ Error in pre-built sequence handler: {e}")
        return False

    # Test Option B: Repeated behavior
    print("\n🧪 Testing Option B: Repeated Behavior Handler")
    try:
        with patch('hive.views.get_instance') as mock_get_instance:
            mock_server = Mock()
            mock_get_instance.return_value = mock_server

            # Start the repeated behavior (it runs in background)
            dj_handle_repeated_behavior(test_device_id, "Bht_Vg_Laugh_Big_Fourcount", 5)  # 5 seconds for testing

            # Give it a moment to start
            time.sleep(0.1)

            print(f"   ✅ Repeated behavior handler started successfully")
            print(f"   ✅ Background thread launched for 5-second test")

    except Exception as e:
        print(f"   ❌ Error in repeated behavior handler: {e}")
        return False

    return True


def interactive_test():
    """Provide an interactive test menu"""
    print_header("Interactive 60-Second Laugh Test")

    while True:
        print("\nSelect a test option:")
        print("1. Generate and display 60-second laugh sequence")
        print("2. Test pre-built sequence handler (Option A)")
        print("3. Test repeated behavior handler (Option B)")
        print("4. Run all tests")
        print("5. Show timing analysis")
        print("0. Exit")

        choice = input("\nEnter your choice (0-5): ").strip()

        if choice == "0":
            print("Exiting manual test...")
            break

        elif choice == "1":
            test_sequence_generation()

        elif choice == "2":
            print_header("Testing Pre-built Sequence (Option A)")
            with patch('hive.views.get_instance') as mock_get_instance:
                mock_server = Mock()
                mock_get_instance.return_value = mock_server

                print("🚀 Sending 60-second laugh sequence...")
                dj_handle_laugh_60_seconds("interactive_test_device")

                print("✅ Pre-built sequence sent to mock server")
                print(f"✅ Server method called: {mock_server.send_telehealth_markup.called}")

        elif choice == "3":
            print_header("Testing Repeated Behavior (Option B)")
            duration = input("Enter test duration in seconds (default 5): ").strip()
            duration = int(duration) if duration.isdigit() else 5

            with patch('hive.views.get_instance') as mock_get_instance:
                mock_server = Mock()
                mock_get_instance.return_value = mock_server

                print(f"🚀 Starting repeated behavior for {duration} seconds...")
                dj_handle_repeated_behavior("interactive_test_device", "Bht_Vg_Laugh_Big_Fourcount", duration)

                print("✅ Repeated behavior started in background thread")
                print(f"   Duration: {duration} seconds")
                print(f"   Behavior: Bht_Vg_Laugh_Big_Fourcount")

        elif choice == "4":
            print("🧪 Running all tests...")
            seq_ok = test_sequence_generation()
            handlers_ok = test_dj_handlers()

            if seq_ok and handlers_ok:
                print("\n🎉 All manual tests completed successfully!")
            else:
                print("\n⚠️ Some tests had issues. Check the output above.")

        elif choice == "5":
            print_header("Timing Analysis")
            sequence = create_laugh_60_second_sequence()

            laugh_count = sequence.count('Bht_Vg_Laugh_Big_Fourcount')
            break_count = sequence.count('<break time="0.5s"/>')

            print(f"📊 Sequence Analysis:")
            print(f"   Total laugh commands: {laugh_count}")
            print(f"   Total breaks: {break_count}")
            print(f"   Laugh duration: {laugh_count} × 1.5s = {laugh_count * 1.5}s")
            print(f"   Break duration: {break_count} × 0.5s = {break_count * 0.5}s")
            print(f"   Total estimated time: {(laugh_count * 1.5) + (break_count * 0.5)}s")

            print(f"\n📏 Timing Breakdown:")
            print(f"   Each cycle: 1.5s laugh + 0.5s break = 2.0s")
            print(f"   Number of cycles: {laugh_count}")
            print(f"   Expected total: {laugh_count * 2.0}s (last cycle has no break)")

        else:
            print("Invalid choice. Please enter 0-5.")


def main():
    """Main function for manual testing"""
    print("🧪 Manual Test for 60-Second Laugh Functionality")
    print("This tool helps verify that the laugh tests are working correctly.")

    try:
        # Quick sanity check
        print("\n🔍 Performing initial sanity check...")
        sequence = create_laugh_60_second_sequence()
        if sequence and len(sequence) > 0:
            print("✅ Basic sequence generation is working")
        else:
            print("❌ Basic sequence generation failed!")
            return 1

        # Start interactive mode
        interactive_test()

        return 0

    except KeyboardInterrupt:
        print("\n❌ Manual test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error in manual test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
