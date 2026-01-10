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
    is_sale_fare: bool = False


class NorseScraper:
    BASE_URL = "https://services.flynorse.com/api/v1"
    BOOKING_URL = "https://flynorse.com/en-GB/booking/select"
    
    # Known Norse routes - bidirectional
    ROUTES = [
        # Europe <-> US
        # LGW routes
        ("LGW", "JFK"), ("JFK", "LGW"),
        ("LGW", "LAX"), ("LAX", "LGW"),
        ("LGW", "MIA"), ("MIA", "LGW"),
        ("LGW", "OAK"), ("OAK", "LGW"),
        # OSL routes
        ("OSL", "JFK"), ("JFK", "OSL"),
        ("OSL", "LAX"), ("LAX", "OSL"),
        ("OSL", "MIA"), ("MIA", "OSL"),
        ("OSL", "FLL"), ("FLL", "OSL"),
        # BER routes
        ("BER", "JFK"), ("JFK", "BER"),
        ("BER", "LAX"), ("LAX", "BER"),
        ("BER", "MIA"), ("MIA", "BER"),
        # Europe <-> Asia
        ("LGW", "BKK"), ("BKK", "LGW"),
        ("OSL", "BKK"), ("BKK", "OSL"),
        ("MAN", "BKK"), ("BKK", "MAN"),
    ]
    
    def __init__(self):
        self.session = requests.Session()
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
        This is the anonymous token from dotREZ API.
        Tokens can expire - update this if you get 403/440 errors.
        To get a fresh token: check the Authorization header in your browser's Network tab on flynorse.com
        """
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJVbmtub3duIiwianRpIjoiMjAwMDM0NzEtNjYyZS01ZGExLTQwMzgtODgyNjcxNjViODNjIiwiaXNzIjoiZG90UkVaIEFQSSJ9.rDLjdM3YtAbzI4IFDCV4ZdCT8fSzmx0v9kS8fsEbUEU"
    
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
    
    def parse_lowfare_response(self, response: dict, currency: str = "GBP") -> list[Flight]:
        """
        Parse the low fare API response into Flight objects.
        
        Response structure:
        {
          "data": [
            {
              "cityPair": {"origin": "LGW", "destination": "BKK"},
              "cabins": [
                {
                  "cabinName": "Economy",
                  "lowFareAmounts": [
                    {
                      "departureDate": "2026-01-09T00:00:00",
                      "fareTotal": 493.57,
                      "roundedFareTotal": 494,
                      ...
                    }
                  ]
                }
              ]
            }
          ]
        }
        """
        flights = []
        scraped_at = datetime.utcnow().isoformat() + "Z"
        
        data = response.get("data", [])
        
        for city_pair_data in data:
            # Extract origin/destination from cityPair
            city_pair = city_pair_data.get("cityPair", {})
            origin = city_pair.get("origin", "")
            destination = city_pair.get("destination", "")
            
            if not origin or not destination:
                continue
            
            # Iterate through cabins (usually just Economy, but could have Premium)
            for cabin in city_pair_data.get("cabins", []):
                cabin_name = cabin.get("cabinName", "Economy")
                
                # Parse each fare date
                for fare in cabin.get("lowFareAmounts", []):
                    # Skip if no fare available (fareTotal is null)
                    fare_total = fare.get("fareTotal")
                    if fare_total is None:
                        continue
                    
                    # Use roundedFareTotal if available, otherwise fareTotal
                    price = fare.get("roundedFareTotal") or fare_total
                    
                    # Parse departure date (format: "2026-01-09T00:00:00")
                    departure_date = fare.get("departureDate", "")[:10]  # Get YYYY-MM-DD
                    
                    if not departure_date:
                        continue
                    
                    # Build booking URL
                    booking_url = (
                        f"{self.BOOKING_URL}?"
                        f"origin={origin}&destination={destination}"
                        f"&date={departure_date}&cabin={cabin_name}"
                    )

                    # Check if this is a sale fare
                    is_sale = fare.get("isSaleFare", False)

                    flights.append(Flight(
                        airline="norse",
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        price=float(price),
                        currency=currency,
                        scraped_at=scraped_at,
                        booking_url=booking_url,
                        is_sale_fare=is_sale
                    ))
        
        return flights
    
    def scrape_route(
        self,
        origin: str,
        destination: str,
        months_ahead: int = 6,
        currency: str = "GBP"
    ) -> list[Flight]:
        """
        Scrape all available flights for a route over the next N months.
        """
        all_flights = []
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
            
            # Skip past dates in current month
            if month_offset == 0:
                start_date = max(start_date, today)
            
            print(f"  {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", end=" ")
            
            try:
                response = self.search_lowfare(
                    origin=origin,
                    destination=destination,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    currency=currency
                )
                
                flights = self.parse_lowfare_response(response, currency)
                all_flights.extend(flights)
                
                print(f"→ {len(flights)} flights")
                
                # Rate limit
                time.sleep(0.5)
                
            except requests.exceptions.HTTPError as e:
                print(f"→ HTTP Error: {e}")
            except Exception as e:
                print(f"→ Error: {e}")
        
        return all_flights
    
    def scrape_all_routes(self, months_ahead: int = 6, currency: str = "GBP") -> list[Flight]:
        """Scrape all known routes"""
        all_flights = []
        
        for origin, destination in self.ROUTES:
            print(f"\n{origin} → {destination}")
            flights = self.scrape_route(origin, destination, months_ahead, currency)
            all_flights.extend(flights)
            time.sleep(1)
        
        return all_flights


def main():
    """Scrape all routes for the next 6 months"""
    scraper = NorseScraper()

    print("=" * 60)
    print("Norse Atlantic Scraper - All Routes")
    print("=" * 60)

    months = 6

    print(f"\nScraping all routes for next {months} months...\n")

    flights = scraper.scrape_all_routes(months_ahead=months, currency="GBP")

    if flights:
        print(f"\n{'=' * 60}")
        print(f"✓ Found {len(flights)} total flights with availability")

        # Count sale fares
        sale_fares = [f for f in flights if f.is_sale_fare]
        print(f"✓ Sale fares: {len(sale_fares)}")

        prices = [f.price for f in flights]
        print(f"\nPrice statistics:")
        print(f"  Cheapest: £{min(prices):.0f}")
        print(f"  Most expensive: £{max(prices):.0f}")
        print(f"  Average: £{sum(prices) / len(prices):.0f}")

        # Save to dated file and current flights.json
        today = datetime.now().strftime("%Y-%m-%d")
        dated_filename = f"norse_flights_{today}.json"
        current_filename = "flights.json"

        flights_data = [asdict(fl) for fl in flights]

        with open(dated_filename, "w") as f:
            json.dump(flights_data, f, indent=2)
        print(f"\n✓ Saved to {dated_filename}")

        # Also save as flights.json for the frontend to use
        with open(current_filename, "w") as f:
            json.dump(flights_data, f, indent=2)
        print(f"✓ Saved to {current_filename}")
        print("=" * 60)
    else:
        print("\n⚠ No flights found")


if __name__ == "__main__":
    main()
