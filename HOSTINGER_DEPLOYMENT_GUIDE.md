# Hostinger Deployment Guide - The Tile Shop

## What Was Fixed
- Changed PDF endpoint from `/api/public/invoices/{id}/pdf` to `/api/invoices/{id}/pdf`
- This matches your PHP backend API structure

## Files Ready for Deployment

### 1. Frontend Build
**File:** `frontend-build-for-hostinger.zip`

Contains the React app built and ready for deployment.

---

## Deployment Steps

### Step 1: Configure Your Frontend Environment

Before uploading, you need to update the `.env` file in the frontend with your Hostinger domain:

```bash
REACT_APP_BACKEND_URL=https://yourdomain.com
```

**Replace `yourdomain.com` with your actual Hostinger domain.**

If you've already built the app with the wrong URL, you'll need to:
1. Update `/app/frontend/.env` with your domain
2. Run `yarn build` again
3. Download the new build

### Step 2: Upload PHP Backend (If Not Already Done)

Upload the contents of `backend-php/` to your Hostinger:
- `public_html/api/` or wherever your API is hosted

### Step 3: Upload Frontend Build

1. Extract `frontend-build-for-hostinger.zip`
2. Upload the contents of the `build/` folder to your Hostinger `public_html/` directory
3. Your file structure should look like:
   ```
   public_html/
   ├── index.html          (from build/)
   ├── static/             (from build/)
   │   ├── css/
   │   └── js/
   ├── api/                (your PHP backend)
   │   ├── index.php
   │   ├── config/
   │   ├── api/
   │   └── ...
   ```

### Step 4: Configure .htaccess for React Router

Create or update `.htaccess` in your `public_html/` directory:

```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    
    # Don't rewrite API requests
    RewriteRule ^api/(.*)$ api/index.php [L,QSA]
    
    # Serve static files directly
    RewriteCond %{REQUEST_FILENAME} -f [OR]
    RewriteCond %{REQUEST_FILENAME} -d
    RewriteRule ^ - [L]
    
    # Redirect all other requests to index.html (React Router)
    RewriteRule ^ index.html [L]
</IfModule>
```

### Step 5: Update PHP Database Config

Edit `api/config/database.php` with your Hostinger MySQL credentials:

```php
define('DB_HOST', 'localhost');           
define('DB_NAME', 'your_database_name');  
define('DB_USER', 'your_mysql_username'); 
define('DB_PASS', 'your_mysql_password'); 
```

### Step 6: Import Database Schema

1. Go to Hostinger hPanel → Databases → phpMyAdmin
2. Select your database
3. Import `database.sql` (or `database/schema.sql`)

---

## Testing Checklist

After deployment, test these features:

- [ ] Login works (Username: `Thetileshop`, Password: `Vicky123`)
- [ ] View tiles list
- [ ] View customers list
- [ ] Create new invoice
- [ ] Download PDF
- [ ] Share on WhatsApp

---

## API Endpoints Reference

| Feature | Endpoint | Method |
|---------|----------|--------|
| Get tiles | `/api/tiles` | GET |
| Get customers | `/api/customers` | GET |
| Get invoices | `/api/invoices` | GET |
| Create invoice | `/api/invoices` | POST |
| Delete invoice | `/api/invoices/{id}` | DELETE |
| Download PDF | `/api/invoices/{id}/pdf` | GET |

---

## Troubleshooting

### "Error creating invoice"
- Check database connection in `config/database.php`
- Verify MySQL credentials are correct

### PDF not downloading
- Check if `pdfs/` directory exists and is writable
- Verify mPDF library is installed (run `composer install`)

### CORS errors
- Verify `Access-Control-Allow-Origin` headers in `index.php`
- Check that your frontend URL matches

### 404 errors on refresh
- Ensure `.htaccess` file is uploaded correctly
- Enable `mod_rewrite` in Hostinger settings
