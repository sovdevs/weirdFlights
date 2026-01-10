#!/usr/bin/env python3
"""
Merge script for combining flight data from multiple scrapers
Runs after each scraper completes and merges all available flight data
into a single flights.json file for the frontend
"""

import json
import glob
from datetime import datetime
from pathlib import Path


def find_latest_file(pattern: str) -> str:
    """Find the most recently modified file matching a glob pattern"""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=lambda f: Path(f).stat().st_mtime)


def load_json_file(filepath: str) -> list:
    """Load and parse a JSON file, return empty list if not found"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ⚠ Error reading {filepath}: {e}")
        return []


def merge_flights(scoot_file: str = None, norse_file: str = None) -> list:
    """
    Merge flight data from Scoot and Norse scrapers

    Args:
        scoot_file: Path to Scoot flights JSON (if None, finds latest)
        norse_file: Path to Norse flights JSON (if None, finds latest)

    Returns:
        List of merged flight dictionaries
    """
    all_flights = []

    print("🔄 Merging flight data from multiple scrapers...\n")

    # Find latest Scoot flights
    if not scoot_file:
        scoot_file = find_latest_file("scoot_flights_*.json")

    if scoot_file:
        scoot_flights = load_json_file(scoot_file)
        print(f"✓ Loaded {len(scoot_flights)} Scoot flights from {Path(scoot_file).name}")
        all_flights.extend(scoot_flights)
    else:
        print("⚠ No Scoot flights file found")

    # Find latest Norse flights
    if not norse_file:
        norse_file = find_latest_file("flynorse/norse_flights_*.json")

    if norse_file:
        norse_flights = load_json_file(norse_file)
        print(f"✓ Loaded {len(norse_flights)} Norse flights from {Path(norse_file).name}")
        all_flights.extend(norse_flights)
    else:
        print("⚠ No Norse flights file found")

    print(f"\n📊 Total flights merged: {len(all_flights)}")

    # Count by airline
    airline_counts = {}
    for flight in all_flights:
        airline = flight.get('airline', 'unknown')
        airline_counts[airline] = airline_counts.get(airline, 0) + 1

    for airline, count in sorted(airline_counts.items()):
        print(f"   • {airline.upper()}: {count} flights")

    return all_flights


def save_merged_flights(flights: list, output_files: list = None) -> bool:
    """Save merged flights to JSON files

    Args:
        flights: List of flight dictionaries to save
        output_files: List of file paths to save to (default: root + flynorse)
    """
    if output_files is None:
        output_files = ["flights.json", "flynorse/flights.json"]

    all_success = True
    for output_file in output_files:
        try:
            with open(output_file, 'w') as f:
                json.dump(flights, f, indent=2)
            file_size = Path(output_file).stat().st_size / (1024 * 1024)
            print(f"✅ Saved {len(flights)} flights to {output_file} ({file_size:.1f} MB)")
        except Exception as e:
            print(f"❌ Error saving to {output_file}: {e}")
            all_success = False

    return all_success


def main():
    """Main merge workflow"""
    print("=" * 60)
    print("Flight Data Merger")
    print("=" * 60 + "\n")

    # Merge flights from all sources
    merged_flights = merge_flights()

    if not merged_flights:
        print("\n⚠ No flights to merge")
        return False

    # Save merged data
    success = save_merged_flights(merged_flights)

    if success:
        print("\n" + "=" * 60)
        print("✓ Merge complete - flights.json is ready for frontend")
        print("=" * 60)

    return success


if __name__ == "__main__":
    main()
