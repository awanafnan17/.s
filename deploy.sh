#!/bin/bash

# IICE CRM Deployment Script
# This script automates the deployment process for the hosting environment

set -e  # Exit on any error

echo "🚀 Starting IICE CRM Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="IICE-CRM"
PROJECT_DIR="/home/iqraacad/public_html/$PROJECT_NAME"
VENV_DIR="/home/iqraacad/venv"
PYTHON_VERSION="python"

echo -e "${YELLOW}📁 Project Directory: $PROJECT_DIR${NC}"
echo -e "${YELLOW}🐍 Virtual Environment: $VENV_DIR${NC}"

# Check if Python is available
echo "🔍 Checking Python availability..."
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo -e "${RED}❌ Error: $PYTHON_VERSION is not installed or not in PATH${NC}"
    echo -e "${YELLOW}Please install Python first:${NC}"
    echo "  - For shared hosting: Contact your hosting provider"
    echo "  - For VPS: sudo apt install python3 python3-pip python3-venv (Ubuntu/Debian)"
    echo "  - For VPS: sudo yum install python3 python3-pip (CentOS/RHEL)"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python --version)${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as correct user
if [ "$USER" != "iqraacad" ]; then
    print_warning "This script should be run as user 'iqraacad'"
    print_warning "Current user: $USER"
fi

# Create project directory if it doesn't exist
echo "📂 Setting up project directory..."
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/staticfiles"
mkdir -p "$PROJECT_DIR/media"
print_status "Project directories created"

# Create virtual environment if it doesn't exist
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_VERSION -m venv "$VENV_DIR"
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
print_status "Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip
print_status "Pip upgraded"

# Install production requirements
echo "📦 Installing Python dependencies..."
if [ -f "requirements-production.txt" ]; then
    pip install -r requirements-production.txt
    print_status "Production requirements installed"
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Requirements installed"
else
    print_error "No requirements file found!"
    exit 1
fi

# Copy project files (assuming they're in current directory)
echo "📋 Copying project files..."
cp -r . "$PROJECT_DIR/"
print_status "Project files copied"

# Set up environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.production" ]; then
        cp "$PROJECT_DIR/.env.production" "$PROJECT_DIR/.env"
        print_status "Production environment file copied"
        print_warning "Please edit $PROJECT_DIR/.env with your actual configuration values"
    else
        print_error "No environment file found! Please create .env file"
        exit 1
    fi
else
    print_status "Environment file already exists"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run Django management commands
echo "🔧 Running Django setup commands..."

# Collect static files
echo "📦 Collecting static files..."
$PYTHON_VERSION manage.py collectstatic --noinput --settings=IICE.settings_production
print_status "Static files collected"

# Run database migrations
echo "🗄️  Running database migrations..."
$PYTHON_VERSION manage.py migrate --settings=IICE.settings_production
print_status "Database migrations completed"

# Create superuser (optional)
echo "👤 Creating superuser..."
echo "Do you want to create a superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    $PYTHON_VERSION manage.py createsuperuser --settings=IICE.settings_production
    print_status "Superuser created"
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
chmod -R 755 "$PROJECT_DIR"
chmod -R 777 "$PROJECT_DIR/media"
chmod -R 777 "$PROJECT_DIR/logs"
print_status "File permissions set"

# Create WSGI configuration for hosting
echo "🌐 Creating WSGI configuration..."
cat > "$PROJECT_DIR/passenger_wsgi.py" << EOF
import sys
import os

# Add project directory to Python path
sys.path.insert(0, '$PROJECT_DIR')

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF
print_status "WSGI configuration created"

# Create .htaccess file for Apache
echo "🔧 Creating .htaccess file..."
cat > "$PROJECT_DIR/.htaccess" << EOF
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ passenger_wsgi.py [QSA,L]

# Static files
RewriteRule ^static/(.*)$ /static/\$1 [L]
RewriteRule ^media/(.*)$ /media/\$1 [L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
EOF
print_status ".htaccess file created"

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "📋 Next steps:"
echo "1. Edit $PROJECT_DIR/.env with your actual configuration values"
echo "2. Set up your database and update database credentials in .env"
echo "3. Configure your domain to point to $PROJECT_DIR"
echo "4. Test the application by visiting your domain"
echo "5. Set up SSL certificate for HTTPS"
echo ""
echo "📁 Project location: $PROJECT_DIR"
echo "🌐 WSGI file: $PROJECT_DIR/passenger_wsgi.py"
echo "⚙️  Environment file: $PROJECT_DIR/.env"
echo ""
print_status "Deployment script completed!"