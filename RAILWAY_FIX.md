# 🚂 Railway Deployment - FIXED!

## ✅ Error Fixed: Missing System Libraries

The error `cannot load library 'libgobject-2.0-0'` occurs because WeasyPrint needs system libraries that aren't installed by default.

---

## 🎯 SOLUTION: Use Dockerfile or Nixpacks

I've created **TWO solutions** - use either one:

### Option 1: Using Dockerfile (Recommended) ⭐

**Steps:**

1. **Push to GitHub** (make sure `backend/Dockerfile` is committed)

2. **Go to Railway**: https://railway.app

3. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository

4. **Railway will auto-detect Dockerfile**:
   - Railway sees `backend/Dockerfile` and uses it automatically
   - This installs all required system libraries

5. **Configure Service**:
   - Root Directory: `backend`
   - Dockerfile Path: `Dockerfile` (auto-detected)

6. **Add Environment Variables**:
   ```
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
   DB_NAME=tileshop
   CORS_ORIGINS=https://your-vercel-app.vercel.app
   ```

7. **Generate Domain**:
   - Go to Settings → Networking
   - Click "Generate Domain"
   - Copy your Railway URL

8. **Deploy** - Should work now! ✅

---

### Option 2: Using Nixpacks Configuration

If Railway doesn't use the Dockerfile, it will use `nixpacks.toml`:

**File created:** `backend/nixpacks.toml`

This tells Railway to install:
- cairo
- pango
- gdk-pixbuf
- libffi
- glib
- gobject-introspection

Railway will automatically detect and use this file.

---

## 📋 Files Created for Railway:

1. **backend/Dockerfile** ✅
   - Complete Python 3.11 environment
   - All WeasyPrint system dependencies
   - Production-ready

2. **backend/nixpacks.toml** ✅
   - Alternative configuration
   - Lists all required system packages

---

## 🔧 Railway Configuration Summary

**What Railway should detect:**

```
✓ Dockerfile found in backend/
✓ Python 3.11
✓ System dependencies: cairo, pango, libgobject, etc.
✓ Port: 8001 (or $PORT from Railway)
✓ Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 🐛 Troubleshooting

### Error still occurs?

**Solution 1: Check Railway Settings**
1. Go to Settings → Deploy
2. Verify "Root Directory" is set to `backend`
3. Verify Dockerfile is detected

**Solution 2: Force Dockerfile usage**
1. Add a `railway.toml` file:
   ```toml
   [build]
   builder = "DOCKERFILE"
   dockerfilePath = "Dockerfile"
   ```

**Solution 3: Check Build Logs**
1. Go to your deployment
2. Check "Build Logs"
3. Verify it says "Using Dockerfile"
4. Verify system packages are being installed

---

## ✅ Verification

After deployment, test:

1. **Backend is accessible:**
   ```bash
   curl https://your-app.railway.app/api/tiles
   ```
   Should return: `[]`

2. **Health check works:**
   Your backend should respond without errors

3. **PDF generation works:**
   Create an invoice and test PDF download

---

## 🎯 Complete Railway Deployment Steps

### Step 1: Prepare Repository
```bash
cd /app
git add backend/Dockerfile backend/nixpacks.toml
git commit -m "Add Railway deployment config with system dependencies"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repository
4. Railway auto-detects Dockerfile ✅

### Step 3: Configure
1. Set Root Directory: `backend`
2. Add environment variables:
   - `MONGO_URL`
   - `DB_NAME`
   - `CORS_ORIGINS`

### Step 4: Generate Domain & Test
1. Settings → Generate Domain
2. Test: `https://your-app.railway.app/api/tiles`
3. ✅ Should work!

---

## 📊 Expected Build Output

```
Building with Dockerfile...
Step 1/8 : FROM python:3.11-slim
Step 2/8 : WORKDIR /app
Step 3/8 : RUN apt-get update && apt-get install...
  Installing libcairo2... ✓
  Installing libpango-1.0-0... ✓
  Installing libgobject-2.0-0... ✓
Step 4/8 : COPY requirements.txt .
Step 5/8 : RUN pip install...
  Installing weasyprint... ✓
  Installing fastapi... ✓
...
Successfully built
Starting server...
Uvicorn running on 0.0.0.0:8001 ✓
```

---

## 🎉 That's It!

The Dockerfile includes all system dependencies needed by WeasyPrint.

Your Railway deployment should now work perfectly! 🚀

---

## 💡 Why This Works

**The Problem:**
- WeasyPrint needs system libraries (libgobject, cairo, pango)
- Railway's default Python environment doesn't have these
- Runtime error occurs when trying to load these libraries

**The Solution:**
- Dockerfile explicitly installs all required system libraries
- Built into the Docker image during deployment
- Everything WeasyPrint needs is available at runtime

---

## 🆘 Still Having Issues?

1. **Check build logs** - Verify Dockerfile is being used
2. **Verify environment variables** are set correctly
3. **Check MongoDB connection** is working
4. **Test locally** with Docker:
   ```bash
   cd backend
   docker build -t tileshop-backend .
   docker run -p 8001:8001 tileshop-backend
   ```

If local Docker works but Railway doesn't, check Railway settings.
