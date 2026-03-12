"""
Comprehensive test script for login functionality
Tests both admin and testuser login
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_login(username, password):
    """Test login with given credentials"""
    print(f"\n{'='*60}")
    print(f"Testing login for: {username}")
    print(f"{'='*60}")
    
    session = requests.Session()
    
    # Get login page first (to get any CSRF tokens if needed)
    print("1. Getting login page...")
    response = session.get(f"{BASE_URL}/login")
    print(f"   Status: {response.status_code}")
    
    # Attempt login
    print(f"2. Attempting login with username={username}, password={password}")
    login_data = {
        'username': username,
        'password': password
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"   Status: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'N/A')}")
    
    # Check if redirected (successful login redirects to index)
    if response.status_code == 302 and '/' in response.headers.get('Location', ''):
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

def test_protected_route(session, route_name, route_path):
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
    admin_success = test_login('admin', 'admin123')
    
    # Test 2: Testuser login
    testuser_success = test_login('testuser', 'test123')
    
    # Test 3: Invalid login
    print(f"\n{'='*60}")
    print("Testing invalid login")
    print(f"{'='*60}")
    invalid_success = not test_login('invalid', 'wrongpass')
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
