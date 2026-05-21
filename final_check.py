from accounts.models import User

print("\n" + "="*80)
print("FINAL DATABASE VERIFICATION")
print("="*80 + "\n")

total = User.objects.count()
print(f"✅ Total Users in PostgreSQL: {total}\n")

print("Recent Registrations:")
for user in User.objects.order_by('-created_at')[:3]:
    status = "✅" if user.is_active else "❌"
    print(f"{status} {user.email}")
    print(f"   ID: {user.id} | Active: {user.is_active} | Admin: {user.is_admin}")
    print(f"   Created: {user.created_at}\n")

print("="*80)
print("✅ SYSTEM VERIFICATION COMPLETE")
print("="*80)
