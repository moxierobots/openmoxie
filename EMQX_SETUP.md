# EMQX MQTT Broker Setup

This document describes the EMQX MQTT broker configuration for the OpenMoxie project, replacing HiveMQ with a lightweight, high-performance Erlang-based MQTT broker.

## Why EMQX?

- ✅ **No Java** - Written in Erlang, much lighter and faster
- ✅ **High Performance** - Handles millions of concurrent connections
- ✅ **Built-in Logging** - Comprehensive MQTT event logging out of the box
- ✅ **Web Dashboard** - Real-time monitoring and management
- ✅ **Multiple Protocols** - MQTT, WebSocket, and more
- ✅ **Easy Configuration** - Simple HOCON configuration format

## Configuration Files

### `site/data/emqx.conf`
Main EMQX configuration with:
- MQTT listeners on ports 1883 (unencrypted) and 8883 (TLS)
- WebSocket support on ports 8083 and 8084
- Anonymous access enabled for monitoring
- Dashboard on port 18083
- Prometheus metrics enabled

### `site/data/log.conf`
Logging configuration with:
- Console output for real-time monitoring
- Debug level logging for all MQTT events
- Specific loggers for connection, session, and message events

## Docker Configuration

### `emqx.Dockerfile`
- Based on EMQX 5.6.0 (latest stable)
- Lightweight and fast startup
- No Java dependencies

### `docker-compose.yml`
Updated to use EMQX with:
- Port mappings: 1883, 8883, 8083, 8084, 18083
- Volume mounts for configuration
- Environment variables for logging

## Features

### 🔓 Open Access
- **Anonymous connections allowed** - No authentication required
- **All clients can connect** - Perfect for monitoring and testing
- **Full topic access** - No ACL restrictions

### 📊 Comprehensive Logging
- **Connection events** - Client ID, IP address, protocol version
- **Authentication attempts** - Username/password logging
- **Message content** - All published messages with topic and payload
- **Session management** - Connect, disconnect, and session events
- **Real-time console output** - See logs immediately

### 🌐 Web Dashboard
- **Real-time monitoring** - Live connection and message statistics
- **Client management** - View connected clients and their details
- **Topic monitoring** - See active subscriptions and message flow
- **System metrics** - CPU, memory, and network usage

## Usage

### 1. Start the Services
```bash
docker-compose up -d
```

### 2. Test the Setup
```bash
./test_emqx.sh
```

### 3. Access the Dashboard
Open your browser to: http://localhost:18083
- Username: `admin`
- Password: `public`

### 4. Monitor Logs
```bash
# Real-time logs
docker-compose logs -f mqtt

# Follow logs with timestamps
docker-compose logs -f -t mqtt

# Filter for specific events
docker-compose logs -f mqtt | grep "CONNECT"
```

### 5. Test MQTT Connections

#### Unencrypted MQTT (port 1883)
```bash
# Publish a message
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "Hello EMQX!"

# Subscribe to messages
mosquitto_sub -h localhost -p 1883 -t "test/#" -v
```

#### WebSocket MQTT (port 8083)
```bash
# Test WebSocket connection
wscat -c ws://localhost:8083/mqtt
```

#### With Authentication (logged but not enforced)
```bash
# Publish with username/password
mosquitto_pub -h localhost -p 1883 -u "testuser" -P "testpass" -t "test/auth" -m "Authenticated message"

# Subscribe with authentication
mosquitto_sub -h localhost -p 1883 -u "testuser" -P "testpass" -t "test/#" -v
```

## Log Output Examples

### Connection Logging
```
2024-01-15T10:30:45.123+00:00 [debug] emqx.connection: Client test-client-123@127.0.0.1:54321 connected
2024-01-15T10:30:45.124+00:00 [debug] emqx.session: Session started for client test-client-123
2024-01-15T10:30:45.125+00:00 [debug] emqx.auth: Authentication attempt for client test-client-123, username: testuser
```

