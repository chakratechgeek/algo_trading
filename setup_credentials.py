#!/usr/bin/env python
"""
Setup script for configuring API credentials
"""

import os
import shutil
from pathlib import Path

def setup_credentials():
    """Setup credentials from template"""
    base_dir = Path(__file__).parent
    config_dir = base_dir / "config"
    template_file = config_dir / "secrets.py.template"
    secrets_file = config_dir / "secrets.py"
    
    print("🔧 Setting up API credentials...")
    
    # Check if config directory exists
    if not config_dir.exists():
        print("❌ Config directory not found!")
        return False
    
    # Check if template exists
    if not template_file.exists():
        print("❌ Template file not found!")
        return False
    
    # Check if secrets file already exists
    if secrets_file.exists():
        response = input("⚠️  Secrets file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Keeping existing secrets file.")
            return True
    
    # Copy template to secrets
    try:
        shutil.copy2(template_file, secrets_file)
        print(f"✅ Created {secrets_file}")
        print("\n📝 Next steps:")
        print(f"1. Edit {secrets_file}")
        print("2. Fill in your actual API credentials")
        print("3. Save the file")
        print("\n🔒 The secrets.py file is gitignored and won't be committed.")
        return True
    except Exception as e:
        print(f"❌ Error creating secrets file: {e}")
        return False

def check_credentials():
    """Check if credentials are properly configured"""
    try:
        from config.secrets import (
            API_KEY, CLIENT_CODE, WEB_PASSWORD, MPIN, 
            TOTP_SECRET, SECRET_KEY, DJANGO_SECRET_KEY
        )
        
        required_fields = {
            'API_KEY': API_KEY,
            'CLIENT_CODE': CLIENT_CODE,
            'WEB_PASSWORD': WEB_PASSWORD,
            'MPIN': MPIN,
            'TOTP_SECRET': TOTP_SECRET,
            'SECRET_KEY': SECRET_KEY,
            'DJANGO_SECRET_KEY': DJANGO_SECRET_KEY
        }
        
        print("🔍 Checking credentials configuration...")
        
        missing_fields = []
        template_values = []
        
        for field, value in required_fields.items():
            if not value or value == "your_" + field.lower() + "_here":
                if "your_" in str(value):
                    template_values.append(field)
                else:
                    missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing credentials: {', '.join(missing_fields)}")
        
        if template_values:
            print(f"⚠️  Template values need to be replaced: {', '.join(template_values)}")
        
        if not missing_fields and not template_values:
            print("✅ All credentials are configured!")
            return True
        else:
            print(f"\n📝 Please edit config/secrets.py and fill in the required values.")
            return False
            
    except ImportError:
        print("❌ Secrets file not found. Run setup first.")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_credentials()
    else:
        if setup_credentials():
            print("\n" + "="*50)
            check_credentials()
