#!/bin/bash
# Hostinger Configuration Helper
# Run this before uploading to set your credentials

echo "======================================"
echo "  HOSTINGER CONFIGURATION SETUP"
echo "======================================"
echo ""

# Get database credentials
read -p "Enter your Hostinger database name (e.g., u123456_tileshop): " DB_NAME
read -p "Enter your database username (e.g., u123456_dbuser): " DB_USER
read -sp "Enter your database password: " DB_PASS
echo ""
read -p "Enter your domain (e.g., https://yourdomain.com): " DOMAIN

# Update backend config
CONFIG_FILE="api/config/database.php"

if [ -f "$CONFIG_FILE" ]; then
    # Backup original
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    
    # Update database credentials
    sed -i "s/define('DB_NAME', '.*');/define('DB_NAME', '$DB_NAME');/" "$CONFIG_FILE"
    sed -i "s/define('DB_USER', '.*');/define('DB_USER', '$DB_USER');/" "$CONFIG_FILE"
    sed -i "s/define('DB_PASS', '.*');/define('DB_PASS', '$DB_PASS');/" "$CONFIG_FILE"
    
    # Update domain
    sed -i "s#define('APP_URL', '.*');#define('APP_URL', '$DOMAIN');#" "$CONFIG_FILE"
    sed -i "s#define('CORS_ORIGIN', '.*');#define('CORS_ORIGIN', '$DOMAIN');#" "$CONFIG_FILE"
    
    echo ""
    echo "✅ Configuration updated successfully!"
    echo ""
    echo "📋 Your settings:"
    echo "   Database: $DB_NAME"
    echo "   Username: $DB_USER"
    echo "   Domain: $DOMAIN"
    echo ""
    echo "📁 Files ready to upload:"
    echo "   1. Upload 'api/' folder to public_html/api/"
    echo "   2. Upload 'frontend/' contents to public_html/"
    echo "   3. Import 'schema.sql' via phpMyAdmin"
    echo ""
    echo "📖 Read README.md for complete instructions"
    echo ""
else
    echo "❌ Error: Config file not found!"
    echo "Make sure you're in the deployment-package directory"
fi
