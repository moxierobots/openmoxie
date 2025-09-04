# Mosquitto MQTT Broker Security Configuration

This document describes the secure configuration setup for the Mosquitto MQTT broker used in the OpenMoxie project.

## Security Improvements Made

### 1. Authentication & Authorization
- **Disabled anonymous access** on the secure port (8883)
- **Added password-based authentication** with hashed passwords
- **Implemented Access Control Lists (ACLs)** for topic-based permissions
- **Required client certificates** for TLS connections

### 2. Network Security
- **TLS encryption** on port 8883 with client certificate verification
- **Local-only unencrypted listener** on port 1883 (127.0.0.1) for internal services
- **Connection limits** to prevent resource exhaustion

### 3. Verbose Logging
- **Comprehensive logging** including debug, info, warning, and error levels
- **Timestamped logs** with ISO format
- **Multiple log destinations** (file and MQTT topic)

## Configuration Files

### `site/data/openmoxie.conf`
Main Mosquitto configuration file with security settings.

### `site/data/passwd`
Password file containing hashed user credentials.

### `site/data/acl`
Access Control List defining topic permissions for each user.

## User Accounts

The configuration includes three default user accounts:

1. **admin** - Full access to all topics
2. **moxie** - Access to moxie/* and system topics
3. **client** - Limited access to status and commands

## Setup Instructions

### 1. Run the Authentication Setup Script
```bash
./setup_mosquitto_auth.sh
```

This script will:
- Create the password file with hashed passwords
- Set up the three default users
- Guide you through password creation

### 2. Verify Configuration
```bash
mosquitto -c site/data/openmoxie.conf -v
```

### 3. Test Client Connection
```bash
# Test with username/password
mosquitto_pub -h localhost -p 8883 -u moxie -P <password> -t "test/topic" -m "Hello World"

# Test with client certificate
mosquitto_pub -h localhost -p 8883 --cafile keys/ca.crt --cert keys/client.crt --key keys/client.key -t "test/topic" -m "Hello World"
```

## Security Features

### Certificate-Based Authentication
- Clients must present valid certificates
- Certificate Common Name (CN) is used as username
- Mutual TLS authentication

### Topic-Based Access Control
- Granular permissions per user
- Wildcard support for topic patterns
- Separate read/write permissions

### Connection Security
- Maximum connection limits
- Message size limits
- Keep-alive timeouts
- Inflight message limits

### Logging & Monitoring
- Verbose logging for security monitoring
- Connection tracking via MQTT topics
- Timestamped log entries

## Docker Integration

When using Docker, ensure the following volumes are mounted:
- `/mosquitto/config/` - Configuration files
- `/mosquitto/log/` - Log files
- `/mosquitto/data/` - Persistence data

## Troubleshooting

### Common Issues

1. **Authentication failures**
   - Verify password file exists and is readable
   - Check username/password combinations
   - Ensure proper file permissions

2. **Certificate errors**
   - Verify certificate files exist
   - Check certificate validity and expiration
   - Ensure proper certificate chain

3. **ACL permission denied**
   - Check topic patterns in ACL file
   - Verify user has appropriate permissions
   - Test with admin user first

### Log Analysis
Check the log file for detailed error messages:
```bash
tail -f site/data/logs/mosquitto.log
```

## Security Best Practices

1. **Regular password rotation**
2. **Certificate renewal before expiration**
3. **Monitor access logs for suspicious activity**
4. **Keep Mosquitto updated to latest version**
5. **Use strong, unique passwords**
6. **Regular backup of configuration files**

## File Permissions

Ensure proper file permissions:
```bash
chmod 600 site/data/passwd
chmod 644 site/data/acl
chmod 644 site/data/openmoxie.conf
```
