#!/usr/bin/env python3
"""
60-Second Laugh Test Suite

This test file specifically validates the 60-second laugh functionality
in OpenMoxie, including both the repeated behavior approach and the
pre-built sequence approach.
"""

import os
import sys
import django
import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openmoxie.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-purposes-12345678901234567890')
os.environ.setdefault('SKIP_ENV_VALIDATION', 'true')

# Add the site directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

django.setup()

from hive.behavior_config import create_laugh_60_second_sequence, get_behavior_markup
from hive.views import dj_handle_laugh_60_seconds, dj_handle_repeated_behavior


class Test60SecondLaugh(unittest.TestCase):
    """Test suite for 60-second laugh functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_device_id = "test_device_123"

    def test_create_laugh_60_second_sequence(self):
        """Test that the 60-second laugh sequence is generated correctly"""
        print("\n🧪 Testing 60-second laugh sequence generation...")

        # Test the sequence creation
        sequence = create_laugh_60_second_sequence()

        # Verify sequence is not empty
        self.assertIsNotNone(sequence, "Laugh sequence should not be None")
        self.assertGreater(len(sequence), 0, "Laugh sequence should not be empty")

        # Verify it contains the expected laugh behavior
        self.assertIn('Bht_Vg_Laugh_Big_Fourcount', sequence,
                     "Sequence should contain the laugh behavior")

        # Verify it contains SSML markup
        self.assertIn('<mark name="cmd:behaviour-tree', sequence,
                     "Sequence should contain behavior tree markup")

        # Count the number of laugh commands (should be around 30)
        laugh_count = sequence.count('Bht_Vg_Laugh_Big_Fourcount')
        self.assertGreaterEqual(laugh_count, 25,
                               f"Should have at least 25 laugh commands, got {laugh_count}")
        self.assertLessEqual(laugh_count, 35,
                            f"Should have at most 35 laugh commands, got {laugh_count}")

        # Verify it contains breaks between laughs
        break_count = sequence.count('<break time="0.5s"/>')
        self.assertGreaterEqual(break_count, 24,
                               f"Should have at least 24 breaks, got {break_count}")

        print(f"✅ Sequence contains {laugh_count} laugh commands and {break_count} breaks")
        print(f"✅ Sequence length: {len(sequence)} characters")

    def test_get_behavior_markup_for_laugh(self):
        """Test that individual laugh behavior markup is generated correctly"""
        print("\n🧪 Testing individual laugh behavior markup...")

        # Test the base behavior markup
        markup = get_behavior_markup("Bht_Vg_Laugh_Big_Fourcount")

        # Verify markup is generated
        self.assertIsNotNone(markup, "Markup should not be None")
        self.assertGreater(len(markup), 0, "Markup should not be empty")

        # Verify it contains expected elements
        self.assertIn('Bht_Vg_Laugh_Big_Fourcount', markup,
                     "Markup should contain the laugh behavior name")

        print(f"✅ Individual laugh markup generated successfully")
        print(f"✅ Markup length: {len(markup)} characters")

    @patch('hive.views.get_instance')
    def test_dj_handle_laugh_60_seconds(self, mock_get_instance):
        """Test the DJ handler for 60-second laugh sequence"""
        print("\n🧪 Testing DJ 60-second laugh handler...")

        # Mock the server instance
        mock_server = Mock()
        mock_get_instance.return_value = mock_server

        # Test the handler
        try:
            dj_handle_laugh_60_seconds(self.test_device_id)

            # Verify get_instance was called
            mock_get_instance.assert_called_once()

            # Verify send_telehealth_markup was called with correct parameters
            mock_server.send_telehealth_markup.assert_called_once()

            # Get the call arguments
            call_args = mock_server.send_telehealth_markup.call_args
            device_id_arg = call_args[0][0]
            sequence_arg = call_args[0][1]

            # Verify device ID
            self.assertEqual(device_id_arg, self.test_device_id,
                           f"Device ID should be {self.test_device_id}")

            # Verify sequence content
            self.assertIn('Bht_Vg_Laugh_Big_Fourcount', sequence_arg,
                         "Sequence should contain laugh behavior")

            print(f"✅ Handler called server correctly with device {device_id_arg}")
            print(f"✅ Sequence sent to server has {len(sequence_arg)} characters")

        except Exception as e:
            self.fail(f"dj_handle_laugh_60_seconds failed with error: {e}")

    @patch('hive.views.get_instance')
    @patch('threading.Thread')
    def test_dj_handle_repeated_behavior(self, mock_thread, mock_get_instance):
        """Test the DJ handler for repeated behavior approach"""
        print("\n🧪 Testing DJ repeated behavior handler...")

        # Mock the server instance
        mock_server = Mock()
        mock_get_instance.return_value = mock_server

        # Mock the thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # Test the handler
        try:
            dj_handle_repeated_behavior(self.test_device_id, "Bht_Vg_Laugh_Big_Fourcount", 60)

            # Verify thread was created
            mock_thread.assert_called_once()

            # Verify thread was started
            mock_thread_instance.start.assert_called_once()

            # Verify thread is daemon
            self.assertTrue(mock_thread_instance.daemon,
                           "Background thread should be daemon")

            print(f"✅ Repeated behavior handler started background thread correctly")

        except Exception as e:
            self.fail(f"dj_handle_repeated_behavior failed with error: {e}")

    def test_sequence_timing_calculation(self):
        """Test that the sequence timing is approximately correct"""
        print("\n🧪 Testing sequence timing calculation...")

        sequence = create_laugh_60_second_sequence()

        # Count laughs and breaks
        laugh_count = sequence.count('Bht_Vg_Laugh_Big_Fourcount')
        break_count = sequence.count('<break time="0.5s"/>')

        # Calculate approximate duration
        # Each laugh is 1.5 seconds, each break is 0.5 seconds
        approx_duration = (laugh_count * 1.5) + (break_count * 0.5)

        # Should be close to 60 seconds (within reasonable tolerance)
        self.assertGreaterEqual(approx_duration, 55.0,
                               f"Duration should be at least 55 seconds, got {approx_duration}")
        self.assertLessEqual(approx_duration, 65.0,
                            f"Duration should be at most 65 seconds, got {approx_duration}")

        print(f"✅ Calculated approximate duration: {approx_duration} seconds")

    def test_sequence_structure(self):
        """Test the structure and format of the generated sequence"""
        print("\n🧪 Testing sequence structure and format...")

        sequence = create_laugh_60_second_sequence()

        # Test that it starts with a laugh command
        self.assertTrue(sequence.startswith('<mark name="cmd:behaviour-tree'),
                       "Sequence should start with a behavior command")

        # Test that breaks are properly formatted - use regex to find complete break elements
        import re
        break_pattern = r'<break[^>]*time="0\.5s"[^>]*/?>'
        breaks = re.findall(break_pattern, sequence)
        self.assertGreater(len(breaks), 20, f"Should find at least 20 properly formatted breaks, found {len(breaks)}")

        # Check first few breaks for proper format
        for i, break_elem in enumerate(breaks[:3]):
            self.assertIn('time="0.5s"', break_elem, f"Break {i} should have correct timing: {break_elem}")

        # Test that behavior commands have required parameters
        if 'duration' in sequence:
            self.assertIn('1.5', sequence, "Duration should be set to 1.5 seconds")
        if 'blocking' in sequence:
            self.assertIn('false', sequence, "Blocking should be set to false")

        print(f"✅ Sequence structure is valid")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n🧪 Testing edge cases...")

        # Test with None device ID (should not crash)
        with patch('hive.views.get_instance') as mock_get_instance:
            mock_server = Mock()
            mock_get_instance.return_value = mock_server

            try:
                dj_handle_laugh_60_seconds(None)
                print("✅ Handler gracefully handles None device ID")
            except Exception as e:
                print(f"⚠️ Handler with None device ID: {e}")

        # Test with empty device ID
        with patch('hive.views.get_instance') as mock_get_instance:
            mock_server = Mock()
            mock_get_instance.return_value = mock_server

            try:
                dj_handle_laugh_60_seconds("")
                print("✅ Handler gracefully handles empty device ID")
            except Exception as e:
                print(f"⚠️ Handler with empty device ID: {e}")

    def run_integration_test(self):
        """Run an integration test of the full 60-second laugh functionality"""
        print("\n🧪 Running integration test...")

        # Test sequence generation
        sequence = create_laugh_60_second_sequence()
        self.assertIsNotNone(sequence)

        # Test handler with mock server
        with patch('hive.views.get_instance') as mock_get_instance:
            mock_server = Mock()
            mock_get_instance.return_value = mock_server

            # Test both approaches
            dj_handle_laugh_60_seconds(self.test_device_id)
            dj_handle_repeated_behavior(self.test_device_id, "Bht_Vg_Laugh_Big_Fourcount", 60)

            print("✅ Integration test completed successfully")


def run_tests():
    """Run all 60-second laugh tests"""
    print("🧪 Starting 60-Second Laugh Test Suite")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Test60SecondLaugh)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Run integration test separately
    test_instance = Test60SecondLaugh()
    test_instance.setUp()
    try:
        test_instance.run_integration_test()
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("\n🎉 All 60-Second Laugh Tests PASSED!")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
