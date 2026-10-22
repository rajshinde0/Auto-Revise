"""
Comprehensive test script for login functionality
Tests both admin and testuser login

This is a manual end-to-end script, not a pytest suite: it needs the app
already running on BASE_URL. Run it with:

    python app.py            # in one terminal
    python tests/test_login.py   # in another

The helpers are deliberately named login_helper/check_protected_route rather
than test_* so pytest does not collect them and then fail trying to resolve
their arguments as fixtures.
"""
import sys

# Windows consoles default to cp1252, which cannot encode the emoji in this
# script's progress output. Without this the script dies with
# UnicodeEncodeError instead of doing its job - and the error handler then
# fails the same way trying to report it.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import re
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def login_helper(username, password):
    """Test login with given credentials"""
    print(f"\n{'='*60}")
    print(f"Testing login for: {username}")
    print(f"{'='*60}")
    
    session = requests.Session()

    # Get login page first, and take the CSRF token from the form. CSRF is
    # enabled, so a POST without it is rejected before the credentials are
    # ever checked.
    print("1. Getting login page...")
    response = session.get(f"{BASE_URL}/login")
    print(f"   Status: {response.status_code}")

    token_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    if not token_match:
        print("   ❌ No CSRF token found on the login page")
        return False

    # Attempt login
    print(f"2. Attempting login with username={username}, password={password}")
    login_data = {
        'username': username,
        'password': password,
        'csrf_token': token_match.group(1)
    }

    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"   Status: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'N/A')}")

    # A successful login redirects to the index. Match it exactly: '/' appears
    # in every path, so a loose check also matched the redirect back to /login
    # that a rejected login produces, reporting failures as successes.
    location = response.headers.get('Location', '')
    if response.status_code == 302 and location in ('/', f'{BASE_URL}/'):
        print("   ✅ Login SUCCESSFUL - Redirected to home page")
        
        # Follow redirect to verify
        response = session.get(f"{BASE_URL}/", allow_redirects=True)
        if username in response.text or 'Hello,' in response.text:
            print("   ✅ Session verified - User greeting found on page")
            return True
        else:
            print("   ⚠️ Redirected but user greeting not found")
            return False
    else:
        print(f"   ❌ Login FAILED")
        if 'Invalid username or password' in response.text:
            print("   Error: Invalid credentials")
        elif 'Too many failed' in response.text:
            print("   Error: Rate limited")
        return False

def check_protected_route(session, route_name, route_path):
    """Test accessing a protected route"""
    print(f"\n3. Testing protected route: {route_name}")
    response = session.get(f"{BASE_URL}{route_path}")
    
    if response.status_code == 200:
        print(f"   ✅ Access granted to {route_name}")
        return True
    elif response.status_code == 302:
        print(f"   ❌ Redirected (not authenticated)")
        return False
    else:
        print(f"   ⚠️ Unexpected status: {response.status_code}")
        return False

def main():
    print("\n" + "="*60)
    print("COMPREHENSIVE LOGIN TEST SUITE")
    print("="*60)
    
    # Test 1: Admin login
    admin_success = login_helper('admin', 'admin123')
    
    # Test 2: Testuser login
    testuser_success = login_helper('testuser', 'test123')
    
    # Test 3: Invalid login
    print(f"\n{'='*60}")
    print("Testing invalid login")
    print(f"{'='*60}")
    invalid_success = not login_helper('invalid', 'wrongpass')
    print(f"   {'✅' if invalid_success else '❌'} Invalid login properly rejected")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Admin Login:    {'✅ PASS' if admin_success else '❌ FAIL'}")
    print(f"Testuser Login: {'✅ PASS' if testuser_success else '❌ FAIL'}")
    print(f"Invalid Reject: {'✅ PASS' if invalid_success else '❌ FAIL'}")
    
    if admin_success and testuser_success and invalid_success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED")
    
    print("="*60)

if __name__ == "__main__":
    main()
