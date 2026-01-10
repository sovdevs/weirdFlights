# Weird Flights ✈️

Budget-first flight search for flexible travelers. Displays the cheapest routes across Europe → US/Asia on an interactive map, updated daily.

## Features

✨ **What it does:**
- Interactive Leaflet map showing flight routes
- Real-time filtering: region, price, price-per-km
- Sale fare highlighting 🔥
- Flexible passenger pricing (1 Adult, Adult+Child, 2 Adults, etc.)
- Booking links direct to airlines
- Automatic daily data updates

## Architecture

```
┌──────────────────────────────────────────────────┐
│         FRONTEND (Static - No Server)            │
│  - Interactive Leaflet map                       │
│  - Loads flight data from flights.json           │
│  - Region/budget/price-per-km filters            │
│  - Hosted on Netlify/Vercel/GitHub Pages        │
└──────────────────────────────────────────────────┘
                          ↑
                    flights.json
                          ↑
┌──────────────────────────────────────────────────┐
│     GITHUB ACTIONS (Daily Automation)            │
│  - Runs norse_scraper.py daily at 2 AM UTC      │
│  - Queries Norse Atlantic Airways API            │
│  - Commits updated flights.json to repo          │
│  - Hosting auto-redeploys with new data         │
└──────────────────────────────────────────────────┘
```

## 🚀 Deploy in 5 Minutes

See [DEPLOY.md](DEPLOY.md) for complete instructions.

**Quick version:**

```bash
./deploy.sh
```

This script will:
1. Initialize git repository
2. Guide you through pushing to GitHub
3. Provide one-click Netlify deployment link
4. Enable daily automated scraping via GitHub Actions

Your site will be live at: `https://your-site.netlify.app`

## 🏃 Local Development

### Quick Start

1. **Install dependencies**
   ```bash
   pip install requests
   ```

2. **Run the scraper**
   ```bash
   python norse_scraper.py
   ```
   This generates `flights.json` with data for all routes

3. **Start local server**
   ```bash
   python -m http.server 3000
   ```

4. **Open browser**
   Visit: http://localhost:3000

## Norse Atlantic API

The scraper uses Norse's internal low fare API:

```bash
POST https://services.flynorse.com/api/v1/availability/lowfare?includePremium=false

{
  "criteria": [{
    "origin": "LGW",
    "destination": "BKK",
    "beginDate": "2026-01-01",
    "endDate": "2026-01-31"
  }],
  "passengers": [{"type": "ADT", "count": 1}],
  "currencyCode": "GBP"
}
```

The bearer token appears to be a static anonymous token. If it expires, you may need to:
1. Visit flynorse.com
2. Open DevTools → Network
3. Search for a flight
4. Copy the new token from the Authorization header

## Known Norse Routes

Europe → US:
- LGW → JFK, LAX, MIA, OAK
- OSL → JFK, LAX, MIA, FLL  
- BER → JFK, LAX, MIA

Europe → Asia:
- LGW → BKK
- OSL → BKK

## Adding New Airlines

1. Create a new scraper in `scrapers/`
2. Implement the same `Flight` dataclass output
3. Add to the scheduled scrape job

Planned airlines:
- [ ] Play (Iceland)
- [ ] Condor
- [ ] French Bee
- [ ] Scoot
- [ ] AirAsia X
- [ ] Cebu Pacific

## Project Structure

```
weird-flights/
├── backend/
│   ├── server.py      # FastAPI application
│   ├── database.py    # SQLite models & queries
│   └── weird_flights.db
├── frontend/
│   └── index.html     # Leaflet map UI
├── scrapers/
│   ├── norse_scraper.py
│   └── parse_response.py
├── requirements.txt
└── README.md
```

## Development Notes

- **Token expiry**: The Norse API token may expire. Monitor for 401 errors.
- **Rate limiting**: The scraper adds delays between requests. Don't hammer their API.
- **Response format**: Check `norse_response_sample.json` if parsing breaks.
- **Database**: SQLite for now. Easy to migrate to Postgres for production.

## License

MIT
