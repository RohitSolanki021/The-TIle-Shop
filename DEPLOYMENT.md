# The Tile Shop - Deployment Guide

## Vercel Deployment (Frontend Only)

This configuration deploys only the React frontend to Vercel. The backend needs to be hosted separately.

### Prerequisites
1. MongoDB database (use MongoDB Atlas for cloud hosting)
2. Backend hosting service (Railway, Render, Heroku, or any VPS)

### Step 1: Deploy Backend
Choose one of these options:

**Option A: Railway (Recommended)**
1. Go to [Railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Select the `backend` directory
4. Add environment variables:
   - `MONGO_URL`: Your MongoDB connection string
   - `DB_NAME`: tileshop
   - `PORT`: 8001
5. Railway will provide a URL like: `https://your-app.railway.app`

**Option B: Render**
1. Go to [Render.com](https://render.com)
2. Create new Web Service
3. Root Directory: `backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (same as above)

### Step 2: Deploy Frontend to Vercel
1. Go to [Vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Vercel will auto-detect the configuration from `vercel.json`
4. Add environment variable:
   - `REACT_APP_BACKEND_URL`: Your backend URL from Step 1 (e.g., `https://your-app.railway.app`)
5. Deploy!

### Environment Variables

**Backend (.env)**
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=tileshop
PORT=8001
```

**Frontend (.env)**
```
REACT_APP_BACKEND_URL=https://your-backend-url.railway.app
```

### Vercel Configuration Files

The repository includes:
- `vercel.json` - Frontend-only deployment configuration
- `package.json` - Root build scripts for Vercel
- `frontend/package.json` - Frontend dependencies

### Post-Deployment
1. Verify backend is accessible at: `https://your-backend-url/api/tiles`
2. Verify frontend loads at your Vercel URL
3. Test the complete flow: Create tiles, customers, invoices

---

## Alternative: Full-Stack Vercel Deployment

If you want to deploy both frontend and backend to Vercel (using serverless functions), you would need to:

1. Convert FastAPI routes to Vercel serverless functions (Python)
2. Handle MongoDB connections in serverless context
3. Manage cold starts and timeout limits

This approach is more complex and not recommended for this application due to:
- PDF generation (can timeout on serverless)
- WeasyPrint dependencies (may not work in Vercel's environment)
- MongoDB persistent connections

**Recommended**: Use the split deployment approach above.
