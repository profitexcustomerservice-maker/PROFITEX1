#!/bin/bash
# Render build script

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "Build completed successfully!"
