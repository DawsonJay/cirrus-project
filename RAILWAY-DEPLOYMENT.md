# Railway Deployment Guide

## Overview
This guide will help you deploy the Weather Data Service to Railway, a free cloud platform perfect for your project.

## Prerequisites
- GitHub account
- Railway account (free at railway.app)
- NOAA API token (get from https://www.ncdc.noaa.gov/cdo-web/token)

## Step 1: Prepare Your Repository

### 1.1 Push to GitHub
```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: Weather Data Service ready for Railway deployment"

# Create GitHub repository and push
# (Do this on GitHub.com or via GitHub CLI)
git remote add origin https://github.com/your-username/cirrus-project.git
git branch -M main
git push -u origin main
```

### 1.2 Verify Files
Make sure these files are in your repository:
- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `weather-data-service/` - Main application directory
- `weather-data-service/railway.env` - Environment template

## Step 2: Deploy to Railway

### 2.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Authorize Railway to access your repositories

### 2.2 Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `cirrus-project` repository
4. Click "Deploy Now"

### 2.3 Add PostgreSQL Database
1. In your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Wait for database to be created
4. Note the connection details

### 2.4 Configure Environment Variables
1. Go to your service settings
2. Click "Variables" tab
3. Add these environment variables:

```
NOAA_CDO_TOKEN=your_actual_noaa_token_here
DATABASE_URL=postgresql://user:password@host:port/database
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
MAX_CONCURRENT_COLLECTIONS=3
DEFAULT_STATION_LIMIT=100
```

**Important**: Replace `your_actual_noaa_token_here` with your real NOAA API token!

### 2.5 Deploy
1. Railway will automatically build and deploy your service
2. Wait for deployment to complete (5-10 minutes)
3. Your service will be available at a Railway URL like: `https://your-app-name.railway.app`

## Step 3: Verify Deployment

### 3.1 Check Health
```bash
curl https://your-app-name.railway.app/health
```

### 3.2 Check API Documentation
Visit: `https://your-app-name.railway.app/docs`

### 3.3 Test Data Collection
```bash
curl -X POST https://your-app-name.railway.app/collect/year \
  -H "Content-Type: application/json" \
  -d '{"year": 2024, "limit": 5}'
```

## Step 4: Configure Custom Domain (Optional)

### 4.1 Add Custom Domain
1. Go to your service settings
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Follow Railway's DNS instructions

### 4.2 SSL Certificate
Railway automatically provides SSL certificates for all domains.

## Step 5: Monitor Your Service

### 5.1 Railway Dashboard
- View logs in real-time
- Monitor resource usage
- Check deployment status

### 5.2 Health Monitoring
- Service health: `https://your-app-name.railway.app/health`
- Collection status: `https://your-app-name.railway.app/status`
- Weather data: `https://your-app-name.railway.app/weather-data`

## Troubleshooting

### Common Issues

#### Database Connection Error
- Check that `DATABASE_URL` is set correctly
- Verify PostgreSQL service is running
- Check database credentials

#### API Not Responding
- Check service logs in Railway dashboard
- Verify environment variables are set
- Check if service is running

#### Data Collection Not Working
- Verify `NOAA_CDO_TOKEN` is set correctly
- Check API logs for errors
- Test with manual collection trigger

### Getting Help
1. Check Railway logs: Dashboard → Your Service → Logs
2. Check service health: `/health` endpoint
3. Test API endpoints: `/docs` for interactive documentation

## Cost
- **Free Tier**: $5/month credit
- **Your Usage**: ~$2-3/month (well within free tier)
- **No Credit Card Required** for free tier

## Next Steps
Once deployed, your weather data service will:
- ✅ Run 24/7 in the cloud
- ✅ Collect data daily at 2:00 AM
- ✅ Provide API access worldwide
- ✅ Store data in PostgreSQL database
- ✅ Scale automatically with traffic

## Support
- Railway Documentation: https://docs.railway.app
- Railway Community: https://discord.gg/railway
- Your Service Logs: Railway Dashboard → Logs

---

**🎉 Congratulations! Your Weather Data Service is now running in the cloud!**
