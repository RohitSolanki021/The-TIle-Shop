# 🚀 Quick Start: Deploy to Vercel

## Step-by-Step Deployment Guide

### 📋 What You'll Need
- GitHub account
- Vercel account (free)
- MongoDB Atlas account (free)
- Railway account (free) OR Render account (free)

---

## 🎯 Part 1: Setup MongoDB (5 minutes)

1. **Go to MongoDB Atlas**: https://cloud.mongodb.com
2. **Create a free cluster**:
   - Click "Build a Database"
   - Select "Free" tier (M0)
   - Choose your region
   - Click "Create Cluster"
3. **Create database user**:
   - Go to "Database Access"
   - Click "Add New Database User"
   - Username: `tileshop_admin`
   - Password: (generate and save it!)
   - Database User Privileges: Read and write to any database
4. **Allow network access**:
   - Go to "Network Access"
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (0.0.0.0/0)
5. **Get connection string**:
   - Go to "Database" → "Connect"
   - Click "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your password
   - Example: `mongodb+srv://tileshop_admin:yourpassword@cluster0.xxxxx.mongodb.net/`

---

## 🎯 Part 2: Deploy Backend to Railway (10 minutes)

### Option A: Railway (Recommended)

1. **Go to Railway**: https://railway.app
2. **Sign in with GitHub**
3. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repo
   - Select your repository
4. **Configure Service**:
   - Click "Add variables"
   - Add these environment variables:
     ```
     MONGO_URL=mongodb+srv://tileshop_admin:yourpassword@cluster0.xxxxx.mongodb.net/
     DB_NAME=tileshop
     PORT=8001
     CORS_ORIGINS=https://your-vercel-app.vercel.app
     ```
     (You'll update CORS_ORIGINS after Vercel deployment)
   
5. **Configure Build**:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt && apt-get update && apt-get install -y libpangoft2-1.0-0 libpango-1.0-0 libpangocairo-1.0-0`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

6. **Get your Railway URL**:
   - Click on your deployment
   - Go to "Settings" → "Generate Domain"
   - Copy the URL (e.g., `https://your-app.railway.app`)

7. **Test backend**:
   - Visit `https://your-app.railway.app/api/tiles`
   - Should return: `[]` (empty array)

### Option B: Render

1. **Go to Render**: https://render.com
2. **Sign in with GitHub**
3. **New Web Service**:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
4. **Configure**:
   - Name: `tileshop-backend`
   - Root Directory: `backend`
   - Runtime: `Python 3.11`
   - Build Command: 
     ```
     pip install -r requirements.txt && apt-get update && apt-get install -y libpangoft2-1.0-0 libpango-1.0-0 libpangocairo-1.0-0
     ```
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables** (same as Railway)
6. **Deploy and get URL**

---

## 🎯 Part 3: Deploy Frontend to Vercel (5 minutes)

1. **Go to Vercel**: https://vercel.com
2. **Sign in with GitHub**
3. **Import Project**:
   - Click "Add New" → "Project"
   - Select your repository
4. **Configure Project**:
   - Framework Preset: Vercel will auto-detect (React)
   - Root Directory: Leave as `/` (Vercel will use vercel.json config)
   - Build Command: Will use from `vercel.json`
   - Output Directory: Will use from `vercel.json`

5. **Add Environment Variable**:
   - Key: `REACT_APP_BACKEND_URL`
   - Value: `https://your-app.railway.app` (your Railway URL from Part 2)

6. **Deploy**:
   - Click "Deploy"
   - Wait 2-3 minutes for build

7. **Get your Vercel URL**:
   - After deployment, copy your Vercel URL
   - Example: `https://the-tile-shop.vercel.app`

---

## 🎯 Part 4: Update CORS (2 minutes)

1. **Go back to Railway/Render**
2. **Update CORS_ORIGINS**:
   - Change from `*` to your actual Vercel URL
   - Example: `https://the-tile-shop.vercel.app`
3. **Redeploy backend** (if needed)

---

## ✅ Part 5: Test Your Deployment

1. **Visit your Vercel URL**
2. **Login**:
   - Username: `Thetileshop`
   - Password: `Vicky123`
3. **Test features**:
   - ✅ Create a tile (e.g., 600x600mm, coverage 3.0, packing 4)
   - ✅ Create a customer
   - ✅ Create an invoice
   - ✅ Download PDF
   - ✅ Test WhatsApp share
   - ✅ Test delete functions

---

## 🐛 Troubleshooting

### Backend not responding
- Check Railway/Render logs
- Verify environment variables are set
- Check MongoDB connection string is correct

### Frontend loads but no data
- Open browser console (F12)
- Check for CORS errors
- Verify `REACT_APP_BACKEND_URL` is set correctly in Vercel
- Verify backend URL is accessible

### PDF generation fails
- Check backend logs
- Ensure WeasyPrint dependencies are installed
- May need to add system dependencies in Railway/Render

### "Module not found" error
- Check all files committed to GitHub
- Verify `package.json` has all dependencies

---

## 📝 Environment Variables Summary

### Backend (Railway/Render)
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=tileshop
PORT=8001
CORS_ORIGINS=https://your-app.vercel.app
```

### Frontend (Vercel)
```
REACT_APP_BACKEND_URL=https://your-backend.railway.app
```

---

## 🎉 You're Done!

Your application is now live and accessible worldwide!

- **Frontend**: https://your-app.vercel.app
- **Backend**: https://your-backend.railway.app

Share your frontend URL with users!

---

## 💡 Tips

1. **Custom Domain**: Add custom domain in Vercel settings
2. **Auto Deploy**: Push to GitHub = auto deploy to Vercel
3. **Monitoring**: Check logs in Vercel and Railway dashboards
4. **Backups**: MongoDB Atlas has automatic backups

---

## 🆘 Need Help?

- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- MongoDB Atlas Docs: https://docs.atlas.mongodb.com

---

**Ready? Start with Part 1! 🚀**
