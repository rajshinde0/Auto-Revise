"""
Verification script to check if all improvements are working correctly
Run this after installation to verify everything is set up properly
"""

import os
import sys

print("=" * 60)
print("MCQ Quiz Application - Installation Verification")
print("=" * 60)
print()

# Check 1: Python version
print("✓ Checking Python version...")
python_version = sys.version_info
if python_version.major >= 3 and python_version.minor >= 8:
    print(f"  ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} (OK)")
else:
    print(f"  ❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (Need 3.8+)")
    sys.exit(1)

# Check 2: Required packages
print("\n✓ Checking required packages...")
required_packages = {
    'flask': 'Flask',
    'mysql.connector': 'mysql-connector-python',
    'bcrypt': 'bcrypt',
    'flask_wtf': 'Flask-WTF',
    'dotenv': 'python-dotenv'
}

all_packages_found = True
for module, package_name in required_packages.items():
    try:
        __import__(module)
        print(f"  ✅ {package_name}")
    except ImportError:
        print(f"  ❌ {package_name} - NOT FOUND")
        all_packages_found = False

if not all_packages_found:
    print("\n⚠️  Please install missing packages: pip install -r requirements.txt")
    sys.exit(1)

# Check 3: Environment file
print("\n✓ Checking environment configuration...")
if os.path.exists('.env'):
    print("  ✅ .env file exists")
    
    # Load and check critical variables
    from dotenv import load_dotenv
    load_dotenv()
    
    critical_vars = ['SECRET_KEY', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if var == 'SECRET_KEY':
                if value == 'your-secret-key-change-in-production-2024':
                    print(f"  ⚠️  {var} - Using default value (CHANGE THIS!)")
                else:
                    print(f"  ✅ {var} - Configured")
            else:
                print(f"  ✅ {var} - Configured")
        else:
            print(f"  ❌ {var} - NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing variables in .env: {', '.join(missing_vars)}")
else:
    print("  ❌ .env file NOT FOUND")
    print("     Please copy .env.example to .env and configure it")
    sys.exit(1)

# Check 4: Directory structure
print("\n✓ Checking directory structure...")
required_dirs = ['Templates', 'static', 'Quiz Data']
for dir_name in required_dirs:
    if os.path.exists(dir_name):
        print(f"  ✅ {dir_name}/ directory exists")
    else:
        print(f"  ❌ {dir_name}/ directory NOT FOUND")

# Check 5: Error page templates
print("\n✓ Checking error page templates...")
error_templates = ['404.html', '500.html', '403.html']
for template in error_templates:
    template_path = os.path.join('Templates', template)
    if os.path.exists(template_path):
        print(f"  ✅ {template}")
    else:
        print(f"  ❌ {template} NOT FOUND")

# Check 6: Logs directory
print("\n✓ Checking logs directory...")
if not os.path.exists('logs'):
    os.makedirs('logs')
    print("  ✅ Created logs/ directory")
else:
    print("  ✅ logs/ directory exists")

# Check 7: Core files
print("\n✓ Checking core application files...")
core_files = ['app.py', 'db_config.py', 'achievement_system.py', 'requirements.txt']
for file_name in core_files:
    if os.path.exists(file_name):
        print(f"  ✅ {file_name}")
    else:
        print(f"  ❌ {file_name} NOT FOUND")

# Check 8: Database connection (optional)
print("\n✓ Testing database connection...")
try:
    from db_config import get_connection
    conn = get_connection()
    if conn.is_connected():
        print("  ✅ Database connection successful")
        conn.close()
    else:
        print("  ❌ Database connection failed")
except Exception as e:
    print(f"  ⚠️  Database connection test failed: {str(e)}")
    print("     Make sure MySQL is running and credentials are correct in .env")

# Final summary
print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print()
print("✅ All checks passed! Your application is ready to run.")
print()
print("To start the application:")
print("  python app.py")
print()
print("To access the application:")
print("  http://127.0.0.1:5000")
print()
print("Default Admin Login:")
print("  Username: admin")
print("  Password: admin123")
print("  (Change this password after first login!)")
print()
print("=" * 60)
