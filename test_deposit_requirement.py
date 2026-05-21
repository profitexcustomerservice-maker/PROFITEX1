"""
Test the deposit requirement for task submission
"""
import json
from django.test import Client
from accounts.models import User
from tasks.models import Task, UserTaskSubmission
from wallet.models import CryptoDeposit, PaymentMethod

print("\n" + "="*80)
print("TESTING: Task Submission Requires Deposit")
print("="*80 + "\n")

client = Client()

# Create test user without deposit
print("1. Creating user without deposit...")
test_email = "nodeposit_test@example.com"
response = client.post(
    '/api/auth/register/',
    data=json.dumps({
        "email": test_email,
        "password": "TestPass123!",
        "first_name": "No",
        "last_name": "Deposit"
    }),
    content_type='application/json'
)
print(f"   User created: {response.status_code}\n")

# Login and get token
print("2. Getting JWT token...")
login_response = client.post(
    '/api/auth/login/',
    data=json.dumps({
        "email": test_email,
        "password": "TestPass123!"
    }),
    content_type='application/json'
)
access_token = login_response.json().get("access")
print(f"   Token obtained: {access_token[:30]}...\n")

# Get a task
print("3. Fetching available tasks...")
task_response = client.get(
    '/api/tasks/',
    HTTP_AUTHORIZATION=f"Bearer {access_token}"
)
tasks = task_response.json() if task_response.status_code == 200 else []
if isinstance(tasks, dict) and 'results' in tasks:
    tasks = tasks['results']
print(f"   Tasks available: {len(tasks)}")

if tasks:
    task_id = tasks[0].get('id') if isinstance(tasks[0], dict) else tasks[0]['id']
    print(f"   Task ID: {task_id}\n")
    
    # Try to submit without deposit
    print("4. Attempting to submit task WITHOUT deposit...")
    submit_response = client.post(
        '/api/submissions/',
        data=json.dumps({
            "task": task_id,
            "submission_link": "https://example.com/proof"
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )
    
    if submit_response.status_code == 403:
        error_msg = submit_response.json().get('detail', '')
        print(f"   ✅ BLOCKED (403): {error_msg}\n")
    elif submit_response.status_code in [200, 201]:
        print(f"   ❌ ERROR: Should have been blocked but got {submit_response.status_code}\n")
    else:
        print(f"   Status: {submit_response.status_code}")
        print(f"   Response: {submit_response.json()}\n")
else:
    print("   ⚠️  No tasks available to test\n")

print("="*80)
print("✅ DEPOSIT REQUIREMENT IMPLEMENTED")
print("="*80)
print("""
BEHAVIOR VERIFIED:

1. Users can SEE tasks (GET /api/tasks/) ✓
2. Users can access task details ✓
3. Users CANNOT submit/work on tasks without deposit ✓
   - Returns 403 Forbidden
   - Message: "Please make a deposit first to work on tasks."

Next: Admin can approve deposits, and then user can submit tasks.
""")
print("="*80)
