# OpenMoxie Development Environment

This document describes the development environment setup for OpenMoxie, a local network hub for Embodied Moxie Robots.

## Quick Start

1. **Run the setup script:**
   ```bash
   ./setup-dev.sh
   ```

2. **Edit your .env file** with your AI API keys:
   ```bash
   nano .env
   # Add your AI service keys:
   # OPENAI_API_KEY=your_openai_key_here
   # ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

3. **Start the development environment:**
   ```bash
   ./dev-start.sh
   ```

4. **Visit the application:**
   - Web interface: http://localhost:8000/hive
   - Django admin: http://localhost:8000/admin
   - MQTT Dashboard: http://localhost:18083 (admin/public)

## Development Scripts

### Core Scripts
- `setup-dev.sh` - Initial setup (run once)
- `dev-start.sh` - Start development server with MQTT broker
- `dev-stop.sh` - Stop all services

### Code Quality Scripts
- `dev-fix.sh` - Auto-format code with Black and isort
- `dev-check.sh` - Run all quality checks (linting, type checking, tests)

## Project Structure

```
openmoxie/
├── site/                 # Django application
│   ├── manage.py        # Django management commands
│   ├── openmoxie/       # Main Django project
│   └── hive/            # Main application logic
├── content_modules/     # Moxie conversation content
├── venv/               # Python virtual environment
├── local/              # Runtime data (logs, database)
├── .env               # Environment variables
└── docker-compose.yml # MQTT broker configuration
```

## Development Workflow

### 1. Making Code Changes
```bash
# Activate virtual environment
source venv/bin/activate

# Make your changes to the code
# ...

# Format and check code
./dev-fix.sh
./dev-check.sh
```

### 2. Running Tests
```bash
# Run all tests
cd site && python -m pytest

# Run with coverage
cd site && python -m pytest --cov=.

# Run specific test file
cd site && python -m pytest hive/tests/test_models.py
```

### 3. Django Management
```bash
source venv/bin/activate

# Create migrations
python site/manage.py makemigrations

# Apply migrations
python site/manage.py migrate

# Create superuser
python site/manage.py createsuperuser

# Load initial data
python site/manage.py init_data
```

### 4. MQTT Debugging
```bash
# View MQTT logs
docker-compose logs mqtt

# Access MQTT dashboard
# Visit http://localhost:18083 (admin/public)
```

### 5. AI Services Testing
```bash
# Test Claude integration
python test_claude_integration.py

# The test will check:
# - Environment configuration
# - API connectivity
# - Service functionality
```

## Code Quality Tools

### Black (Code Formatting)
- Configuration: `pyproject.toml` [tool.black]
- Usage: `black site/` or `./dev-fix.sh`

### isort (Import Sorting)
- Configuration: `pyproject.toml` [tool.isort]
- Usage: `isort site/` or `./dev-fix.sh`

### flake8 (Linting)
- Configuration: `.flake8`
- Usage: `flake8 site/` or `./dev-check.sh`

### mypy (Type Checking)
- Configuration: `pyproject.toml` [tool.mypy]
- Usage: `mypy site/` or `./dev-check.sh`

### pytest (Testing)
- Configuration: `pyproject.toml` [tool.pytest.ini_options]
- Usage: `pytest` or `./dev-check.sh`

### bandit (Security Scanning)
- Usage: `bandit -r site/` or `./dev-check.sh`

## Environment Variables

Key variables in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True for development)
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models
- `CLAUDE_MODEL` - Claude model to use (default: claude-3-5-sonnet-20241022)
- `MQTT_HOST` - MQTT broker hostname (default: mqtt)
- `DB_HOST` - Database host (postgres for production, sqlite for dev)

## VS Code Setup

Recommended VS Code extensions:
```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "batisteo.vscode-django",
        "ms-python.debugpy"
    ]
}
```

## Troubleshooting

### Common Issues

1. **"Virtual environment not found"**
   ```bash
   ./setup-dev.sh
   ```

2. **"MQTT connection failed"**
   ```bash
   docker-compose up -d mqtt
   ```

3. **"Database migration error"**
   ```bash
   source venv/bin/activate
   python site/manage.py migrate
   ```

4. **"AI API key not set"**
   - Edit `.env` file and add your API keys:
   - `OPENAI_API_KEY=your_openai_key_here`
   - `ANTHROPIC_API_KEY=your_anthropic_key_here`

5. **"Claude integration test fails"**
   ```bash
   python test_claude_integration.py
   ```

### Docker Issues
```bash
# Restart all services
docker-compose down && docker-compose up -d

# View logs
docker-compose logs

# Rebuild containers
docker-compose build --no-cache
```

### Python Issues
```bash
# Reinstall dependencies
rm -rf venv
./setup-dev.sh
```

## Contributing

1. Make your changes
2. Run `./dev-fix.sh` to format code
3. Run `./dev-check.sh` to verify quality
4. Ensure all tests pass
5. Commit your changes

## AI Services

### Supported AI Providers

OpenMoxie supports multiple AI providers for robot conversations:

#### OpenAI (GPT Models)
- **Models**: GPT-3.5, GPT-4, etc.
- **Configuration**: `OPENAI_API_KEY` in `.env`
- **Usage**: Existing integration for chat functionality

#### Anthropic Claude
- **Models**: Claude 3.5 Sonnet (recommended), Claude 3 Opus, Claude 3 Haiku
- **Configuration**: `ANTHROPIC_API_KEY` and `CLAUDE_MODEL` in `.env`
- **Usage**: New integration for enhanced conversational AI

### Usage Examples

#### Using Claude Service
```python
from hive.mqtt.claude_service import get_claude_service

# Initialize service
service = get_claude_service()
service.initialize()

# Simple chat
response = service.create_simple_chat(
    system_prompt="You are Moxie, a friendly robot companion.",
    user_message="Hello! How can I help you today?"
)

# Conversation management
conversation = service.create_conversation(
    system_prompt="You are a helpful robot assistant."
)
response1 = service.generate_response(conversation, "What's the weather?")
response2 = service.generate_response(conversation, "Tell me more about that")
```

#### Testing AI Integration
```bash
# Test Claude integration
python test_claude_integration.py

# This will verify:
# - API key configuration
# - Network connectivity
# - Service functionality
# - Response generation
```

## Additional Resources

- [OpenMoxie README](README.md) - Project overview and usage
- [Django Documentation](https://docs.djangoproject.com/)
- [MQTT Documentation](https://mqtt.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
