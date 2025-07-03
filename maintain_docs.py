#!/usr/bin/env python
"""
Documentation maintenance script
Helps keep FUNCTIONALITY_REFERENCE.md updated
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def update_functionality_reference():
    """Update the functionality reference with current project state"""
    
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "docs"
    func_ref_file = docs_dir / "FUNCTIONALITY_REFERENCE.md"
    
    if not func_ref_file.exists():
        print("❌ FUNCTIONALITY_REFERENCE.md not found!")
        return False
    
    print("🔍 Analyzing current project structure...")
    
    # Count Django apps
    apps = []
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "models.py").exists():
            apps.append(item.name)
    
    # Count management commands
    commands = []
    for app_dir in base_dir.iterdir():
        if app_dir.is_dir():
            cmd_dir = app_dir / "management" / "commands"
            if cmd_dir.exists():
                for cmd_file in cmd_dir.iterdir():
                    if cmd_file.suffix == ".py" and cmd_file.name != "__init__.py":
                        commands.append(f"{app_dir.name}/{cmd_file.stem}")
    
    # Count API endpoints (approximate)
    api_files = []
    for app_dir in base_dir.iterdir():
        if app_dir.is_dir():
            views_file = app_dir / "views.py"
            urls_file = app_dir / "urls.py"
            if views_file.exists() or urls_file.exists():
                api_files.append(app_dir.name)
    
    # Generate update info
    update_info = f"""
📊 **Current Project Stats** (Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')})
- **Django Apps**: {len(apps)} ({', '.join(apps)})
- **Management Commands**: {len(commands)} ({', '.join(commands)})
- **API Modules**: {len(api_files)} ({', '.join(api_files)})
    """
    
    print("📋 Current project statistics:")
    print(update_info)
    
    print(f"\n📝 Please manually update {func_ref_file} with any new features or changes.")
    print("\n🔄 Remember to update:")
    print("- Last Updated date")
    print("- Version number (if applicable)")
    print("- Any new features in the appropriate sections")
    print("- Status of planned features")
    
    return True

def check_documentation_health():
    """Check if documentation is up to date"""
    
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "docs"
    
    print("🏥 Documentation Health Check")
    print("=" * 40)
    
    # Check required files
    required_docs = [
        "docs/FUNCTIONALITY_REFERENCE.md",
        "docs/README.md",
        "config/README.md",
        "README.md",
        "PROJECT_FINAL.md"
    ]
    
    missing_docs = []
    for doc in required_docs:
        if not (base_dir / doc).exists():
            missing_docs.append(doc)
    
    if missing_docs:
        print(f"❌ Missing documentation: {', '.join(missing_docs)}")
    else:
        print("✅ All required documentation files present")
    
    # Check if FUNCTIONALITY_REFERENCE.md was updated recently
    func_ref = base_dir / "docs" / "FUNCTIONALITY_REFERENCE.md"
    if func_ref.exists():
        # Get file modification time
        mod_time = datetime.fromtimestamp(func_ref.stat().st_mtime)
        days_old = (datetime.now() - mod_time).days
        
        if days_old > 30:
            print(f"⚠️  FUNCTIONALITY_REFERENCE.md is {days_old} days old - consider updating")
        else:
            print(f"✅ FUNCTIONALITY_REFERENCE.md is up to date ({days_old} days old)")
    
    # Check for TODO or FIXME in docs
    todo_count = 0
    if docs_dir.exists():
        for doc_file in docs_dir.rglob("*.md"):
            try:
                content = doc_file.read_text(encoding='utf-8')
                todo_count += content.upper().count("TODO")
                todo_count += content.upper().count("FIXME")
            except:
                pass
    
    if todo_count > 0:
        print(f"📝 Found {todo_count} TODO/FIXME items in documentation")
    else:
        print("✅ No pending TODO/FIXME items in documentation")
    
    return len(missing_docs) == 0

def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "update":
            update_functionality_reference()
        elif command == "check":
            check_documentation_health()
        elif command == "health":
            check_documentation_health()
        else:
            print("❓ Unknown command. Use 'update' or 'check'")
    else:
        print("📚 Documentation Maintenance Tool")
        print("\nUsage:")
        print("  python maintain_docs.py update  - Analyze project and suggest updates")
        print("  python maintain_docs.py check   - Check documentation health")
        print("  python maintain_docs.py health  - Same as check")
        print("\n📝 Remember to manually update FUNCTIONALITY_REFERENCE.md")
        print("   when adding new features, apps, or commands!")

if __name__ == "__main__":
    main()
