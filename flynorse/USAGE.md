cd /Users/vmac/PycharmProjects/wierdFlights/flynorse
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python norse_scraper.py

## get flights for Norse Atlantic
python norse_scraper.py
# launch FE
python -m http.server 3001

cd /Users/vmac/PycharmProjects/wierdFlights/flynorse
# 1. Generate flights.json
uv run --with requests norse_scraper.py

# 2. Serve the files (needed for fetch to work)
python -m http.server 3000
