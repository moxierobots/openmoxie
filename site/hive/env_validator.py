"""
Environment variable validation for OpenMoxie
"""
import os
import sys
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails"""
    pass


def validate_required_env_vars() -> Dict[str, Any]:
    """
    Validate required environment variables for OpenMoxie
    Returns a dict of validated values
    """
    validation_results = {}
    errors = []
    warnings = []
    
    # Required environment variables
    required_vars = {
        'SECRET_KEY': {
            'description': 'Django secret key for cryptographic signing',
            'min_length': 50,
            'required': True
        },
        'DJANGO_ENV': {
            'description': 'Django environment (development, staging, production)',
            'allowed_values': ['development', 'staging', 'production'],
            'required': False,
            'default': 'development'
        }
    }
    
    # Production-specific required variables
    production_required = {
        'ALLOWED_HOSTS': {
            'description': 'Comma-separated list of allowed hosts',
            'required': True
        },
        'DB_HOST': {
            'description': 'Database host',
            'required': True
        },
        'DB_PASSWORD': {
            'description': 'Database password',
            'required': True
        }
    }
    
    # Optional but recommended variables
    optional_vars = {
        'SENTRY_DSN': {
            'description': 'Sentry DSN for error tracking',
            'required': False
        },
        'CACHE_LOCATION': {
            'description': 'Cache location (Redis URL or similar)',
            'required': False
        }
    }
    
    # Get current environment
    django_env = os.getenv('DJANGO_ENV', 'development')
    validation_results['DJANGO_ENV'] = django_env
    
    # Validate base required variables
    for var_name, config in required_vars.items():
        if var_name == 'DJANGO_ENV':  # Already handled above
            continue
            
        value = os.getenv(var_name)
        
        if not value and config.get('required', True):
            errors.append(f"Required environment variable {var_name} is not set: {config['description']}")
            continue
        elif not value and 'default' in config:
            value = config['default']
            validation_results[var_name] = value
            continue
        
        # Validate length if specified
        if 'min_length' in config and len(value) < config['min_length']:
            errors.append(f"{var_name} must be at least {config['min_length']} characters long")
        
        # Validate allowed values if specified
        if 'allowed_values' in config and value not in config['allowed_values']:
            errors.append(f"{var_name} must be one of: {', '.join(config['allowed_values'])}")
        
        validation_results[var_name] = value
    
    # Production-specific validation
    if django_env == 'production':
        for var_name, config in production_required.items():
            value = os.getenv(var_name)
            
            if not value:
                errors.append(f"Production environment requires {var_name}: {config['description']}")
            else:
                validation_results[var_name] = value
    
    # Check optional but recommended variables
    for var_name, config in optional_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            warnings.append(f"Optional variable {var_name} not set: {config['description']}")
        else:
            validation_results[var_name] = value
    
    # Additional validations
    
    # Check SECRET_KEY security
    secret_key = validation_results.get('SECRET_KEY')
    if secret_key and django_env == 'production':
        if 'django-insecure' in secret_key.lower():
            errors.append("Production SECRET_KEY appears to be a development key (contains 'django-insecure')")
    
    # Check database configuration
    db_engine = os.getenv('DB_ENGINE', 'postgresql')
    if django_env == 'production' and db_engine == 'sqlite3':
        warnings.append("Using SQLite in production is not recommended for performance and concurrency")
    
    # Check SSL configuration in production
    if django_env == 'production':
        if os.getenv('SECURE_SSL_REDIRECT', 'false').lower() != 'true':
            warnings.append("SECURE_SSL_REDIRECT should be enabled in production")
        
        if os.getenv('SESSION_COOKIE_SECURE', 'false').lower() != 'true':
            warnings.append("SESSION_COOKIE_SECURE should be enabled in production")
        
        if os.getenv('CSRF_COOKIE_SECURE', 'false').lower() != 'true':
            warnings.append("CSRF_COOKIE_SECURE should be enabled in production")
    
    # Log results
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        raise EnvironmentValidationError(f"Environment validation failed: {'; '.join(errors)}")
    
    if warnings:
        logger.warning("Environment validation warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info(f"Environment validation passed for {django_env} environment")
    return validation_results


def validate_openai_configuration():
    """
    Validate OpenAI configuration
    """
    from .models import HiveConfiguration
    
    try:
        config = HiveConfiguration.get_current()
        if not config.openai_api_key:
            logger.warning("OpenAI API key not configured - speech-to-text features will not work")
            return False
        
        # Basic format check
        api_key = config.openai_api_key
        if not api_key.startswith(('sk-', 'sk-proj-')):
            logger.warning("OpenAI API key format appears invalid (should start with 'sk-' or 'sk-proj-')")
        
        logger.info("OpenAI configuration validated successfully")
        return True
        
    except Exception as e:
        logger.warning(f"Could not validate OpenAI configuration: {str(e)}")
        return False


def check_system_requirements():
    """
    Check system requirements and dependencies
    """
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check required Python packages
    required_packages = [
        'django',
        'paho-mqtt',
        'openai',
        'soundfile',
        'numpy',
        'pillow'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            issues.append(f"Required Python package '{package}' not found")
    
    # Check for system dependencies
    system_deps = {
        'libsndfile1': 'apt-get install libsndfile1',  # For soundfile
    }
    
    if issues:
        logger.error("System requirements check failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    
    logger.info("System requirements check passed")
    return True


def run_startup_validation():
    """
    Run all validation checks at startup
    """
    logger.info("Starting OpenMoxie environment validation...")
    
    try:
        # Validate environment variables
        env_results = validate_required_env_vars()
        
        # Check system requirements
        system_ok = check_system_requirements()
        
        # Validate OpenAI configuration (non-blocking)
        validate_openai_configuration()
        
        logger.info("✅ OpenMoxie environment validation completed successfully")
        return True
        
    except EnvironmentValidationError as e:
        logger.error(f"❌ Environment validation failed: {str(e)}")
        logger.error("OpenMoxie cannot start with invalid environment configuration")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during validation: {str(e)}")
        return False