"""
Weird Flights API Server
FastAPI backend serving flight data to the frontend map
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
from datetime import datetime
import os

from database import (
    get_db, get_flights, get_routes, get_cheapest_by_route,
    AIRPORTS, init_db, DATABASE_PATH
)

# Initialize database on startup
if not os.path.exists(DATABASE_PATH):
    init_db()

app = FastAPI(
    title="Weird Flights API",
    description="Budget-first flight search for flexible travelers",
    version="0.1.0"
)

# CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "Weird Flights API",
        "version": "0.1.0",
        "endpoints": [
            "/api/flights",
            "/api/routes",
            "/api/airports",
            "/api/cheapest",
        ]
    }


@app.get("/api/flights")
def api_flights(
    origin: Optional[str] = Query(None, description="Origin airport code"),
    destination: Optional[str] = Query(None, description="Destination airport code"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get flights sorted by price (cheapest first).
    
    Filter by origin/destination airports, max price, and date range.
    """
    with get_db() as conn:
        flights = get_flights(
            conn,
            origin=origin.upper() if origin else None,
            destination=destination.upper() if destination else None,
            max_price=max_price,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    return {
        "count": len(flights),
        "flights": flights
    }


@app.get("/api/routes")
def api_routes(
    origin_region: Optional[str] = Query(None, description="Origin region (europe, north_america, se_asia)"),
    dest_region: Optional[str] = Query(None, description="Destination region"),
    max_price: Optional[float] = Query(None, description="Maximum price")
):
    """
    Get all available routes with their lowest prices.
    
    Optionally filter by region to find e.g. all "Europe -> SE Asia" routes.
    """
    with get_db() as conn:
        routes = get_routes(
            conn,
            origin_region=origin_region,
            dest_region=dest_region,
            max_price=max_price
        )
    
    return {
        "count": len(routes),
        "routes": routes
    }


@app.get("/api/cheapest")
def api_cheapest(limit: int = Query(20, ge=1, le=100)):
    """
    Get the cheapest routes overall, sorted by price.
    
    Perfect for "show me the cheapest flights anywhere" queries.
    """
    with get_db() as conn:
        routes = get_cheapest_by_route(conn, limit=limit)
    
    return {
        "count": len(routes),
        "routes": routes
    }


@app.get("/api/airports")
def api_airports(region: Optional[str] = Query(None)):
    """
    Get all known airports with coordinates.
    
    Optionally filter by region.
    """
    airports = []
    for code, info in AIRPORTS.items():
        if region and info.get("region") != region:
            continue
        airports.append({
            "code": code,
            "name": info["name"],
            "lat": info["lat"],
            "lon": info["lon"],
            "region": info["region"]
        })
    
    return {
        "count": len(airports),
        "airports": airports
    }


@app.get("/api/regions")
def api_regions():
    """List available regions"""
    regions = set(info["region"] for info in AIRPORTS.values())
    return {
        "regions": sorted(regions)
    }


@app.get("/api/stats")
def api_stats():
    """Get database statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM flights")
        flight_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM routes")
        route_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM flights")
        price_stats = cursor.fetchone()
        
        cursor.execute("SELECT MAX(scraped_at) FROM flights")
        last_update = cursor.fetchone()[0]
    
    return {
        "total_flights": flight_count,
        "total_routes": route_count,
        "price_range": {
            "min": price_stats[0],
            "max": price_stats[1],
            "avg": round(price_stats[2], 2) if price_stats[2] else None
        },
        "last_updated": last_update,
        "airports_known": len(AIRPORTS)
    }


# Serve frontend static files if they exist
FRONTEND_DIR = "../frontend/dist"
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    
    @app.get("/app")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
