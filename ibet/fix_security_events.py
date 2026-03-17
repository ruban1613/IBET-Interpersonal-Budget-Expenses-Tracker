#!/usr/bin/env python3
"""
Script to fix missing wallet event types in security monitoring.
"""

import os
import sys

# Add the IBET directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_security_events():
    """Add missing wallet event types to the security monitoring module."""

    # Read the current file
    file_path = 'core/security_monitoring.py'
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if WALLET_TRANSFER is already defined
    if "'WALLET_TRANSFER': 'wallet_transfer'" in content:
        print("✅ WALLET_TRANSFER event type already exists")
        return True

    # Find the EVENT_TYPES dictionary and add missing wallet event types
    event_types_start = content.find("EVENT_TYPES = {")
    if event_types_start == -1:
        print("❌ Could not find EVENT_TYPES dictionary")
        return False

    # Find the end of the EVENT_TYPES dictionary
    event_types_end = content.find("}", event_types_start)
    while event_types_end < len(content) and content[event_types_end] != '\n':
        event_types_end += 1

    # Extract the current EVENT_TYPES content
    current_event_types = content[event_types_start:event_types_end + 1]

    # Add missing wallet event types before the closing brace
    new_event_types = current_event_types.replace(
        "        'SECURITY_VIOLATION': 'security_violation'\n    }",
        "        'SECURITY_VIOLATION': 'security_violation',\n        'WALLET_TRANSFER': 'wallet_transfer',\n        'WALLET_DEPOSIT': 'wallet_deposit',\n        'WALLET_WITHDRAWAL': 'wallet_withdrawal'\n    }"
    )

    # Replace the old content with the new content
    new_content = content.replace(current_event_types, new_event_types)

    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.write(new_content)

    print("✅ Added missing wallet event types:")
    print("   - WALLET_TRANSFER: wallet_transfer")
    print("   - WALLET_DEPOSIT: wallet_deposit")
    print("   - WALLET_WITHDRAWAL: wallet_withdrawal")

    return True

if __name__ == "__main__":
    success = fix_security_events()
    if success:
        print("\n🎉 Security events fixed successfully!")
    else:
        print("\n❌ Failed to fix security events")
        sys.exit(1)
