# 🚀 Shared Hosting Deployment Guide - PHP/MySQL

## ✅ PHP/MySQL Conversion Complete!

Your application has been fully converted from Python/FastAPI/MongoDB to PHP/MySQL and is ready for shared hosting deployment.

---

## 📦 What You Have

**Backend:** Pure PHP 7.4+ (no frameworks)
**Database:** MySQL 5.7+
**Frontend:** React (unchanged)
**PDF:** mPDF library (pure PHP, no system dependencies)

---

## 🎯 Deployment Steps

### Step 1: Prepare Your Shared Hosting

**Requirements:**
- PHP 7.4 or higher
- MySQL 5.7 or higher
- Apache with mod_rewrite enabled
- Composer (optional, for mPDF)

**Verify Your Hosting:**
1. Login to cPanel
2. Check PHP version (Software → Select PHP Version)
3. Ensure mod_rewrite is enabled
4. Note your MySQL credentials

---

### Step 2: Create MySQL Database

1. **Login to cPanel**
2. **Go to MySQL Databases**
3. **Create new database:**
   - Database name: `tileshop` (or your choice)
   - Create database user
   - Set password (save it!)
   - Grant ALL privileges to user

4. **Import Database Schema:**
   - Go to phpMyAdmin
   - Select your database
   - Click "Import"
   - Upload `/database/schema.sql`
   - Click "Go"

✅ Database is ready!

---

### Step 3: Upload Backend Files

**Using File Manager:**
1. Login to cPanel → File Manager
2. Navigate to `public_html` (or your web root)
3. Create folder: `backend-php`
4. Upload all files from `/backend-php/` to `public_html/backend-php/`

**Using FTP:**
1. Connect via FileZilla/WinSCP
2. Navigate to `public_html`
3. Upload `/backend-php/` folder

**Files to upload:**
```
backend-php/
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
├── pdfs/ (create this folder, set permissions 755)
├── .htaccess
├── index.php
└── composer.json (optional)
```

---

### Step 4: Configure Backend

1. **Edit `backend-php/config/database.php`:**

```php
// Update these lines:
define('DB_HOST', 'localhost');
define('DB_NAME', 'your_database_name');
define('DB_USER', 'your_mysql_username');
define('DB_PASS', 'your_mysql_password');

// Update app URL:
define('APP_URL', 'https://yourdomain.com');
define('CORS_ORIGIN', 'https://yourdomain.com');
```

2. **Set folder permissions:**
```bash
chmod 755 backend-php/pdfs
chmod 755 backend-php/uploads
```

---

### Step 5: Install mPDF (Optional but Recommended)

**Option A: Using Composer (if available):**
```bash
cd public_html/backend-php
composer install
```

**Option B: Manual Installation:**
1. Download mPDF: https://github.com/mpdf/mpdf/releases
2. Extract to `backend-php/vendor/`
3. Ensure autoload.php exists

**Option C: Skip (use HTML fallback):**
- PDF generator will create HTML files
- You can manually print to PDF from browser

---

### Step 6: Test Backend API

**Test in browser:**
```
https://yourdomain.com/backend-php/api/health
```

**Should return:**
```json
{
  "status": "ok",
  "message": "The Tile Shop API is running"
}
```

**Test database connection:**
```
https://yourdomain.com/backend-php/api/tiles
```

**Should return:**
```json
[]
```

✅ Backend is working!

---

### Step 7: Build & Upload Frontend

**On your local machine:**

1. **Update frontend environment:**
```bash
cd /app/frontend
```

2. **Edit `.env`:**
```
REACT_APP_BACKEND_URL=https://yourdomain.com/backend-php
```

3. **Build frontend:**
```bash
yarn build
```

4. **Upload to hosting:**
   - Upload contents of `frontend/build/` to `public_html/`
   - Or upload to subdomain/subfolder

---

### Step 8: Configure .htaccess for Frontend

**Create/Edit `public_html/.htaccess`:**

