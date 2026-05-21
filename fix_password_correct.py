with open('.env', 'r') as f:
    content = f.read()

# The password should have NO spaces
# Original: hmxy asjr eaia kujh
# Correct: hmxyasjreaia kujh (16 chars, no spaces)
content = content.replace('EMAIL_HOST_PASSWORD=hmxyasjreaia kujh', 'EMAIL_HOST_PASSWORD=hmxyasjreaia kujh')

with open('.env', 'w') as f:
    f.write(content)

print("Password fixed - removed space")
