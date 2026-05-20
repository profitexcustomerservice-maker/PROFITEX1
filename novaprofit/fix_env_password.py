# Fix the .env file password
with open('.env', 'r') as f:
    lines = f.readlines()

# Replace the password line (line 16, index 15)
# Current: EMAIL_HOST_PASSWORD=hmxyasjreaia kujh
# Correct: EMAIL_HOST_PASSWORD=hmxyasjreaia kujh (no space)

for i, line in enumerate(lines):
    if 'EMAIL_HOST_PASSWORD=' in line:
        lines[i] = 'EMAIL_HOST_PASSWORD=hmxyasjreaia kujh\n'
        print(f"Fixed line {i+1}")
        break

with open('.env', 'w') as f:
    f.writelines(lines)

print("Password fixed successfully")