```apache
# React Router Support
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  
  # Don't rewrite backend API calls
  RewriteRule ^backend-php - [L]
  
  # React app routing
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /index.html [L]
</IfModule>
```

---

## ✅ Verification Checklist

After deployment, test:

- [ ] Visit https://yourdomain.com
- [ ] Login page loads
- [ ] Login works (Thetileshop / Vicky123)
- [ ] Dashboard loads
- [ ] Create a tile
- [ ] Create a customer
- [ ] Create an invoice
- [ ] Download PDF
- [ ] WhatsApp share (if configured)
- [ ] Delete tile/customer/invoice

---

## 🎯 File Structure on Server

```
public_html/
├── backend-php/              ← PHP API
│   ├── api/
│   ├── config/
│   ├── utils/
│   ├── assets/
│   ├── pdfs/
│   ├── .htaccess
│   └── index.php
├── static/                   ← React build files
│   ├── css/
│   └── js/
├── index.html                ← React app
├── manifest.json
└── .htaccess                 ← Root htaccess
```

---

## 🔧 Troubleshooting

### Issue: API returns 404

**Solution:**
- Check `.htaccess` is uploaded
- Verify mod_rewrite is enabled in cPanel
- Check file permissions (755 for folders, 644 for files)

### Issue: Database connection failed

**Solution:**
- Verify MySQL credentials in `config/database.php`
- Check database user has ALL privileges
- Ensure database exists

### Issue: PDF generation not working

**Solution:**
- Install mPDF via composer
- Or use HTML fallback (already implemented)
- Check `pdfs/` folder permissions (755)

### Issue: CORS errors in browser

**Solution:**
- Update `CORS_ORIGIN` in `config/database.php`
- Must match your frontend URL exactly

### Issue: 500 Internal Server Error

**Solution:**
- Check PHP error logs in cPanel
- Enable error display temporarily:
```php
error_reporting(E_ALL);
ini_set('display_errors', 1);
```
- Check file permissions

---

## 📱 Mobile/WhatsApp Configuration

WhatsApp share will work automatically. The frontend sends:
- Invoice PDF download link
- Invoice details

No backend changes needed for WhatsApp!

---

## 🔐 Security Recommendations

1. **Change default admin password:**
```sql
UPDATE admin_users 
SET password_hash = '$2y$10$new_hash_here' 
WHERE username = 'Thetileshop';
```

Generate hash in PHP:
```php
echo password_hash('your_new_password', PASSWORD_DEFAULT);
```

2. **Disable error display in production:**
```php
error_reporting(0);
ini_set('display_errors', 0);
```

3. **Secure database.php:**
- Don't commit to Git with real credentials
- Set file permissions to 644

4. **Enable HTTPS:**
- Get free SSL from cPanel (Let's Encrypt)
- Force HTTPS in .htaccess

---

## 🎉 You're Done!

Your application is now deployed on shared hosting!

**What you have:**
- ✅ PHP/MySQL backend running
- ✅ React frontend deployed
- ✅ Database configured
- ✅ PDF generation working
- ✅ All CRUD operations functional

**Access your app:**
- Frontend: https://yourdomain.com
- API: https://yourdomain.com/backend-php/api

**Login:**
- Username: Thetileshop
- Password: Vicky123

---

## 📚 Additional Resources

**cPanel Documentation:**
- File Manager: https://docs.cpanel.net/cpanel/files/file-manager/
- MySQL: https://docs.cpanel.net/cpanel/databases/mysql-databases/
- PHP Selector: https://docs.cpanel.net/cpanel/software/select-php-version/

**Support:**
- Contact your hosting provider for server-specific issues
- Check PHP version and extensions
- Verify mod_rewrite is enabled

---

## 🔄 Updating the Application

**To update:**
1. Pull latest code from Git
2. Build frontend (`yarn build`)
3. Upload changed files via FTP/File Manager
4. Clear browser cache

**Database changes:**
- Export current database (backup!)
- Apply new SQL migrations
- Test thoroughly

---

**Happy Deploying! 🚀**

Your invoice management system is now live on shared hosting!
