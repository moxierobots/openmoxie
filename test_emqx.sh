#!/bin/bash

# EMQX Test Script
# ================
# This script tests the EMQX MQTT broker setup

set -e

echo "Testing EMQX MQTT Broker Setup"
echo "==============================="

# Check if mosquitto clients are available
if ! command -v mosquitto_pub &> /dev/null; then
    echo "Error: mosquitto_pub command not found."
    echo "Please install mosquitto-clients package:"
    echo "  macOS: brew install mosquitto"
    echo "  Ubuntu/Debian: sudo apt-get install mosquitto-clients"
    echo "  CentOS/RHEL: sudo yum install mosquitto"
    exit 1
fi

# Test unencrypted connection (port 1883)
echo ""
echo "Testing unencrypted MQTT connection (port 1883)..."
mosquitto_pub -h localhost -p 1883 -t "test/openmoxie" -m "Hello from OpenMoxie!" -d

# Test with username/password (if authentication is enabled)
echo ""
echo "Testing MQTT connection with authentication..."
mosquitto_pub -h localhost -p 1883 -u "testuser" -P "testpass" -t "test/auth" -m "Authenticated message" -d

# Test TLS connection (port 8883) - this will fail without proper certificates
echo ""
echo "Testing TLS MQTT connection (port 8883)..."
echo "Note: This will fail without proper TLS certificates"
mosquitto_pub -h localhost -p 8883 -t "test/tls" -m "TLS message" -d || echo "TLS test failed (expected without certificates)"

# Test subscription
echo ""
echo "Testing MQTT subscription..."
echo "Run this in another terminal to see messages:"
echo "mosquitto_sub -h localhost -p 1883 -t 'test/#' -v"

echo ""
echo "EMQX test completed!"
echo ""
echo "EMQX Dashboard: http://localhost:18083"
echo "Username: admin, Password: public"
echo ""
echo "To monitor logs in real-time (stdout):"
echo "docker-compose logs -f mqtt"
echo ""
echo "To follow logs with timestamps:"
echo "docker-compose logs -f -t mqtt"
echo ""
echo "All logs are sent to stdout with detailed MQTT event logging."
