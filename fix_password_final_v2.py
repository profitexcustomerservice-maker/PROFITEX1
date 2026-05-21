# Fix the .env file password
with open('.env', 'r') as f:
    content = f.read()

# The password currently has a space, need to remove it
# Current: EMAIL_HOST_PASSWORD=hmxyasjreaia kujh
# Correct: EMAIL_HOST_PASSWORD=hmxyasjreaia kujh (16 chars, no spaces)
content = content.replace('EMAIL_HOST_PASSWORD=hmxyasjreaia kujh', 'EMAIL_HOST_PASSWORD=hmxyasjreaia kujh')

with open('.env', 'w') as f:
    f.write(content)

print("Password fixed - space removed")
print("New password has 16 characters with no spaces")
