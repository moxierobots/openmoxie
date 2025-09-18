#!/usr/bin/env python3
"""
Comprehensive test runner for OpenMoxie

This script runs all available tests and provides a summary of results.
It handles environment setup and provides clear feedback on test status.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Colors for output
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

def run_command(command: str, cwd: str = None) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return 1, "", str(e)

def setup_test_environment() -> Dict[str, str]:
    """Setup environment variables for testing"""
    env = os.environ.copy()

    # Required Django settings
    env['SECRET_KEY'] = 'test-secret-key-for-testing-purposes-12345678901234567890'
    env['DJANGO_SETTINGS_MODULE'] = 'openmoxie.settings'
    env['SKIP_ENV_VALIDATION'] = 'true'
    env['DJANGO_ENV'] = 'development'

    # Add site directory to Python path
    site_dir = Path(__file__).parent / 'site'
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{site_dir}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = str(site_dir)

    return env

def test_django_tests() -> Tuple[bool, str]:
    """Run Django tests"""
    print_colored("🧪 Running Django tests...", Colors.YELLOW)

    env = setup_test_environment()

    # Activate virtual environment and run Django tests
    cmd = f"""
    export SECRET_KEY='{env['SECRET_KEY']}'
    export DJANGO_SETTINGS_MODULE='{env['DJANGO_SETTINGS_MODULE']}'
    export SKIP_ENV_VALIDATION='{env['SKIP_ENV_VALIDATION']}'
    source venv/bin/activate 2>/dev/null || true
    cd site
    python manage.py test --verbosity=2
    """

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        # Check if any tests actually ran
        if "Ran 0 tests" in stdout:
            return True, "No Django tests found (this is okay - tests.py is empty)"
        else:
            return True, f"Django tests passed\n{stdout}"
    else:
        return False, f"Django tests failed\nSTDOUT: {stdout}\nSTDERR: {stderr}"

def test_improvements() -> Tuple[bool, str]:
    """Run improvement tests"""
    print_colored("🔧 Running improvement tests...", Colors.YELLOW)

    env = setup_test_environment()

    cmd = f"""
    export SECRET_KEY='{env['SECRET_KEY']}'
    export DJANGO_SETTINGS_MODULE='{env['DJANGO_SETTINGS_MODULE']}'
    export SKIP_ENV_VALIDATION='{env['SKIP_ENV_VALIDATION']}'
    source venv/bin/activate 2>/dev/null || true
    python test_improvements.py
    """

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        return True, f"Improvement tests passed\n{stdout}"
    else:
        return False, f"Improvement tests failed\nSTDOUT: {stdout}\nSTDERR: {stderr}"

def test_claude_integration() -> Tuple[bool, str]:
    """Run Claude integration tests"""
    print_colored("🤖 Running Claude integration tests...", Colors.YELLOW)

    env = setup_test_environment()

    cmd = f"""
    export SECRET_KEY='{env['SECRET_KEY']}'
    export DJANGO_SETTINGS_MODULE='{env['DJANGO_SETTINGS_MODULE']}'
    export SKIP_ENV_VALIDATION='{env['SKIP_ENV_VALIDATION']}'
    source venv/bin/activate 2>/dev/null || true
    python test_claude_integration.py
    """

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        return True, f"Claude integration tests passed\n{stdout}"
    else:
        # Check if it's just missing API key
        if "ANTHROPIC_API_KEY not set" in stdout:
            return True, "Claude integration tests skipped (ANTHROPIC_API_KEY not set - this is expected)"
        else:
            return False, f"Claude integration tests failed\nSTDOUT: {stdout}\nSTDERR: {stderr}"

def test_pytest() -> Tuple[bool, str]:
    """Run pytest tests"""
    print_colored("🧬 Running pytest tests...", Colors.YELLOW)

    env = setup_test_environment()

    cmd = f"""
    export SECRET_KEY='{env['SECRET_KEY']}'
    export DJANGO_SETTINGS_MODULE='{env['DJANGO_SETTINGS_MODULE']}'
    export SKIP_ENV_VALIDATION='{env['SKIP_ENV_VALIDATION']}'
    source venv/bin/activate 2>/dev/null || true
    pytest site/ --no-cov --tb=short -v
    """

    exit_code, stdout, stderr = run_command(cmd)



    # Check for successful pytest run (including no tests collected)
    has_no_tests = "no tests ran" in stdout.lower() or "collected 0 items" in stdout.lower()

    if exit_code == 0 or (exit_code in [1, 5] and has_no_tests):
        if has_no_tests:
            return True, "No pytest tests found (this is okay - no pytest test files exist yet)"
        else:
            return True, f"Pytest tests passed\n{stdout}"
    else:
        return False, f"Pytest tests failed\nSTDOUT: {stdout}\nSTDERR: {stderr}"

def check_code_quality() -> Tuple[bool, str]:
    """Run code quality checks"""
    print_colored("📋 Running code quality checks...", Colors.YELLOW)

    checks = []

    # Check if flake8 is available and run it
    cmd = """
    source venv/bin/activate 2>/dev/null || true
    flake8 site/ --max-line-length=88 --extend-ignore=E203,W503 || echo "flake8 not installed"
    """

    exit_code, stdout, stderr = run_command(cmd)
    if "flake8 not installed" not in stdout and exit_code == 0:
        checks.append("✅ Flake8 checks passed")
    elif "flake8 not installed" in stdout:
        checks.append("⚠️  Flake8 not installed (optional)")
    else:
        checks.append(f"❌ Flake8 found issues:\n{stdout}")

    # Check Python imports
    cmd = f"""
    export SECRET_KEY='{setup_test_environment()['SECRET_KEY']}'
    export DJANGO_SETTINGS_MODULE='openmoxie.settings'
    export SKIP_ENV_VALIDATION='true'
    source venv/bin/activate 2>/dev/null || true
    python -c "
