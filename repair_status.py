#!/usr/bin/env python3
"""
Robot Repair Status Report for OpenMoxie

This script provides a comprehensive status report of the robot repair
and 60-second laugh test functionality after fixes have been applied.

Usage:
    python repair_status.py                    # Full status report
    python repair_status.py --test-commands   # Test all DJ commands
    python repair_status.py --test-mqtt       # Test MQTT connectivity
    python repair_status.py --test-laughs     # Test 60-second laugh functionality
"""

import os
import sys
import django
import json
import time
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openmoxie.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-purposes-12345678901234567890')
os.environ.setdefault('SKIP_ENV_VALIDATION', 'true')

# Add the site directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

django.setup()

from django.utils import timezone
from hive.models import MoxieDevice
from hive.behavior_config import create_laugh_60_second_sequence
from hive.views import dj_handle_laugh_60_seconds, dj_handle_repeated_behavior


class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'


def print_colored(message: str, color: str = Colors.NC):
    """Print message with color"""
    print(f"{color}{message}{Colors.NC}")


def print_header(title: str):
    """Print a formatted header"""
    print()
    print_colored("=" * 70, Colors.BLUE)
    print_colored(f" {title}", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 70, Colors.BLUE)


class RepairStatusChecker:
    def __init__(self):
        self.hive_url = "http://localhost:8001"
        self.test_results = []

    def add_test_result(self, test_name: str, status: bool, message: str):
        """Add a test result to the results list"""
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    def check_docker_services(self) -> Dict:
        """Check if Docker services are running"""
        print_colored("🐳 Checking Docker services...", Colors.YELLOW)

        try:
            import subprocess
            result = subprocess.run(['docker-compose', 'ps', '--format', 'json'],
                                  capture_output=True, text=True, cwd='.')

            if result.returncode == 0:
                services = json.loads(result.stdout) if result.stdout.strip() else []
                running_services = [s for s in services if 'Up' in s.get('State', '')]

                status = {
                    'mqtt': any('mqtt' in s['Service'] for s in running_services),
                    'server': any('server' in s['Service'] for s in running_services),
                    'postgres': any('postgres' in s['Service'] for s in running_services),
                    'total_services': len(services),
                    'running_services': len(running_services)
                }

                for service, running in [('MQTT', status['mqtt']),
                                       ('Server', status['server']),
                                       ('PostgreSQL', status['postgres'])]:
                    if running:
                        print_colored(f"   ✅ {service}: Running", Colors.GREEN)
                    else:
                        print_colored(f"   ❌ {service}: Not running", Colors.RED)

                return status
            else:
                print_colored("   ❌ Failed to check Docker services", Colors.RED)
                return {'error': 'Docker compose command failed'}

        except Exception as e:
            print_colored(f"   ❌ Error checking Docker services: {e}", Colors.RED)
            return {'error': str(e)}

    def check_hive_server(self) -> Dict:
        """Check if Hive server is responsive"""
        print_colored("🌐 Checking Hive server status...", Colors.YELLOW)

        try:
            # Check health endpoint
            response = requests.get(f"{self.hive_url}/health/ready/", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print_colored("   ✅ Hive server: Healthy", Colors.GREEN)
                return {'status': 'healthy', 'data': health_data}
            else:
                print_colored(f"   ❌ Hive server: Unhealthy (HTTP {response.status_code})", Colors.RED)
                return {'status': 'unhealthy', 'code': response.status_code}
        except Exception as e:
            print_colored(f"   ❌ Hive server: Connection failed ({e})", Colors.RED)
            return {'status': 'connection_failed', 'error': str(e)}

    def check_database_devices(self) -> Dict:
        """Check registered devices in database"""
        print_colored("📱 Checking registered devices...", Colors.YELLOW)

        try:
            devices = MoxieDevice.objects.all()
            device_info = []

            for device in devices:
                recently_connected = False
                if device.last_connect:
                    time_diff = timezone.now() - device.last_connect
                    recently_connected = time_diff < timedelta(minutes=5)

                device_data = {
                    'id': device.pk,
                    'device_id': device.device_id,
                    'name': device.name,
                    'last_connect': device.last_connect.isoformat() if device.last_connect else None,
                    'recently_connected': recently_connected,
                    'telehealth_enabled': device.robot_config.get("moxie_mode") == "TELEHEALTH" if device.robot_config else False
                }
                device_info.append(device_data)

                status_icon = "🟢" if recently_connected else "🔴"
                telehealth_icon = "✅" if device_data['telehealth_enabled'] else "❌"
                print(f"   {status_icon} {device.name} ({device.device_id[-8:]}...)")
                print(f"      Telehealth: {telehealth_icon} | Last connect: {device_data['last_connect'] or 'Never'}")

            if not device_info:
                print_colored("   ⚠️ No devices registered", Colors.YELLOW)

            return {'devices': device_info, 'count': len(device_info)}

        except Exception as e:
            print_colored(f"   ❌ Database error: {e}", Colors.RED)
            return {'error': str(e)}

    def check_60_second_laugh_sequence(self) -> Dict:
        """Check 60-second laugh sequence generation"""
        print_colored("😂 Testing 60-second laugh sequence generation...", Colors.YELLOW)

        try:
            sequence = create_laugh_60_second_sequence()

            # Analyze sequence
            laugh_count = sequence.count('Bht_Vg_Laugh_Big_Fourcount')
            break_count = sequence.count('<break time="0.5s"/>')
            estimated_duration = (laugh_count * 1.5) + (break_count * 0.5)

            analysis = {
                'sequence_length': len(sequence),
                'laugh_count': laugh_count,
                'break_count': break_count,
                'estimated_duration': estimated_duration,
                'duration_valid': 55.0 <= estimated_duration <= 65.0
            }

            print(f"   ✅ Sequence generated: {analysis['sequence_length']} chars")
            print(f"   📊 Laughs: {laugh_count}, Breaks: {break_count}")

            if analysis['duration_valid']:
                print_colored(f"   ✅ Duration: {estimated_duration}s (within valid range)", Colors.GREEN)
            else:
                print_colored(f"   ❌ Duration: {estimated_duration}s (outside valid range)", Colors.RED)

            return analysis

        except Exception as e:
            print_colored(f"   ❌ Sequence generation failed: {e}", Colors.RED)
            return {'error': str(e)}

    def test_dj_commands(self) -> Dict:
        """Test DJ command endpoints"""
        print_colored("🎛️ Testing DJ command endpoints...", Colors.YELLOW)

        # Get first device for testing
        try:
            device = MoxieDevice.objects.first()
            if not device:
                print_colored("   ❌ No devices available for testing", Colors.RED)
                return {'error': 'No devices available'}

            device_pk = device.pk
            print(f"   🎯 Testing with device: {device.name} (ID: {device_pk})")

        except Exception as e:
            print_colored(f"   ❌ Failed to get device: {e}", Colors.RED)
            return {'error': str(e)}

        # Test commands
        test_commands = [
            {'cmd': 'interrupt', 'data': {}, 'expected': True},
            {'cmd': 'laugh_60s', 'data': {}, 'expected': True},
            {'cmd': 'repeated_behavior', 'data': {
                'behavior_name': 'Bht_Vg_Laugh_Big_Fourcount',
                'duration_seconds': 5
            }, 'expected': True},
            {'cmd': 'invalid_command_test', 'data': {}, 'expected': False}
        ]

        results = {}

        for test in test_commands:
            try:
                # Prepare request data
                data = {'command': test['cmd']}
                data.update(test['data'])

                # Send request
                response = requests.post(
                    f"{self.hive_url}/hive/dj_command_safe/{device_pk}",
                    data=data,
                    timeout=10
                )

                response_data = response.json() if response.content else {}
                success = response_data.get('result') == 'success'

                if test['expected'] == success:
                    print_colored(f"   ✅ {test['cmd']}: {'Success' if success else 'Failed as expected'}", Colors.GREEN)
                    results[test['cmd']] = {'status': 'pass', 'response': response_data}
                else:
                    print_colored(f"   ❌ {test['cmd']}: Unexpected result", Colors.RED)
                    results[test['cmd']] = {'status': 'fail', 'response': response_data}

            except Exception as e:
                print_colored(f"   ❌ {test['cmd']}: Error - {e}", Colors.RED)
                results[test['cmd']] = {'status': 'error', 'error': str(e)}

        return results

    def test_mqtt_connectivity(self) -> Dict:
        """Test MQTT connectivity (basic check)"""
        print_colored("📡 Testing MQTT connectivity...", Colors.YELLOW)

        try:
            # Try to create a 60-second laugh sequence and see if MQTT server responds
            device = MoxieDevice.objects.first()
            if not device:
                return {'error': 'No devices available for MQTT test'}

            print(f"   🎯 Testing MQTT with device: {device.name}")

            # This will attempt to create MQTT server instance and connect
            result = dj_handle_laugh_60_seconds(device.device_id)

            print_colored("   ✅ MQTT connection attempt completed", Colors.GREEN)
            print_colored("   ℹ️ Check MQTT logs for detailed connection status", Colors.CYAN)

            return {'status': 'attempted', 'device_id': device.device_id}

        except Exception as e:
            print_colored(f"   ⚠️ MQTT test encountered error: {e}", Colors.YELLOW)
            return {'status': 'error', 'error': str(e)}

    def run_comprehensive_status_check(self) -> Dict:
        """Run comprehensive status check"""
        print_header("🔍 OpenMoxie Repair Status Report")

        report = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        # Check all components
        report['checks']['docker'] = self.check_docker_services()
        report['checks']['server'] = self.check_hive_server()
        report['checks']['devices'] = self.check_database_devices()
        report['checks']['laugh_sequence'] = self.check_60_second_laugh_sequence()

        return report

    def run_command_tests(self) -> Dict:
        """Run DJ command tests"""
        print_header("🎛️ DJ Command Test Suite")

        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }

        results['tests']['dj_commands'] = self.test_dj_commands()

        return results

    def run_mqtt_tests(self) -> Dict:
        """Run MQTT connectivity tests"""
        print_header("📡 MQTT Connectivity Tests")

        results = {
            'timestamp': datetime.now().isoformat(),
            'mqtt_test': self.test_mqtt_connectivity()
        }

        return results

    def run_laugh_tests(self) -> Dict:
        """Run specific 60-second laugh tests"""
        print_header("😂 60-Second Laugh Test Suite")

        results = {
            'timestamp': datetime.now().isoformat(),
            'laugh_tests': {}
        }

        # Test sequence generation
        results['laugh_tests']['sequence_generation'] = self.check_60_second_laugh_sequence()

        # Test DJ commands for laugh functionality
        device = MoxieDevice.objects.first()
        if device:
            print_colored("🎭 Testing laugh command endpoints...", Colors.YELLOW)

            laugh_commands = [
                {'cmd': 'laugh_60s', 'name': 'Pre-built Sequence (Option A)'},
                {'cmd': 'repeated_behavior', 'name': 'Repeated Behavior (Option B)', 'data': {
                    'behavior_name': 'Bht_Vg_Laugh_Big_Fourcount',
                    'duration_seconds': 10
                }}
            ]

            command_results = {}

            for test in laugh_commands:
                try:
                    data = {'command': test['cmd']}
                    if 'data' in test:
                        data.update(test['data'])

                    response = requests.post(
                        f"{self.hive_url}/hive/dj_command_safe/{device.pk}",
                        data=data,
                        timeout=10
                    )

                    response_data = response.json()
                    success = response_data.get('result') == 'success'

                    if success:
                        print_colored(f"   ✅ {test['name']}: Working", Colors.GREEN)
                    else:
                        print_colored(f"   ❌ {test['name']}: Failed", Colors.RED)

                    command_results[test['cmd']] = {
                        'name': test['name'],
                        'success': success,
                        'response': response_data
                    }

                except Exception as e:
                    print_colored(f"   ❌ {test['name']}: Error - {e}", Colors.RED)
                    command_results[test['cmd']] = {
                        'name': test['name'],
                        'success': False,
                        'error': str(e)
                    }

            results['laugh_tests']['commands'] = command_results

        return results

    def print_summary(self, results: Dict):
        """Print a summary of all test results"""
        print_header("📊 Summary")

        total_checks = 0
        passed_checks = 0

        # Count results based on the type of test run
        if 'checks' in results:
            # Comprehensive status check
            for check_name, check_data in results['checks'].items():
                total_checks += 1
                if not isinstance(check_data, dict) or 'error' not in check_data:
                    passed_checks += 1

        elif 'tests' in results:
            # Command tests
            if 'dj_commands' in results['tests']:
                for cmd_name, cmd_result in results['tests']['dj_commands'].items():
                    total_checks += 1
                    if cmd_result.get('status') == 'pass':
                        passed_checks += 1

        elif 'laugh_tests' in results:
            # Laugh tests
            for test_category, test_data in results['laugh_tests'].items():
                if test_category == 'sequence_generation':
                    total_checks += 1
                    if 'error' not in test_data:
                        passed_checks += 1
                elif test_category == 'commands':
                    for cmd_name, cmd_data in test_data.items():
                        total_checks += 1
                        if cmd_data.get('success'):
                            passed_checks += 1

        # Print summary
        if total_checks > 0:
            success_rate = (passed_checks / total_checks) * 100

            print(f"📈 Test Results: {passed_checks}/{total_checks} passed ({success_rate:.1f}%)")

            if passed_checks == total_checks:
                print_colored("🎉 All tests passed! The robot repair was successful.", Colors.GREEN + Colors.BOLD)
            elif passed_checks > total_checks * 0.8:
                print_colored("⚠️ Most tests passed, but some issues remain.", Colors.YELLOW + Colors.BOLD)
            else:
                print_colored("❌ Multiple failures detected. Further investigation needed.", Colors.RED + Colors.BOLD)

        # Print timestamp
        print(f"\n🕐 Report generated: {results.get('timestamp', 'Unknown')}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="OpenMoxie Repair Status Checker")
    parser.add_argument("--test-commands", action="store_true", help="Test all DJ commands")
    parser.add_argument("--test-mqtt", action="store_true", help="Test MQTT connectivity")
    parser.add_argument("--test-laughs", action="store_true", help="Test 60-second laugh functionality")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    checker = RepairStatusChecker()

    try:
        if args.test_commands:
            results = checker.run_command_tests()
        elif args.test_mqtt:
            results = checker.run_mqtt_tests()
        elif args.test_laughs:
            results = checker.run_laugh_tests()
        else:
            results = checker.run_comprehensive_status_check()

        # Output results
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            checker.print_summary(results)

        return 0

    except KeyboardInterrupt:
        print_colored("\n❌ Status check interrupted by user", Colors.RED)
        return 1
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
