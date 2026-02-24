# 🚀 HOSTINGER DEPLOYMENT - Complete Guide

## 📦 Package Contents for Upload

You need to upload these folders to Hostinger:

```
public_html/
├── backend-php/          ← Upload this to public_html/api/
└── frontend/build/       ← Upload contents to public_html/
```

---

## STEP 1: Prepare Database on Hostinger

### 1.1 Create MySQL Database

1. Login to **Hostinger hPanel**
2. Go to **"Databases" → "MySQL Databases"**
3. Click **"Create New Database"**
   - Database name: `u123456_tileshop` (Hostinger adds prefix automatically)
   - Username: Create new or use existing
   - Password: Set strong password
   - **SAVE THESE CREDENTIALS!**

### 1.2 Import Database Schema

1. Click **"Manage"** next to your database
2. Opens phpMyAdmin
3. Select your database from left sidebar
4. Click **"Import"** tab
5. Click **"Choose File"**
6. Upload: `/app/database/schema.sql`
7. Click **"Go"**
8. ✅ Success! Tables created

---

## STEP 2: Configure PHP Backend

### 2.1 Update Database Config

Edit `backend-php/config/database.php`:

```php
// Line 8-11: Update with YOUR Hostinger credentials
define('DB_HOST', 'localhost');  // Usually 'localhost' on Hostinger
define('DB_NAME', 'u123456_tileshop');  // Your actual database name
define('DB_USER', 'u123456_dbuser');     // Your database username  
define('DB_PASS', 'YourStrongPassword'); // Your database password

// Line 15-16: Update with YOUR domain
define('APP_URL', 'https://yourdomain.com');
define('CORS_ORIGIN', 'https://yourdomain.com');
```

### 2.2 Install mPDF (For PDF Generation)

**Option A: Using Composer on Hostinger** (if available)
```bash
cd public_html/api
composer install
```

**Option B: Manual Upload** (if no Composer)
1. Download mPDF: https://github.com/mpdf/mpdf/releases/latest
2. Extract to `backend-php/vendor/mpdf/`
3. Upload entire `vendor/` folder

**Option C: Use HTML Fallback** (Already implemented)
- PDF generator will create HTML files
- Still works, just not as polished

---

## STEP 3: Upload Files to Hostinger

### 3.1 Upload Backend

**Using File Manager:**
1. Login to hPanel
2. Go to **"Files" → "File Manager"**
3. Navigate to `public_html/`
4. Create folder: `api`
5. Upload ALL files from `/app/backend-php/` into `public_html/api/`

**Files to upload:**
```
public_html/api/
├── api/
│   ├── tiles.php
│   ├── customers.php
│   └── invoices.php
├── config/
│   └── database.php
├── utils/
│   ├── invoice_helper.php
│   └── pdf_generator.php
├── assets/
│   └── (logo files)
├── pdfs/  (create empty folder)
├── .htaccess
├── index.php
└── composer.json
```

### 3.2 Set Folder Permissions

In File Manager:
1. Right-click `api/pdfs/` folder
2. Select **"Permissions"**
3. Set to **755** or **775**
4. Click "Change"

---

## STEP 4: Build & Upload Frontend

### 4.1 Build Frontend Locally

On your computer:

```bash
cd /app/frontend

# Create production .env
echo "REACT_APP_BACKEND_URL=https://yourdomain.com/api" > .env

# Build
yarn build
```

### 4.2 Upload Frontend to Hostinger

1. Go to File Manager → `public_html/`
2. Upload **ALL contents** from `frontend/build/` directly to `public_html/`
   - index.html
   - static/ folder
   - manifest.json
   - etc.

**Final structure:**
```
public_html/
├── api/           ← Backend PHP
├── static/        ← React built files
├── index.html     ← React app entry
└── manifest.json
```

---

## STEP 5: Configure .htaccess

### 5.1 Root .htaccess

Create/Edit `public_html/.htaccess`:

```apache
# PHP Settings
php_value upload_max_filesize 10M
php_value post_max_size 10M
php_value max_execution_time 300

# React Router Support
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  
  # Don't rewrite API calls
  RewriteRule ^api/ - [L]
  
  # React app routing
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /index.html [L]
</IfModule>

# Security
<FilesMatch "^\.">
    Order allow,deny
    Deny from all
</FilesMatch>

# Disable directory listing
Options -Indexes
```

### 5.2 API .htaccess

Already included in `backend-php/.htaccess` - No changes needed!

---

## STEP 6: Test Your Deployment

### 6.1 Test Backend API

Open browser:
```
https://yourdomain.com/api/health
```

Should show:
```json
{"status":"ok","message":"The Tile Shop API is running","timestamp":"2025-..."}
```

### 6.2 Test Database Connection

```
https://yourdomain.com/api/tiles
```

Should show:
```json
[]
```

### 6.3 Test Frontend

```
https://yourdomain.com
```

Should show: Login page ✅

---

## STEP 7: Login & Use

**Login Credentials:**
- Username: `Thetileshop`
- Password: `Vicky123`

**Test Flow:**
1. Create a tile
2. Create a customer
3. Create an invoice
4. Download PDF ✅
5. Share on WhatsApp ✅

---

## 🐛 Troubleshooting

### Backend shows 500 Error

**Check:**
1. Database credentials in `config/database.php`
2. PHP error logs in hPanel → "Advanced" → "Error Logs"
3. Folder permissions on `pdfs/` folder

### Frontend shows blank page

**Check:**
1. Browser console (F12) for errors
2. Verify `REACT_APP_BACKEND_URL` in built files
3. Check `.htaccess` is uploaded

### PDF generation fails

**Check:**
1. mPDF installed (`vendor/` folder exists)
2. `pdfs/` folder has write permissions (755/775)
3. PHP memory limit (increase in hPanel if needed)

### CORS errors

**Fix:**
1. Update `CORS_ORIGIN` in `config/database.php`
2. Must match your actual domain exactly

---

## 📁 Checklist Before Upload

Backend:
- [ ] Updated `config/database.php` with Hostinger credentials
- [ ] Updated `APP_URL` and `CORS_ORIGIN`
- [ ] Created `pdfs/` folder
- [ ] Uploaded all backend files to `public_html/api/`
- [ ] Set permissions on `pdfs/` to 755

Frontend:
- [ ] Built with correct `REACT_APP_BACKEND_URL`
- [ ] Uploaded `build/` contents to `public_html/`
- [ ] Uploaded root `.htaccess`

Database:
- [ ] Created MySQL database
- [ ] Imported `schema.sql`
- [ ] Noted credentials

Testing:
- [ ] Tested `/api/health` endpoint
- [ ] Tested `/api/tiles` endpoint
- [ ] Logged into frontend
- [ ] Created test invoice
- [ ] Downloaded PDF
- [ ] Tested WhatsApp share

---

## 🎉 You're Live!

Your application is now running on Hostinger with PHP/MySQL!

**Access:**
- Website: https://yourdomain.com
- API: https://yourdomain.com/api

**Manage:**
- Database: hPanel → Databases → phpMyAdmin
- Files: hPanel → File Manager
- Logs: hPanel → Error Logs

---

## 📞 Hostinger Support

If you encounter hosting-specific issues:
- **Live Chat:** Available 24/7 in hPanel
- **Knowledge Base:** https://support.hostinger.com
- **PHP Version:** Change in hPanel → "Advanced" → "PHP Configuration"

---

**Happy Hosting! 🚀**
