"""
Markup validation and sanitization for Moxie robot commands
"""
import re
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Maximum allowed markup length to prevent DoS
MAX_MARKUP_LENGTH = 10000

# Allowed markup elements and attributes
ALLOWED_ELEMENTS = {
    'mark': ['name'],
    'break': ['time'],
    'speak': [],
    'emphasis': ['level'],
    'prosody': ['rate', 'pitch', 'volume']
}

# Allowed command patterns
ALLOWED_COMMANDS = [
    r'^cmd:behaviour-tree$',
    r'^cmd:playaudio$',
    r'^cmd:external$',
    r'^cmd:stop$',
    r'^cmd:interrupt$'
]


class MarkupValidationError(Exception):
    """Raised when markup validation fails"""
    pass


def validate_markup(markup: str) -> Tuple[bool, Optional[str]]:
    """
    Validate markup XML for safety and correctness
    Returns (is_valid, error_message)
    """
    if not markup:
        return True, None

    # Check length
    if len(markup) > MAX_MARKUP_LENGTH:
        return False, f"Markup too long (max {MAX_MARKUP_LENGTH} characters)"

    # Basic XML structure validation
    try:
        # Wrap in root element for parsing if needed
        if not markup.strip().startswith('<'):
            # Plain text is valid
            return True, None

        # Try to parse as XML fragment
        # Add a root element if the markup doesn't have one
        if not re.match(r'^\s*<\w+', markup):
            test_xml = f"<root>{markup}</root>"
        else:
            test_xml = markup

        # Parse and validate structure
        root = ET.fromstring(test_xml)

        # Validate elements recursively
        return validate_element(root)

    except ET.ParseError as e:
        return False, f"Invalid XML structure: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error validating markup: {e}")
        return False, "Invalid markup format"


def validate_element(element) -> Tuple[bool, Optional[str]]:
    """
    Recursively validate XML elements
    """
    # Skip root element if it was added for parsing
    if element.tag == 'root':
        for child in element:
            is_valid, error = validate_element(child)
            if not is_valid:
                return False, error
        return True, None

    # Check if element is allowed
    if element.tag not in ALLOWED_ELEMENTS:
        return False, f"Disallowed element: {element.tag}"

    # Check attributes
    allowed_attrs = ALLOWED_ELEMENTS[element.tag]
    for attr in element.attrib:
        if attr not in allowed_attrs:
            return False, f"Disallowed attribute '{attr}' in element '{element.tag}'"

    # Special validation for mark elements
    if element.tag == 'mark':
        name_attr = element.get('name', '')
        if not validate_mark_name(name_attr):
            return False, f"Invalid mark command: {name_attr}"

    # Validate children
    for child in element:
        is_valid, error = validate_element(child)
        if not is_valid:
            return False, error

    return True, None


def validate_mark_name(name: str) -> bool:
    """
    Validate mark element name attribute
    """
    if not name:
        return False

    # Extract command part
    parts = name.split(',', 1)
    if not parts:
        return False

    command = parts[0]

    # Check against allowed commands
    for pattern in ALLOWED_COMMANDS:
        if re.match(pattern, command):
            return True

    return False


def sanitize_markup(markup: str) -> str:
    """
    Sanitize markup by escaping potentially dangerous content
    """
    if not markup:
        return ""

    # Remove any script tags or javascript
    markup = re.sub(r'<script[^>]*>.*?</script>', '', markup, flags=re.IGNORECASE | re.DOTALL)
    markup = re.sub(r'javascript:', '', markup, flags=re.IGNORECASE)
    markup = re.sub(r'on\w+\s*=', '', markup, flags=re.IGNORECASE)

    # Escape special characters that could break XML
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;'
    }

    # Only escape if not already escaped
    for char, escape in replacements.items():
        if char == '&':
            # Don't double-escape
            markup = re.sub(r'&(?![a-zA-Z]+;)', escape, markup)
        else:
            # Simple replacement for other characters
            # but preserve existing XML tags
            pass

    return markup.strip()


def validate_mood(mood: str) -> bool:
    """
    Validate mood parameter
    """
    valid_moods = [
        'neutral', 'happy', 'positive', 'excited', 'curious', 'silly',
        'shy', 'concerned', 'confused', 'angry', 'sad', 'negative',
        'afraid', 'embarrassed'
    ]
    return mood.lower() in valid_moods


def validate_intensity(intensity: any) -> Tuple[bool, float]:
    """
    Validate and convert intensity parameter
    Returns (is_valid, converted_value)
    """
    try:
        value = float(intensity)
        if 0.0 <= value <= 1.0:
            return True, value
        return False, 0.5
    except (TypeError, ValueError):
        return False, 0.5


def validate_behavior_name(behavior: str) -> bool:
    """
    Validate behavior tree name
    """
    if not behavior:
        return False

    # Check length
    if len(behavior) > 100:
        return False

    # Allow alphanumeric, underscores, and common separators
    if not re.match(r'^[a-zA-Z0-9_\-]+$', behavior):
        return False

    return True


def validate_sound_name(sound: str) -> bool:
    """
    Validate sound effect name
    """
    if not sound:
        return False

    # Check length
    if len(sound) > 100:
        return False

    # Allow alphanumeric, underscores, hyphens, and dots
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', sound):
        return False

    return True


def validate_volume(volume: any) -> Tuple[bool, float]:
    """
    Validate and convert volume parameter
    Returns (is_valid, converted_value)
    """
    try:
        value = float(volume)
        if 0.0 <= value <= 1.0:
            return True, value
        return False, 0.75
    except (TypeError, ValueError):
        return False, 0.75


def validate_sequence_data(sequence_data: list) -> Tuple[bool, Optional[str]]:
    """
    Validate sequence data structure
    """
    if not isinstance(sequence_data, list):
        return False, "Sequence data must be a list"

    if len(sequence_data) > 100:
        return False, "Sequence too long (max 100 items)"

    for item in sequence_data:
        if not isinstance(item, dict):
            return False, "Each sequence item must be a dictionary"

        if 'type' not in item:
            return False, "Sequence item missing 'type' field"

        item_type = item.get('type')
        if item_type not in ['behavior', 'sound', 'pause', 'speak', 'emotion']:
            return False, f"Invalid sequence item type: {item_type}"

        # Validate item-specific fields
        if item_type == 'behavior':
            if 'value' not in item or not validate_behavior_name(item['value']):
                return False, "Invalid behavior in sequence"
        elif item_type == 'sound':
            if 'value' not in item or not validate_sound_name(item['value']):
                return False, "Invalid sound in sequence"
        elif item_type == 'pause':
            if 'duration' not in item:
                return False, "Pause item missing duration"
            try:
                duration = float(item['duration'])
                if duration < 0 or duration > 60:
                    return False, "Pause duration must be between 0 and 60 seconds"
            except (TypeError, ValueError):
                return False, "Invalid pause duration"

    return True, None