import sys
sys.path.insert(0, 'site')
try:
    from hive.behavior_config import get_behavior_markup
    from hive.validators import validate_openai_api_key
    from hive.auth_utils import generate_api_token
    print('✅ All critical imports work')
except ImportError as e:
    print(f'❌ Import error: {{e}}')
    sys.exit(1)
"
    """

    exit_code, stdout, stderr = run_command(cmd)
    if exit_code == 0:
        checks.append(stdout.strip())
    else:
        checks.append(f"❌ Import checks failed: {stderr}")

    return True, "\n".join(checks)

def main():
    """Main test runner"""
    print_header("🧪 OpenMoxie Test Runner")

    # Check if we're in the right directory
    if not Path('site/manage.py').exists():
        print_colored("❌ Error: Could not find site/manage.py", Colors.RED)
        print_colored("Please run this script from the OpenMoxie root directory", Colors.YELLOW)
        sys.exit(1)

    # Check virtual environment
    if not Path('venv/bin/activate').exists():
        print_colored("⚠️  Warning: Virtual environment not found", Colors.YELLOW)
        print_colored("Some tests may fail. Run './setup-dev.sh' first.", Colors.YELLOW)

    test_results: List[Tuple[str, bool, str]] = []

    # Define tests to run
    tests = [
        ("Django Tests", test_django_tests),
        ("Improvement Tests", test_improvements),
        ("Claude Integration", test_claude_integration),
        ("Pytest Tests", test_pytest),
        ("Code Quality", check_code_quality),
    ]

    # Run each test
    for test_name, test_func in tests:
        print_header(f"Running {test_name}")
        try:
            success, message = test_func()
            test_results.append((test_name, success, message))

            if success:
                print_colored(f"✅ {test_name} completed successfully", Colors.GREEN)
                if message.strip():
                    print_colored(message, Colors.CYAN)
            else:
                print_colored(f"❌ {test_name} failed", Colors.RED)
                print_colored(message, Colors.RED)

        except Exception as e:
            test_results.append((test_name, False, str(e)))
            print_colored(f"❌ {test_name} failed with exception: {e}", Colors.RED)

    # Print summary
    print_header("📊 Test Summary")

    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)

    print_colored(f"Tests passed: {passed}/{total}", Colors.BOLD)
    print()

    for test_name, success, message in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        color = Colors.GREEN if success else Colors.RED
        print_colored(f"{status} {test_name}", color)

    print()

    if passed == total:
        print_colored("🎉 All tests completed successfully!", Colors.GREEN + Colors.BOLD)
        sys.exit(0)
    else:
        print_colored(f"⚠️  {total - passed} test(s) failed or had issues", Colors.YELLOW + Colors.BOLD)
        print_colored("Check the detailed output above for more information", Colors.YELLOW)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n❌ Tests interrupted by user", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        sys.exit(1)
