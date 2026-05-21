from django.test import Client
from accounts.models import User
from wallet.models import CryptoDeposit
import json

print("\n" + "="*80)
print("TESTING: Task Deposit Requirement")
print("="*80 + "\n")

client = Client()

# Create user
test_email = "nodep_" + str(__import__('time').time()).split('.')[0] + "@test.com"
reg_resp = client.post('/api/auth/register/', 
    data=json.dumps({"email": test_email, "password": "Test123!", "first_name": "T", "last_name": "U"}),
    content_type='application/json')

print(f"User created: {reg_resp.status_code}")

# Login
login_resp = client.post('/api/auth/login/', 
    data=json.dumps({"email": test_email, "password": "Test123!"}),
    content_type='application/json')

token = login_resp.json().get("access")
print(f"Token: {token[:20]}...\n")

# Try to submit task
print("Attempting to submit task WITHOUT deposit:")
submit_resp = client.post('/api/submissions/',
    data=json.dumps({"task": 1, "submission_link": "https://example.com"}),
    content_type='application/json',
    HTTP_AUTHORIZATION=f"Bearer {token}")

print(f"Status: {submit_resp.status_code}")
print(f"Response: {submit_resp.json()}")

if submit_resp.status_code == 403:
    print("\n✅ SUCCESS: User blocked from submitting without deposit")
    print(f"   Message: {submit_resp.json().get('detail')}")
else:
    print(f"\n⚠️  Unexpected status code: {submit_resp.status_code}")

print("\n" + "="*80)
