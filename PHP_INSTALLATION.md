# 📦 PHP/MySQL Installation - Quick Start

## ⚡ 5-Minute Local Setup

### Prerequisites
- PHP 7.4+ installed
- MySQL 5.7+ installed
- Apache with mod_rewrite
- Composer (optional)

---

## Step 1: Database Setup (2 min)

```bash
# Create database
mysql -u root -p

CREATE DATABASE tileshop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

# Import schema
mysql -u root -p tileshop < database/schema.sql
```

---

## Step 2: Configure Backend (1 min)

Edit `backend-php/config/database.php`:

```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'tileshop');
define('DB_USER', 'root');
define('DB_PASS', '');  // Your MySQL password
```

---

## Step 3: Install mPDF (1 min)

```bash
cd backend-php
composer install
```

*Or skip and use HTML fallback*

---

## Step 4: Start PHP Server (1 min)

```bash
cd backend-php
php -S localhost:8000
```

**Test:** http://localhost:8000/api/health

---

## Step 5: Build Frontend (2 min)

```bash
cd frontend

# Update .env
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env

# Install & start
yarn install
yarn start
```

**Open:** http://localhost:3000

---

## ✅ Login & Test

- **Username:** Thetileshop  
- **Password:** Vicky123

---

## 🎯 API Endpoints

```
GET    /api/tiles              - List all tiles
POST   /api/tiles              - Create tile
PUT    /api/tiles/:id          - Update tile
DELETE /api/tiles/:id          - Delete tile

GET    /api/customers          - List all customers
POST   /api/customers          - Create customer
PUT    /api/customers/:id      - Update customer
DELETE /api/customers/:id      - Delete customer

GET    /api/invoices           - List all invoices
POST   /api/invoices           - Create invoice
DELETE /api/invoices/:id       - Delete invoice
GET    /api/invoices/:id/pdf   - Generate PDF
```

---

## 🚀 Deploy to Shared Hosting

See **PHP_DEPLOYMENT_GUIDE.md** for complete deployment instructions.

Quick steps:
1. Upload `backend-php/` to `public_html/backend-php/`
2. Import `database/schema.sql` via phpMyAdmin
3. Configure `config/database.php` with hosting credentials
4. Build frontend and upload to `public_html/`
5. Done!

---

## 📁 Project Structure

```
/app
├── backend-php/           ✅ NEW - PHP Backend
│   ├── api/              - REST API endpoints
│   ├── config/           - Database config
│   ├── utils/            - Helper functions
│   ├── assets/           - Logo, templates
│   ├── pdfs/             - Generated PDFs
│   └── index.php         - Router
├── database/
│   └── schema.sql        ✅ MySQL schema
├── frontend/             ✅ React app (unchanged)
└── backend/              (Old Python - can remove)
```

---

## 🐛 Common Issues

**"Connection refused"**
- Check MySQL is running
- Verify credentials in database.php

**"404 Not Found"**
- Ensure .htaccess is in backend-php/
- Check mod_rewrite is enabled

**"Class 'Mpdf\\Mpdf' not found"**
- Run `composer install` in backend-php/
- Or use HTML fallback (automatic)

---

## 🎉 You're Ready!

- ✅ Backend API running
- ✅ Database configured  
- ✅ Frontend connected
- ✅ Ready to deploy!

**Next:** Read PHP_DEPLOYMENT_GUIDE.md for shared hosting deployment.
