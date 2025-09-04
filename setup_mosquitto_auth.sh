#!/bin/bash

# Mosquitto Authentication Setup Script
# ====================================
# This script helps set up user authentication for the Mosquitto MQTT broker

set -e

# Configuration
PASSWD_FILE="/Users/pratikgajjar/dopemind/openmoxie/site/data/passwd"
ACL_FILE="/Users/pratikgajjar/dopemind/openmoxie/site/data/acl"

echo "Setting up Mosquitto authentication..."

# Check if mosquitto_passwd is available
if ! command -v mosquitto_passwd &> /dev/null; then
    echo "Error: mosquitto_passwd command not found."
    echo "Please install mosquitto-clients package:"
    echo "  macOS: brew install mosquitto"
    echo "  Ubuntu/Debian: sudo apt-get install mosquitto-clients"
    echo "  CentOS/RHEL: sudo yum install mosquitto"
    exit 1
fi

# Create password file if it doesn't exist
if [ ! -f "$PASSWD_FILE" ]; then
    echo "Creating password file..."
    touch "$PASSWD_FILE"
fi

# Function to add user
add_user() {
    local username=$1
    local password=$2
    
    if [ -z "$password" ]; then
        echo "Adding user '$username' (you'll be prompted for password):"
        mosquitto_passwd "$PASSWD_FILE" "$username"
    else
        echo "Adding user '$username' with provided password:"
        mosquitto_passwd -b "$PASSWD_FILE" "$username" "$password"
    fi
}

# Add default users
echo "Adding default users..."

# Add admin user
read -p "Enter password for 'admin' user: " -s admin_pass
echo
add_user "admin" "$admin_pass"

# Add moxie user
read -p "Enter password for 'moxie' user: " -s moxie_pass
echo
add_user "moxie" "$moxie_pass"

# Add client user
read -p "Enter password for 'client' user: " -s client_pass
echo
add_user "client" "$client_pass"

echo "Authentication setup complete!"
echo ""
echo "Users created:"
echo "- admin: Full access to all topics"
echo "- moxie: Access to moxie/* and system topics"
echo "- client: Limited access to status and commands"
echo ""
echo "Password file: $PASSWD_FILE"
echo "ACL file: $ACL_FILE"
echo ""
echo "To add more users later, run:"
echo "  mosquitto_passwd $PASSWD_FILE <username>"
echo ""
echo "To test the configuration:"
echo "  mosquitto -c /Users/pratikgajjar/dopemind/openmoxie/site/data/openmoxie.conf -v"
