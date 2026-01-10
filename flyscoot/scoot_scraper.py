"""
Scoot Airways Scraper
Scrapes low fare availability from scoot.com via their internal API
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
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
    price_usd: float = None
    price_eur: float = None
    price_gbp: float = None


class ScootScraper:
    BASE_URL = "https://booking.flyscoot.com/api/flights"
    BOOKING_URL = "https://booking.flyscoot.com"

    # Exchange rates: SGD to other currencies (update as needed)
    EXCHANGE_RATES = {
        "SGD": 1.0,
        "USD": 0.75,  # 1 SGD = ~0.75 USD
        "EUR": 0.68,  # 1 SGD = ~0.68 EUR
        "GBP": 0.57,  # 1 SGD = ~0.57 GBP
    }

    # SE Asia regional routes (Scoot is a regional carrier, not long-haul)
    ROUTES = [
        # Singapore (main hub) <-> Regional SE Asia
        ("SIN", "BKK"), ("BKK", "SIN"),
        ("SIN", "KUL"), ("KUL", "SIN"),
        ("SIN", "CGK"), ("CGK", "SIN"),
        ("SIN", "DPS"), ("DPS", "SIN"),
        ("SIN", "HAN"), ("HAN", "SIN"),
        ("SIN", "SGN"), ("SGN", "SIN"),
        # Bangkok <-> Regional
        ("BKK", "KUL"), ("KUL", "BKK"),
        ("BKK", "CGK"), ("CGK", "BKK"),
        ("BKK", "DPS"), ("DPS", "BKK"),
        ("BKK", "HAN"), ("HAN", "BKK"),
        # Kuala Lumpur <-> Regional
        ("KUL", "CGK"), ("CGK", "KUL"),
        ("KUL", "DPS"), ("DPS", "KUL"),
        ("KUL", "HAN"), ("HAN", "KUL"),
        # Jakarta <-> Regional
        ("CGK", "DPS"), ("DPS", "CGK"),
        ("CGK", "HAN"), ("HAN", "CGK"),
        # Denpasar <-> Regional
        ("DPS", "HAN"), ("HAN", "DPS"),
    ]

    def __init__(self):
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Configure session with required headers"""
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://booking.flyscoot.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Safari/605.1.15",
        })

    def convert_price(self, price: float, from_currency: str = "SGD") -> dict:
        """
        Convert a price from one currency to multiple currencies.

        Returns dict with converted prices for USD, EUR, GBP
        """
        if from_currency not in self.EXCHANGE_RATES:
            from_currency = "SGD"

        # Convert to base (SGD)
        base_price = price / self.EXCHANGE_RATES[from_currency]

        return {
            "price_usd": round(base_price * self.EXCHANGE_RATES["USD"], 2),
            "price_eur": round(base_price * self.EXCHANGE_RATES["EUR"], 2),
            "price_gbp": round(base_price * self.EXCHANGE_RATES["GBP"], 2),
        }

    def _get_token(self) -> str:
        """
        Get authentication token.
        Scoot uses a JWT token that may expire.
        If it expires, fetch fresh from scoot booking page (DevTools → Network → Authorization header).
        """
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlYjg1NjhhOC03YzY4LTRlZGEtYjAyYy00ZjgyMDI4Y2U0ZDQiLCJpYXQiOjE3NjgwNDI3MzksInRrbiI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUp6ZFdJaU9pSlZibXR1YjNkdUlpd2lhblJwSWpvaVlqZG1NRFpqWmpndE1qVXdZaTFqTXpaakxUZGhNR1V0TlROaU1qazRNREpsWVRaaElpd2lhWE56SWpvaVpHOTBVa1ZhSUVGUVNTSjkuVXFtX0pyMXpqVGo3OFhxUGJRZmJwaHFLdTBCby00UEt0bVNkQTAyZFA5byIsImlzcyI6InNjb290LWNtdyIsImF1ZCI6InNjb290LWFwcCJ9.UtjtSIPtwK817b8RaqB0HgDeUmUvrZFl8wlE82u46lQ"

    def search_lowfare(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        currency: str = "SGD",
        adult: int = 1,
        days_forward: int = 7,
        days_backward: int = 7
    ) -> dict:
        """
        Search for low fares around a specific date.

        Args:
            origin: Origin airport code (e.g., "SIN")
            destination: Destination airport code (e.g., "BKK")
            departure_date: Central departure date in YYYY-MM-DD format
            currency: Currency code (default SGD)
            adult: Number of adult passengers
            days_forward: Days ahead to search
            days_backward: Days before to search

        Returns:
            Raw API response dict
        """
        url = f"{self.BASE_URL}/lowfare"

        payload = {
            "currencyCode": currency,
            "promoCode": "",
            "daysForward": days_forward,
            "daysBackward": days_backward,
            "flightFare": {
                "fareType": [],
                "productClass": []
            },
            "flightCriteria": [
                {
                    "origin": origin,
                    "destination": destination,
                    "departureDate": departure_date
                }
            ],
            "passengerCriteria": {
                "adult": adult,
                "child": 0,
                "infant": 0
            }
        }

        headers = {
            "Authorization": self._get_token()
        }

        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

    def parse_lowfare_response(self, response: dict, origin: str, destination: str, currency: str = "SGD") -> list:
        """
        Parse the low fare API response into Flight objects.

        Response structure:
        {
          "currencyCode": "SGD",
          "lowFareSearchMarkets": [
            {
              "origin": "SIN",
              "destination": "BKK",
              "lowFares": [
                {
                  "totalAmount": 45.50,
                  "departureDate": "2026-01-13T00:00:00",
                  "available": 2,
                  "noFlights": false,
                  "soldOut": false
                },
                ...
              ]
            }
          ]
        }
        """
        flights = []
        scraped_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        try:
            # Parse from lowFareSearchMarkets
            markets = response.get("lowFareSearchMarkets", [])

            if not isinstance(markets, list):
                return flights

            for market in markets:
                if not isinstance(market, dict):
                    continue

                # Get fares for this market
                low_fares = market.get("lowFares", [])

                for fare in low_fares:
                    # Skip if no price or not available
                    total_amount = fare.get("totalAmount")
                    if total_amount is None:
                        continue

                    # Skip if no flights or sold out
                    if fare.get("noFlights", False) or fare.get("soldOut", False):
                        continue

                    departure_date = fare.get("departureDate", "")
                    if not departure_date:
                        continue

                    # Format departure date (remove timestamp)
                    if "T" in departure_date:
                        departure_date = departure_date.split("T")[0]

                    # Build booking URL
                    booking_url = (
                        f"{self.BOOKING_URL}?origin={origin}&destination={destination}"
                        f"&departure={departure_date}"
                    )

                    # Convert price to other currencies
                    try:
                        converted_prices = self.convert_price(float(total_amount), currency)
                    except Exception as e:
                        print(f"    Currency conversion error: {e}")
                        converted_prices = {"price_usd": None, "price_eur": None, "price_gbp": None}

                    flights.append(Flight(
                        airline="scoot",
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        price=float(total_amount),
                        currency=currency,
                        scraped_at=scraped_at,
                        booking_url=booking_url,
                        is_sale_fare=False,  # Scoot response doesn't indicate sale status
                        price_usd=converted_prices.get("price_usd"),
                        price_eur=converted_prices.get("price_eur"),
                        price_gbp=converted_prices.get("price_gbp")
                    ))

        except Exception as e:
            print(f"Error parsing response: {e}")

        return flights

    def scrape_route(
        self,
        origin: str,
        destination: str,
        months_ahead: int = 6,
        currency: str = "SGD"
    ) -> list:
        """
        Scrape all available flights for a route over the next N months.
        Uses one API call per month with daysForward/daysBackward to search around key dates.
        """
        all_flights = []
        today = datetime.now()

        # Search by month - one API call per month
        for month_offset in range(months_ahead):
            year = today.year + (today.month + month_offset - 1) // 12
            month = (today.month + month_offset - 1) % 12 + 1

            # Search around the 15th of each month (middle of month for broader coverage)
            search_date = datetime(year, month, 15)

            # Skip past dates in current month
            if month_offset == 0 and today.day > 15:
                search_date = today

            print(f"  {search_date.strftime('%Y-%m-%d')}", end=" ")

            try:
                response = self.search_lowfare(
                    origin=origin,
                    destination=destination,
                    departure_date=search_date.strftime("%Y-%m-%d"),
                    currency=currency,
                    days_forward=7,
                    days_backward=7
                )

                flights = self.parse_lowfare_response(response, origin, destination, currency)
                all_flights.extend(flights)

                print(f"→ {len(flights)} flights")

                # Rate limit
                time.sleep(0.5)

            except requests.exceptions.HTTPError as e:
                print(f"→ HTTP Error: {e}")
            except Exception as e:
                print(f"→ Error: {e}")

        return all_flights

    def scrape_all_routes(self, months_ahead: int = 6, currency: str = "SGD") -> list:
        """Scrape all known routes"""
        all_flights = []

        for origin, destination in self.ROUTES:
            print(f"\n{origin} → {destination}")
            flights = self.scrape_route(origin, destination, months_ahead, currency)
            all_flights.extend(flights)
            time.sleep(1)

        return all_flights


def main():
    """Scrape all Scoot routes for the next 6 months"""
    scraper = ScootScraper()

    print("=" * 60)
    print("Scoot Airways Scraper - All Routes")
    print("=" * 60)

    months = 6

    print(f"\nScraping all routes for next {months} months...\n")

    flights = scraper.scrape_all_routes(months_ahead=months, currency="SGD")

    if flights:
        print(f"\n{'=' * 60}")
        print(f"✓ Found {len(flights)} total flights with availability")

        # Count sale fares
        sale_fares = [f for f in flights if f.is_sale_fare]
        print(f"✓ Sale fares: {len(sale_fares)}")

        prices = [f.price for f in flights]
        print(f"\nPrice statistics:")
        print(f"  Cheapest: SGD {min(prices):.0f}")
        print(f"  Most expensive: SGD {max(prices):.0f}")
        print(f"  Average: SGD {sum(prices) / len(prices):.0f}")

        # Save to dated file and current flights.json
        today = datetime.now().strftime("%Y-%m-%d")
        dated_filename = f"scoot_flights_{today}.json"
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
