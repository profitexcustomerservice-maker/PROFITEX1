with open('.env', 'r') as f:
    content = f.read()

for line in content.split('\n'):
    if 'EMAIL_HOST_PASSWORD=' in line:
        password = line.split('=')[1]
        print(f"Password: {password}")
        print(f"Length: {len(password)}")
        print(f"Has spaces: {' ' in password}")
        print(f"Characters: {[c for c in password]}")
