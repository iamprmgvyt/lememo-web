import requests
import sys
import json
from datetime import datetime

class DiscordNotesAPITester:
    def __init__(self, base_url="https://discord-notes.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = "123456789012345678"
        self.test_username = "TestUser"
        self.created_note_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_register(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "discord_user_id": self.test_user_id,
                "username": self.test_username
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"discord_user_id": self.test_user_id}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_create_note(self):
        """Test note creation"""
        success, response = self.run_test(
            "Create Note",
            "POST",
            "notes",
            200,
            data={
                "discord_user_id": self.test_user_id,
                "content": "This is a test note from Discord bot",
                "server_name": "Test Server",
                "channel_name": "general"
            }
        )
        if success and 'id' in response:
            self.created_note_id = response['id']
            print(f"   Note ID: {self.created_note_id}")
            return True
        return False

    def test_get_notes(self):
        """Test getting user notes"""
        return self.run_test("Get Notes", "GET", "notes", 200)

    def test_search_notes(self):
        """Test searching notes"""
        return self.run_test("Search Notes", "GET", "notes?search=test", 200)

    def test_get_note_by_id(self):
        """Test getting a specific note"""
        if not self.created_note_id:
            print("❌ No note ID available for testing")
            return False
        return self.run_test("Get Note by ID", "GET", f"notes/{self.created_note_id}", 200)

    def test_update_note(self):
        """Test updating a note"""
        if not self.created_note_id:
            print("❌ No note ID available for testing")
            return False
        return self.run_test(
            "Update Note",
            "PUT",
            f"notes/{self.created_note_id}",
            200,
            data={"content": "Updated test note content"}
        )

    def test_bot_get_notes(self):
        """Test bot endpoint for getting notes"""
        return self.run_test(
            "Bot Get Notes",
            "GET",
            f"bot/notes/{self.test_user_id}",
            200
        )

    def test_bot_search_notes(self):
        """Test bot endpoint for searching notes"""
        return self.run_test(
            "Bot Search Notes",
            "GET",
            f"bot/notes/{self.test_user_id}/search?q=test",
            200
        )

    def test_delete_note(self):
        """Test deleting a note"""
        if not self.created_note_id:
            print("❌ No note ID available for testing")
            return False
        return self.run_test("Delete Note", "DELETE", f"notes/{self.created_note_id}", 200)

    def test_duplicate_registration(self):
        """Test duplicate user registration (should fail)"""
        return self.run_test(
            "Duplicate Registration (should fail)",
            "POST",
            "auth/register",
            400,
            data={
                "discord_user_id": self.test_user_id,
                "username": self.test_username
            }
        )

    def test_invalid_login(self):
        """Test login with non-existent user"""
        return self.run_test(
            "Invalid Login (should fail)",
            "POST",
            "auth/login",
            404,
            data={"discord_user_id": "999999999999999999"}
        )

def main():
    print("🚀 Starting Discord Notes API Tests")
    print("=" * 50)
    
    tester = DiscordNotesAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Registration", tester.test_register),
        ("Get Current User", tester.test_get_me),
        ("Create Note", tester.test_create_note),
        ("Get Notes", tester.test_get_notes),
        ("Search Notes", tester.test_search_notes),
        ("Get Note by ID", tester.test_get_note_by_id),
        ("Update Note", tester.test_update_note),
        ("Bot Get Notes", tester.test_bot_get_notes),
        ("Bot Search Notes", tester.test_bot_search_notes),
        ("Delete Note", tester.test_delete_note),
        ("Duplicate Registration", tester.test_duplicate_registration),
        ("Invalid Login", tester.test_invalid_login),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())