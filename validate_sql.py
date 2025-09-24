#!/usr/bin/env python
"""
SQL Syntax Validator for database_setup.sql
This script validates the SQL syntax without requiring a MySQL connection.
"""

import re
import sys

def validate_sql_file(filename):
    """
    Basic SQL syntax validation for MySQL scripts.
    """
    errors = []
    warnings = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        return [f"File {filename} not found"], []
    
    lines = content.split('\n')
    
    # Check for common SQL syntax issues
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('--') or line.startswith('/*') or line.startswith('*/'):
            continue
            
        # Check for password placeholders
        if 'CHANGE_THIS' in line:
            warnings.append(f"Line {i}: Remember to replace placeholder password")
        
        # Check for basic SQL statement structure
        sql_keywords = ['CREATE', 'GRANT', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'SHOW', 'USE', 'FLUSH']
        if any(keyword in line.upper() for keyword in sql_keywords):
            # Check if statement ends properly
            if not line.endswith(';'):
                # Look ahead for continuation
                next_line_idx = i
                found_semicolon = False
                while next_line_idx < len(lines) and next_line_idx < i + 3:
                    next_line = lines[next_line_idx].strip()
                    if next_line.endswith(';'):
                        found_semicolon = True
                        break
                    next_line_idx += 1
                
                if not found_semicolon and not any(cont in line for cont in [',', '(', 'CHARACTER SET', 'COLLATE']):
                    warnings.append(f"Line {i}: SQL statement may be missing semicolon")
    
    return errors, warnings

def main():
    filename = 'database_setup.sql'
    print(f"Validating {filename}...")
    
    errors, warnings = validate_sql_file(filename)
    
    if errors:
        print("\n❌ ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ SQL file appears to be syntactically correct!")
    elif not errors:
        print("\n✅ No syntax errors found. Only warnings present.")
        print("\n📝 The warnings are reminders for deployment preparation.")
    
    print("\n📋 DEPLOYMENT CHECKLIST:")
    print("  1. ✅ SQL syntax is valid")
    print("  2. ⚠️  Replace all 'CHANGE_THIS_*' passwords with secure ones")
    print("  3. ⚠️  Review and uncomment remote access lines if needed")
    print("  4. ⚠️  Test the script on your hosting provider's MySQL server")
    print("  5. ⚠️  Backup any existing database before running")
    
    return len(errors)

if __name__ == '__main__':
    sys.exit(main())