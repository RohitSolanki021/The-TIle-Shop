# Vercel Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Backend Deployment (Deploy First!)
- [ ] Create MongoDB Atlas account and cluster
- [ ] Get MongoDB connection string
- [ ] Choose backend hosting (Railway recommended)
- [ ] Deploy backend with environment variables:
  - `MONGO_URL`: Your MongoDB Atlas connection string
  - `DB_NAME`: tileshop
  - `PORT`: 8001 (or as required by host)
- [ ] Test backend endpoint: `https://your-backend.railway.app/api/tiles`
- [ ] Note down your backend URL

### 2. Repository Configuration
- [x] Root `package.json` created
- [x] `vercel.json` configured
- [x] `.vercelignore` added
- [x] Build scripts tested locally
- [x] ESLint warnings fixed
- [x] Frontend builds successfully

### 3. Vercel Deployment
- [ ] Push code to GitHub/GitLab/Bitbucket
- [ ] Go to https://vercel.com and sign in
- [ ] Click "Import Project"
- [ ] Select your repository
- [ ] Vercel will auto-detect the configuration
- [ ] Add environment variable in Vercel dashboard:
  - Key: `REACT_APP_BACKEND_URL`
  - Value: `https://your-backend.railway.app` (your backend URL from step 1)
- [ ] Click "Deploy"
- [ ] Wait for build to complete (~2-3 minutes)

### 4. Post-Deployment Testing
- [ ] Visit your Vercel URL
- [ ] Test login (Username: Thetileshop, Password: Vicky123)
- [ ] Test creating a tile
- [ ] Test creating a customer
- [ ] Test creating an invoice
- [ ] Test PDF generation
- [ ] Test WhatsApp share
- [ ] Test delete functionality

## 🔧 Troubleshooting

### Build Fails
- Check build logs in Vercel dashboard
- Ensure `REACT_APP_BACKEND_URL` is set
- Verify `yarn build` works locally

### Frontend Works but Backend Calls Fail
- Check CORS settings in backend
- Verify `REACT_APP_BACKEND_URL` is correct
- Check backend is running and accessible
- Check browser console for errors

### PDF Generation Fails
- Ensure backend has all dependencies installed
- Check WeasyPrint system dependencies on your backend host
- Verify MongoDB connection works

## 📊 Expected Build Output

```
✓ Creating an optimized production build...
✓ Compiled successfully
✓ File sizes after gzip:
  264.03 kB  build/static/js/main.ea7135c3.js
  11.57 kB   build/static/css/main.f1f322d7.css
✓ Build completed
```

## 🎯 Backend Hosting Options

### Railway (Recommended) ⭐
- Easiest setup
- Automatic HTTPS
- Good free tier
- Great for Python apps

### Render
- Similar to Railway
- Good free tier
- Easy MongoDB integration

### Heroku
- Mature platform
- No free tier (paid only)
- Easy deployment

### VPS (DigitalOcean, AWS EC2)
- Full control
- Requires more setup
- Best for production

## 🔗 Useful Links

- Vercel Dashboard: https://vercel.com/dashboard
- Railway: https://railway.app
- Render: https://render.com
- MongoDB Atlas: https://cloud.mongodb.com

---

## Common Errors & Solutions

### "Module not found" Error
**Solution**: Make sure all dependencies are in `frontend/package.json` and run `yarn install`

### "Backend URL not defined" Error
**Solution**: Set `REACT_APP_BACKEND_URL` environment variable in Vercel

### "CORS Error"
**Solution**: Add your Vercel domain to backend CORS allowed origins

### "Build Timeout"
**Solution**: The build is too large. Check for any accidentally included large files in the build.

---

**Ready to deploy? Follow the checklist above step by step!**
