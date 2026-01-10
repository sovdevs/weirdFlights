# Weird Flights ✈️

Budget-first flight search for flexible travelers. Like Rome2Rio but for lesser-known airlines, sorted by price instead of date.

## Concept

Someone has a rough idea of start and end point (e.g., "Europe → SE Asia") but a fixed budget and will fly to a nearby airport if needed. This tool shows the cheapest routes on a map.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  - Interactive Leaflet map                                  │
│  - Route lines colored by price                             │
│  - Region/budget filters                                    │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  - /api/routes - all routes with lowest prices              │
│  - /api/flights - individual flights                        │
│  - /api/airports - airport coordinates                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   SQLITE DATABASE                            │
│  - flights: individual prices by date                       │
│  - routes: aggregated lowest prices                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ Populated by
┌─────────────────────▼───────────────────────────────────────┐
│                       SCRAPERS                               │
│  - Norse Atlantic (POC)                                     │
│  - More airlines to be added                                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database & Run Scraper

```bash
cd scrapers
python norse_scraper.py
```

This will:
- Test the Norse Atlantic API
- Save a sample response to `norse_response_sample.json`
- Show the response structure (needed to finalize parsing)

### 3. Import Data to Database

After scraping:

```bash
cd backend
python database.py  # Initialize with test data
```

### 4. Start the API Server

```bash
cd backend
python server.py
# or: uvicorn server:app --reload --port 8000
```

API available at: http://localhost:8000

### 5. Open the Frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
cd frontend
python -m http.server 3000
```

Then visit: http://localhost:3000

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/routes` | All routes with lowest prices |
| `GET /api/routes?origin_region=europe&dest_region=se_asia` | Filter by region |
| `GET /api/routes?max_price=500` | Filter by max price |
| `GET /api/flights?origin=LGW&destination=BKK` | Specific route flights |
| `GET /api/airports` | All airports with coordinates |
| `GET /api/cheapest` | Top 20 cheapest routes |
| `GET /api/stats` | Database statistics |

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
