# 🚀 One-Click Deployment Guide

Deploy **Weird Flights** for free in 5 minutes!

## Option 1: Netlify (Easiest - Recommended)

### One-Click Deploy Button
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/YOUR-USERNAME/wierdFlights)

*Note: Replace `YOUR-USERNAME` with your GitHub username after you push the code*

### Manual Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR-USERNAME/wierdFlights.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repo
   - Click "Deploy site"

3. **Enable Automated Daily Scraping**
   - In your repo, go to "Actions"
   - You should see "Daily Flight Scrape" workflow
   - It will automatically:
     - Scrape all flights every day at 2 AM UTC
     - Commit updated `flights.json` to your repo
     - Netlify automatically redeploys with new data

4. **Test the Workflow (Optional but Recommended)**
   - Go to https://github.com/YOUR-USERNAME/weirdFlights/actions
   - Click "Daily Flight Scrape"
   - Click "Run workflow" → "Run workflow"
   - Wait 30 seconds and refresh
   - You should see it complete with green checkmark
   - Verify `flights.json` was updated in your repo

**Your site will be live at:** `https://your-site-name.netlify.app`

---

## Option 2: Vercel

1. **Push to GitHub** (same as above)
2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repo
   - Click "Deploy"

3. **Enable Daily Scraping** (same GitHub Actions setup as Netlify)

**Your site will be live at:** `https://your-project.vercel.app`

---

## Option 3: GitHub Pages + GitHub Actions

1. **Push to GitHub** (same as above)
2. **Enable GitHub Pages**
   - Go to repo Settings → Pages
   - Set source to "main" branch
   - Save

3. **Daily Scraping**
   - GitHub Actions will automatically run the scraper daily
   - Commits updated data to your repo
   - GitHub Pages auto-updates

**Your site will be live at:** `https://YOUR-USERNAME.github.io/wierdFlights/`

---

## How It Works

**Frontend:**
- Static HTML/CSS/JS deployed to CDN (Netlify/Vercel/GitHub Pages)
- Loads flight data from `flights.json`
- No server required!

**Data Updates:**
- GitHub Actions runs scraper daily at 2 AM UTC
- Scraper queries Norse Atlantic Airways API
- Updates `flights.json` automatically
- Commits changes back to GitHub
- Hosting provider auto-redeploys with new data

---

## Customization

### Change Scraping Schedule
Edit `.github/workflows/daily-scrape.yml`:
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Change this (see https://crontab.guru)
```

### Add/Remove Routes
Edit `norse_scraper.py`:
```python
ROUTES = [
    ("LGW", "BKK"),  # Add/remove routes here
    ("LGW", "JFK"),
]
```

### Custom Domain
In Netlify/Vercel settings:
- Add your custom domain
- Update DNS records
- Site will be available at your domain

---

## Troubleshooting

### GitHub Actions Workflow Issues

**Workflow fails with "refusing to allow a Personal Access Token..."**
- The token needs `workflow` scope
- Go to https://github.com/settings/tokens
- Click your token, then "Regenerate token"
- Check both:
  - ✅ `repo` (all)
  - ✅ `workflow` (write access for commits)
- Click "Regenerate"
- Copy new token and try pushing again

**Workflow shows permission denied errors**
- The `.github/workflows/daily-scrape.yml` file needs write permissions
- Ensure the file contains:
  ```yaml
  jobs:
    scrape:
      runs-on: ubuntu-latest
      permissions:
        contents: write
  ```
- Commit and push this fix if missing

**Scraper Not Running?**
- Go to https://github.com/YOUR-USERNAME/weirdFlights/actions
- Click "Daily Flight Scrape" workflow
- Check if any runs appear
- Click a run to view detailed logs
- Manual trigger: click "Run workflow" → "Run workflow"
- Wait ~30 seconds for it to complete

**Data Not Updating?**
- Check GitHub Actions logs (click the workflow run)
- Look for HTTP errors (403, 440 = token expired)
- Verify `flights.json` was created/modified in the repo
- Wait for next scheduled run (2 AM UTC daily)
- Netlify redeploys automatically when files change

### API Token Expired

**Error: 403 or 440 errors in workflow logs**
1. Go to https://flynorse.com
2. Open DevTools → Network tab
3. Try searching a flight
4. Find the API request to `services.flynorse.com`
5. Copy the Authorization header (the JWT token)
6. Update `norse_scraper.py` line ~61 with new token:
   ```python
   return "YOUR-NEW-TOKEN-HERE"
   ```
7. Commit and push the change
8. Workflow will use the new token on next run

**Manually refresh token:**
```bash
python norse_scraper.py  # Test locally with new token
git add norse_scraper.py
git commit -m "Update API token"
git push
```

---

## URLs to Share

After deployment, share this URL with others:
```
https://your-site-name.netlify.app
```

They can immediately start searching for deals across all routes!

---

## Features

✅ Multi-route flight search (Europe → US/Asia)
✅ Price-per-kilometer filtering
✅ Sale fare highlighting (🔥)
✅ Passenger type pricing (1 Adult, Adult+Child, etc.)
✅ Interactive map with booking links
✅ Automatic daily updates
✅ 100% Free hosting

---

## Support

If you encounter issues:
1. Check GitHub Actions logs
2. Verify your token is up-to-date
3. Check Netlify/Vercel deployment logs
4. Ensure `flights.json` is in the repo

