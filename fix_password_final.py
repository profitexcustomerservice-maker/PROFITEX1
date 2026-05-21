with open('.env', 'r') as f:
    content = f.read()

# Fix the password by removing the space
content = content.replace('EMAIL_HOST_PASSWORD=hmxyasjreaia kujh', 'EMAIL_HOST_PASSWORD=hmxyasjreaia kujh')

with open('.env', 'w') as f:
    f.write(content)

print("Password fixed")
