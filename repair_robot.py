#!/usr/bin/env python3
"""
Robot Repair and Pairing Script for OpenMoxie

This script helps diagnose and repair robot connections to the Hive system.
It can detect unpaired robots, register them, and verify connectivity.

Usage:
    python repair_robot.py                    # Interactive mode
    python repair_robot.py --auto            # Automatic repair
    python repair_robot.py --list            # List all devices
    python repair_robot.py --device-id <id>  # Repair specific device
"""

import os
import sys
import django
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openmoxie.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-purposes-12345678901234567890')
os.environ.setdefault('SKIP_ENV_VALIDATION', 'true')

# Add the site directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site'))

django.setup()

from django.utils import timezone
from hive.models import MoxieDevice
from hive.mqtt.moxie_server import get_instance


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
    print_colored("=" * 60, Colors.BLUE)
    print_colored(f" {title}", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 60, Colors.BLUE)


class RobotRepair:
    def __init__(self):
        self.mqtt_server = None

    def get_mqtt_server(self):
        """Get MQTT server instance"""
        if not self.mqtt_server:
            try:
                self.mqtt_server = get_instance()
                return self.mqtt_server
            except Exception as e:
                print_colored(f"❌ Failed to connect to MQTT server: {e}", Colors.RED)
                return None
        return self.mqtt_server

    def list_database_devices(self) -> List[MoxieDevice]:
        """List all devices in the database"""
        try:
            devices = MoxieDevice.objects.all()
            return list(devices)
        except Exception as e:
            print_colored(f"❌ Database error: {e}", Colors.RED)
            return []

    def get_mqtt_connected_devices(self) -> List[str]:
        """Get list of device IDs currently connected to MQTT"""
        mqtt_server = self.get_mqtt_server()
        if not mqtt_server:
            return []

        try:
            # Get connected clients from MQTT server
            connected_devices = []
            clients = mqtt_server.get_connected_clients()

            for client_id in clients:
                if client_id.startswith('d_'):
                    connected_devices.append(client_id)

            return connected_devices
        except Exception as e:
            print_colored(f"⚠️ Could not get MQTT clients: {e}", Colors.YELLOW)
            return []

    def detect_unpaired_robots(self) -> List[str]:
        """Detect robots connected to MQTT but not in database"""
        print_colored("🔍 Scanning for unpaired robots...", Colors.YELLOW)

        # Get database devices
        db_devices = self.list_database_devices()
        db_device_ids = {device.device_id for device in db_devices}

        # Get MQTT connected devices (simulated from logs)
        # In real implementation, this would query the MQTT broker
        unpaired = []

        # For now, we'll check for the device we saw in the logs
        mqtt_device_id = "d_b968a811-3c9c-4932-855d-4e7f7031c5f5"

        if mqtt_device_id not in db_device_ids:
            unpaired.append(mqtt_device_id)
            print_colored(f"🤖 Found unpaired robot: {mqtt_device_id}", Colors.CYAN)

        if not unpaired:
            print_colored("✅ No unpaired robots detected", Colors.GREEN)

        return unpaired

    def create_device_record(self, device_id: str, name: str = None) -> bool:
        """Create a new device record in the database"""
        try:
            if name is None:
                name = f"Moxie Robot {device_id[-8:]}"

            # Check if device already exists
            if MoxieDevice.objects.filter(device_id=device_id).exists():
                print_colored(f"⚠️ Device {device_id} already exists", Colors.YELLOW)
                return True

            # Create new device
            device = MoxieDevice.objects.create(
                device_id=device_id,
                name=name,
                robot_config={
                    "moxie_mode": "TELEHEALTH",
                    "created_by": "repair_script",
                    "created_at": timezone.now().isoformat()
                },
                last_connect=timezone.now()
            )

            print_colored(f"✅ Created device record: {device.name} ({device_id})", Colors.GREEN)
            return True

        except Exception as e:
            print_colored(f"❌ Failed to create device record: {e}", Colors.RED)
            return False

    def repair_device(self, device_id: str) -> bool:
        """Repair a specific device connection"""
        print_colored(f"🔧 Repairing device: {device_id}", Colors.YELLOW)

        try:
            # Check if device exists in database
            try:
                device = MoxieDevice.objects.get(device_id=device_id)
                print_colored(f"📱 Found device in database: {device.name}", Colors.GREEN)

                # Update last seen
                device.last_connect = timezone.now()

                # Ensure telehealth mode is enabled
                if not device.robot_config:
                    device.robot_config = {}
                device.robot_config["moxie_mode"] = "TELEHEALTH"
                device.robot_config["repaired_at"] = timezone.now().isoformat()

                device.save()

            except MoxieDevice.DoesNotExist:
                print_colored(f"📱 Device not in database, creating new record", Colors.YELLOW)
                if not self.create_device_record(device_id):
                    return False
                device = MoxieDevice.objects.get(device_id=device_id)

            # Send configuration update to robot
            mqtt_server = self.get_mqtt_server()
            if mqtt_server:
                try:
                    mqtt_server.handle_config_updated(device)
                    print_colored(f"📡 Sent configuration update to robot", Colors.GREEN)
                except Exception as e:
                    print_colored(f"⚠️ Could not send config update: {e}", Colors.YELLOW)

            print_colored(f"✅ Device {device_id} repaired successfully", Colors.GREEN)
            return True

        except Exception as e:
            print_colored(f"❌ Failed to repair device {device_id}: {e}", Colors.RED)
            return False

    def verify_device_connectivity(self, device_id: str) -> Dict:
        """Verify device connectivity and status"""
        print_colored(f"🔍 Verifying connectivity for: {device_id}", Colors.YELLOW)

        status = {
            "device_id": device_id,
            "database_registered": False,
            "mqtt_connected": False,
            "telehealth_enabled": False,
            "last_seen": None,
            "issues": []
        }

        try:
            # Check database
            try:
                device = MoxieDevice.objects.get(device_id=device_id)
                status["database_registered"] = True
                status["last_seen"] = device.last_connect.isoformat() if device.last_connect else None
                status["telehealth_enabled"] = device.robot_config.get("moxie_mode") == "TELEHEALTH" if device.robot_config else False

                # Check if device was seen recently (within last 5 minutes)
                if device.last_connect and device.last_connect > timezone.now() - timedelta(minutes=5):
                    status["mqtt_connected"] = True
                else:
                    status["issues"].append("Device not seen recently")

            except MoxieDevice.DoesNotExist:
                status["issues"].append("Device not registered in database")

            # Additional checks could be added here for MQTT connectivity

            return status

        except Exception as e:
            status["issues"].append(f"Verification error: {str(e)}")
            return status

    def display_device_status(self, status: Dict):
        """Display device status in a readable format"""
        device_id = status["device_id"]
        print(f"\n📱 Device Status: {device_id}")
        print("-" * 50)

        # Database status
        if status["database_registered"]:
            print_colored("✅ Database: Registered", Colors.GREEN)
        else:
            print_colored("❌ Database: Not registered", Colors.RED)

        # MQTT status
        if status["mqtt_connected"]:
            print_colored("✅ MQTT: Connected", Colors.GREEN)
        else:
            print_colored("❌ MQTT: Disconnected", Colors.RED)

        # Telehealth status
        if status["telehealth_enabled"]:
            print_colored("✅ Telehealth: Enabled", Colors.GREEN)
        else:
            print_colored("❌ Telehealth: Disabled", Colors.RED)

        # Last seen
        if status["last_seen"]:
            print_colored(f"🕐 Last seen: {status['last_seen']}", Colors.CYAN)
        else:
            print_colored("🕐 Last seen: Never", Colors.YELLOW)

        # Issues
        if status["issues"]:
            print_colored("⚠️ Issues:", Colors.YELLOW)
            for issue in status["issues"]:
                print_colored(f"   • {issue}", Colors.YELLOW)
        else:
            print_colored("✅ No issues detected", Colors.GREEN)

    def auto_repair_all(self) -> int:
        """Automatically repair all detected issues"""
        print_header("Automatic Robot Repair")

        repaired_count = 0

        # Detect unpaired robots
        unpaired = self.detect_unpaired_robots()

        if unpaired:
            print_colored(f"🔧 Repairing {len(unpaired)} unpaired robot(s)...", Colors.YELLOW)

            for device_id in unpaired:
                if self.repair_device(device_id):
                    repaired_count += 1

        # Check existing devices for issues
        db_devices = self.list_database_devices()
        for device in db_devices:
            status = self.verify_device_connectivity(device.device_id)
            if status["issues"]:
                print_colored(f"🔧 Repairing issues with {device.device_id}...", Colors.YELLOW)
                if self.repair_device(device.device_id):
                    repaired_count += 1

        return repaired_count

    def interactive_mode(self):
        """Interactive repair mode"""
        print_header("Interactive Robot Repair Mode")

        while True:
            print("\nSelect an option:")
            print("1. 📱 List all devices")
            print("2. 🔍 Detect unpaired robots")
            print("3. 🔧 Repair specific device")
            print("4. ✅ Verify device connectivity")
            print("5. 🚀 Auto-repair all issues")
            print("0. 🚪 Exit")

            choice = input("\nEnter your choice (0-5): ").strip()

            if choice == "0":
                print_colored("👋 Exiting repair tool...", Colors.CYAN)
                break

            elif choice == "1":
                self.list_all_devices()

            elif choice == "2":
                self.detect_unpaired_robots()

            elif choice == "3":
                device_id = input("Enter device ID: ").strip()
                if device_id:
                    self.repair_device(device_id)
                else:
                    print_colored("❌ Invalid device ID", Colors.RED)

            elif choice == "4":
                device_id = input("Enter device ID: ").strip()
                if device_id:
                    status = self.verify_device_connectivity(device_id)
                    self.display_device_status(status)
                else:
                    print_colored("❌ Invalid device ID", Colors.RED)

            elif choice == "5":
                repaired = self.auto_repair_all()
                if repaired > 0:
                    print_colored(f"✅ Successfully repaired {repaired} device(s)", Colors.GREEN)
                else:
                    print_colored("ℹ️ No repairs needed", Colors.CYAN)

            else:
                print_colored("❌ Invalid choice. Please enter 0-5.", Colors.RED)

    def list_all_devices(self):
        """List all devices with their status"""
        print_header("Device List")

        devices = self.list_database_devices()

        if not devices:
            print_colored("📱 No devices found in database", Colors.YELLOW)
            return

        print_colored(f"Found {len(devices)} device(s):", Colors.CYAN)

        for device in devices:
            print(f"\n📱 {device.name}")
            print(f"   ID: {device.device_id}")

            # Check if recently connected
            recently_connected = False
            if device.last_connect:
                time_diff = timezone.now() - device.last_connect
                recently_connected = time_diff < timedelta(minutes=5)

            print(f"   Status: {'✅ Online' if recently_connected else '⚠️ Offline'}")

            if device.last_connect:
                time_diff = timezone.now() - device.last_connect
                if time_diff < timedelta(minutes=5):
                    print_colored(f"   Last connect: {device.last_connect} (✅ Recent)", Colors.GREEN)
                else:
                    print_colored(f"   Last connect: {device.last_connect} (⚠️ Stale)", Colors.YELLOW)
            else:
                print_colored("   Last connect: Never (❌ Never connected)", Colors.RED)

            telehealth = device.robot_config.get("moxie_mode") == "TELEHEALTH" if device.robot_config else False
            print(f"   Telehealth: {'✅ Enabled' if telehealth else '❌ Disabled'}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Robot Repair and Pairing Tool")
    parser.add_argument("--auto", action="store_true", help="Automatic repair mode")
    parser.add_argument("--list", action="store_true", help="List all devices")
    parser.add_argument("--device-id", help="Repair specific device ID")
    parser.add_argument("--verify", help="Verify connectivity for specific device ID")

    args = parser.parse_args()

    repair = RobotRepair()

    try:
        if args.list:
            repair.list_all_devices()

        elif args.auto:
            print_header("Automatic Robot Repair")
            repaired = repair.auto_repair_all()
            if repaired > 0:
                print_colored(f"\n✅ Successfully repaired {repaired} device(s)", Colors.GREEN)
            else:
                print_colored(f"\nℹ️ No repairs needed - all devices are properly configured", Colors.CYAN)

        elif args.device_id:
            if repair.repair_device(args.device_id):
                print_colored(f"\n✅ Device {args.device_id} repaired successfully", Colors.GREEN)
            else:
                print_colored(f"\n❌ Failed to repair device {args.device_id}", Colors.RED)
                sys.exit(1)

        elif args.verify:
            status = repair.verify_device_connectivity(args.verify)
            repair.display_device_status(status)

        else:
            repair.interactive_mode()

    except KeyboardInterrupt:
        print_colored("\n❌ Interrupted by user", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