### Message Logging
```
2024-01-15T10:30:46.200+00:00 [debug] emqx.pubsub: Message published to topic test/openmoxie by client test-client-123
2024-01-15T10:30:46.201+00:00 [debug] emqx.pubsub: Message content: "Hello from OpenMoxie!"
2024-01-15T10:30:46.202+00:00 [debug] emqx.pubsub: Message QoS: 0, Retain: false
```

### Session Logging
```
2024-01-15T10:30:47.300+00:00 [debug] emqx.session: Client test-client-123 disconnected, reason: normal
2024-01-15T10:30:47.301+00:00 [debug] emqx.connection: Connection closed for client test-client-123
```

## Dashboard Features

### Real-time Monitoring
- **Connected Clients** - Live count and details
- **Message Rate** - Messages per second
- **Topic Statistics** - Most active topics
- **System Resources** - CPU, memory, disk usage

### Client Management
- **Client List** - All connected clients with details
- **Client Details** - IP, protocol, subscriptions, messages
- **Disconnect Clients** - Force disconnect if needed

### Topic Management
- **Active Subscriptions** - Live subscription list
- **Message History** - Recent messages per topic
- **Topic Tree** - Hierarchical topic view

## Performance Benefits

### vs HiveMQ (Java)
- ✅ **Faster startup** - No JVM warmup
- ✅ **Lower memory usage** - ~50MB vs ~200MB+
- ✅ **Better concurrency** - Erlang's actor model
- ✅ **No garbage collection pauses** - Erlang's per-process GC

### vs Mosquitto
- ✅ **Better logging** - Built-in comprehensive logging
- ✅ **Web dashboard** - Real-time monitoring
- ✅ **More protocols** - WebSocket, HTTP API
- ✅ **Better scalability** - Handles more connections

## Configuration Details

### MQTT Settings
- **Max connections**: 1000
- **Max packet size**: 1MB
- **Keep alive**: 65535 seconds
- **Session expiry**: 2 hours
- **Max inflight**: 32 messages

### Logging Settings
- **Level**: DEBUG (all events)
- **Output**: Console (stdout)
- **Format**: Text with timestamps
- **Specific loggers**: Connection, session, pubsub, auth

### Security Settings
- **Anonymous access**: Enabled
- **Authentication**: Optional (logged but not enforced)
- **Authorization**: Allow all operations
- **TLS**: Available on port 8883

## Troubleshooting

### Common Issues

1. **Connection refused**
   - Check if EMQX is running: `docker-compose ps`
   - Verify ports are exposed: `docker-compose port mqtt 1883`
   - Check logs: `docker-compose logs mqtt`

2. **No logs appearing**
   - Verify log configuration is mounted
   - Check environment variables
   - Ensure console handler is enabled

3. **Dashboard not accessible**
   - Check port 18083 is exposed
   - Verify EMQX is fully started
   - Check firewall settings

### Debug Commands
```bash
# Check container status
docker-compose ps

# View real-time logs
docker-compose logs -f mqtt

# Check EMQX status
docker-compose exec mqtt /opt/emqx/bin/emqx_ctl status

# View configuration
docker-compose exec mqtt cat /opt/emqx/etc/emqx.conf
```

## Monitoring

### Prometheus Metrics
Access metrics at: `http://localhost:18083/api/v5/prometheus/stats`

### Log Analysis
```bash
# Count connections by client
docker-compose logs mqtt | grep "connected" | wc -l

# Find authentication attempts
docker-compose logs mqtt | grep "Authentication attempt"

# Monitor message volume
docker-compose logs mqtt | grep "Message published" | wc -l
```

## Migration from HiveMQ

### Benefits of EMQX
1. **No Java** - Eliminates JVM overhead
2. **Better logging** - More detailed MQTT event logging
3. **Web dashboard** - Real-time monitoring interface
4. **Better performance** - Handles more concurrent connections
5. **Easier configuration** - HOCON format vs XML

### Configuration Changes
- Replaced HiveMQ XML config with EMQX HOCON
- Removed Java extension (not needed)
- Added WebSocket support
- Enhanced logging configuration

This setup provides excellent MQTT performance with comprehensive logging and monitoring capabilities, all without the overhead of Java!
