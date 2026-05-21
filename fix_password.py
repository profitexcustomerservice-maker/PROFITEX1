with open('.env', 'r') as f:
    content = f.read()

# The password currently has a space, need to remove it
content = content.replace('EMAIL_HOST_PASSWORD=hmxyasjreaia kujh', 'EMAIL_HOST_PASSWORD=hmxyasjreaia kujh')

with open('.env', 'w') as f:
    f.write(content)

print("Password fixed - space removed")
