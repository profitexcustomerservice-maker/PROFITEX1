with open('.env', 'r') as f:
    lines = f.readlines()

# Find and fix the password line
for i, line in enumerate(lines):
    if 'EMAIL_HOST_PASSWORD=' in line:
        # Remove the space from the password
        current_password = line.split('=')[1].strip()
        fixed_password = current_password.replace(' ', '')
        lines[i] = f'EMAIL_HOST_PASSWORD={fixed_password}\n'
        print(f"Fixed line {i+1}")
        print(f"Old: {current_password} (len={len(current_password)})")
        print(f"New: {fixed_password} (len={len(fixed_password)})")
        break

with open('.env', 'w') as f:
    f.writelines(lines)

print("Password fixed successfully")
