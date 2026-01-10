#!/usr/bin/env python3
"""
Daily scraper automation script
Runs all flight scrapers and merges results into a single flights.json
Designed to run once per day via cron or GitHub Actions
"""

import subprocess
import sys
import os
from datetime import datetime


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Main daily scrape workflow"""
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "DAILY FLIGHT SCRAPER" + " "*23 + "║")
    print("╚" + "="*58 + "╝")

    start_time = datetime.now()
    print(f"\n⏰ Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Track results
    results = {}

    # Step 1: Run Scoot scraper
    results['scoot'] = run_command(
        "python flyscoot/scoot_scraper.py",
        "Scoot Airways Scraper"
    )

    # Step 2: Run Norse scraper
    results['norse'] = run_command(
        "python flynorse/norse_scraper.py",
        "Norse Atlantic Scraper"
    )

    # Step 3: Merge all flight data
    results['merge'] = run_command(
        "python merge_flights.py",
        "Merge Flight Data"
    )

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for scraper, success in results.items():
        status = "✓ SUCCESS" if success else "❌ FAILED"
        print(f"{scraper.upper():15} {status}")

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print(f"\n⏱ Completed in {elapsed:.1f} seconds")
    print(f"🕐 Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Exit with appropriate code
    if all(results.values()):
        print("✅ All scrapers completed successfully!")
        return 0
    else:
        print("⚠ Some scrapers failed - check logs above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
