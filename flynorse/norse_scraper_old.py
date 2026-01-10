"""
Norse Atlantic Airways Scraper
Scrapes low fare availability from flynorse.com via their internal API
"""

import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional
import time


@dataclass
class Flight:
    airline: str
    origin: str
    destination: str
    departure_date: str
    price: float
    currency: str
    scraped_at: str
    booking_url: str


class NorseScraper:
    BASE_URL = "https://services.flynorse.com/api/v1"
    BOOKING_URL = "https://flynorse.com/en-GB/booking/select"
    
    # Known Norse routes (we'll need to maintain/scrape this list)
    ROUTES = [
        # Europe -> US
        ("LGW", "JFK"), ("LGW", "LAX"), ("LGW", "MIA"), ("LGW", "OAK"),
        ("OSL", "JFK"), ("OSL", "LAX"), ("OSL", "MIA"), ("OSL", "FLL"),
        ("BER", "JFK"), ("BER", "LAX"), ("BER", "MIA"),
        # Europe -> Asia (Bangkok route)
        ("LGW", "BKK"), ("OSL", "BKK"),
        # Add more as discovered
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self._setup_session()
    
    def _setup_session(self):
        """Configure session with required headers"""
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://flynorse.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        })
    
    def _get_token(self) -> str:
        """
        Get authentication token.
        The token appears to be a static anonymous token from dotREZ API.
        If it expires, we'd need to fetch it from the main site.
        """
        # This is the anonymous token from the curl - appears to be static
        # If it stops working, we'll need to scrape it from the main page
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJVbmtub3duIiwianRpIjoiODJkNDRlYjYtZWZkNy05ZjUxLTQ1MGItNjljZTI3MjdmYzg5IiwiaXNzIjoiZG90UkVaIEFQSSJ9.Tbs7dDYe1Iv7FY0ajYLpRXKKNCaRIWB29n8ce6Wv7Ck"
    
    def search_lowfare(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        currency: str = "GBP",
        passengers: int = 1
    ) -> dict:
        """
        Search for low fares between two airports for a date range.
        
        Args:
            origin: Origin airport code (e.g., "LGW")
            destination: Destination airport code (e.g., "BKK")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            currency: Currency code (default GBP)
            passengers: Number of adult passengers
        
        Returns:
            Raw API response dict
        """
        url = f"{self.BASE_URL}/availability/lowfare?includePremium=false"
        
        payload = {
            "criteria": [
                {
                    "origin": origin,
                    "destination": destination,
                    "beginDate": start_date,
                    "endDate": end_date
                }
            ],
            "passengers": [{"type": "ADT", "count": passengers}],
            "currencyCode": currency,
            "promotionCode": "",
            "clearBooking": True,
            "childDobs": [],
            "infantDobs": []
        }
        
        headers = {
            "Authorization": f"Bearer {self._get_token()}"
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def parse_lowfare_response(self, response: dict, origin: str, destination: str) -> list[Flight]:
        """
        Parse the low fare API response into Flight objects.
        
        The response structure appears to be:
        {
            "data": {
                "lowFareAvailability": {
                    "outboundDates": [...],  # or similar structure
                }
            }
        }
        """
        flights = []
        scraped_at = datetime.utcnow().isoformat() + "Z"
        
        # Navigate the response structure
        # This will need adjustment based on actual response format
        try:
            data = response.get("data", response)
            
            # The structure might vary - let's handle common patterns
            if "lowFareAvailability" in data:
                availability = data["lowFareAvailability"]
            elif "outboundDates" in data:
                availability = data
            else:
                availability = data
            
            # Look for date/price data
            dates_data = availability.get("outboundDates", availability.get("dates", []))
            
            if isinstance(dates_data, list):
                for item in dates_data:
                    if isinstance(item, dict):
                        date = item.get("date", item.get("departureDate", ""))
                        price = item.get("price", item.get("lowestPrice", item.get("amount", 0)))
                        currency = item.get("currencyCode", "GBP")
                        
                        if date and price and price > 0:
                            flights.append(Flight(
                                airline="norse",
                                origin=origin,
                                destination=destination,
                                departure_date=date,
                                price=float(price),
                                currency=currency,
                                scraped_at=scraped_at,
                                booking_url=f"{self.BOOKING_URL}?origin={origin}&destination={destination}&date={date}"
                            ))
            
            elif isinstance(dates_data, dict):
                # Handle dict format where keys are dates
                for date, info in dates_data.items():
                    if isinstance(info, dict):
                        price = info.get("price", info.get("lowestPrice", 0))
                    else:
                        price = info
                    
                    if price and price > 0:
                        flights.append(Flight(
                            airline="norse",
                            origin=origin,
                            destination=destination,
                            departure_date=date,
                            price=float(price),
                            currency="GBP",
                            scraped_at=scraped_at,
                            booking_url=f"{self.BOOKING_URL}?origin={origin}&destination={destination}&date={date}"
                        ))
                        
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response structure: {json.dumps(response, indent=2)[:1000]}")
        
        return flights
    
    def scrape_route(
        self,
        origin: str,
        destination: str,
        months_ahead: int = 3,
        currency: str = "GBP"
    ) -> list[Flight]:
        """
        Scrape all available flights for a route over the next N months.
        """
        all_flights = []
        
        # Generate month ranges
        today = datetime.now()
        
        for month_offset in range(months_ahead):
            # Calculate month start/end
            year = today.year + (today.month + month_offset - 1) // 12
            month = (today.month + month_offset - 1) % 12 + 1
            
            start_date = datetime(year, month, 1)
            
            # End of month
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            print(f"Searching {origin} -> {destination}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            try:
                response = self.search_lowfare(
                    origin=origin,
                    destination=destination,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    currency=currency
                )
                
                flights = self.parse_lowfare_response(response, origin, destination)
                all_flights.extend(flights)
                
                print(f"  Found {len(flights)} flights")
                
                # Be nice to the API
                time.sleep(0.5)
                
            except requests.exceptions.HTTPError as e:
                print(f"  HTTP Error: {e}")
            except Exception as e:
                print(f"  Error: {e}")
        
        return all_flights
    
    def scrape_all_routes(self, months_ahead: int = 3, currency: str = "GBP") -> list[Flight]:
        """Scrape all known routes"""
        all_flights = []
        
        for origin, destination in self.ROUTES:
            flights = self.scrape_route(origin, destination, months_ahead, currency)
            all_flights.extend(flights)
            time.sleep(1)  # Pause between routes
        
        return all_flights


def main():
    """Test the scraper with a single route"""
    scraper = NorseScraper()
    
    # Test single search
    print("=" * 60)
    print("Testing Norse Atlantic API")
    print("=" * 60)
    
    # Search LGW -> BKK for January 2026
    print("\nSearching LGW -> BKK for January 2026...")
    
    try:
        response = scraper.search_lowfare(
            origin="LGW",
            destination="BKK",
            start_date="2026-01-01",
            end_date="2026-01-31",
            currency="GBP"
        )
        
        # Save raw response for analysis
        with open("norse_response_sample.json", "w") as f:
            json.dump(response, f, indent=2)
        
        print(f"\n✓ API call successful!")
        print(f"  Response saved to norse_response_sample.json")
        print(f"\nResponse structure preview:")
        print(json.dumps(response, indent=2)[:2000])
        
        # Try to parse
        print("\n" + "=" * 60)
        print("Parsing response...")
        flights = scraper.parse_lowfare_response(response, "LGW", "BKK")
        
        if flights:
            print(f"\n✓ Parsed {len(flights)} flights:")
            for f in sorted(flights, key=lambda x: x.price)[:10]:
                print(f"  {f.departure_date}: £{f.price:.0f}")
        else:
            print("\n⚠ No flights parsed - check response structure above")
            
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        print("  Token may have expired - need to fetch fresh token")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
