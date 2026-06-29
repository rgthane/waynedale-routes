# Waynedale Routes

A lightweight, voice-capable route lookup app for USPS mail carriers covering Fort Wayne, Indiana zip codes **46809** and **46819**.

Built to run on a Raspberry Pi or any small computer with a browser — no internet required after setup.

---

## What It Does

Given a street address, it tells you which carrier route delivers it — instantly, as you type or speak.

**Address lookup:** Type or say a number, street name, and optionally even/odd. Results narrow in real time. When only one route matches, it displays big and bold on screen.

**Carrier reverse lookup:** Type a carrier code (e.g. `C087`) to see every street on that route listed alphabetically.

---

## Search Syntax

| What you type | What it means |
|---|---|
| `7800 anoka` | Address 7800 on Anoka Dr |
| `anoka 7800` | Same — order doesn't matter |
| `78 anoka` | Shorthand: 78 = 7800 block |
| `43 A` | 4300 block, streets starting with A |
| `43 arrow e` | 4300 block, Arrow Dr, even side |
| `de forest 4301` | Auto-detects odd, shows C086 |
| `glastonbury` | Any address → Route 98 |
| `C087` | Lists all streets on C087 |
| `C86` | Same as C086 (leading zero optional) |
| `C08` | All streets across C080–C089 |
| `R008` | All streets on rural route R008 |

**Even/Odd:** Use `E` or `even` / `O` or `odd`. For exact addresses (4-digit numbers), even/odd is detected automatically.

**Directions:** Use `north`, `south`, `east`, `west` (or `N`, `S`, `W`) when a street has directional variants (e.g. `N cedar crest`).

**Voice:** Hold the 🎤 button, speak your query, release. Works in Chromium/Chrome with a microphone.

---

## Data

Route data is stored in SQLite (`data/routes.db`) loaded from two CSV source files:

| File | Zip | Entries |
|---|---|---|
| `data/carrier_routes_46809_extracted.csv` | 46809 | 247 |
| `data/carrier_routes_46819_extracted.cvs.csv` | 46819 | 198 |

Original source data (Apple Numbers spreadsheets) is in `data/untitled folder/`.

Route images (photos of the original printed route sheets) are in `Route images/`.

### CSV Format

```
street_name, range_start, range_end, even_odd, carrier_number
ANOKA DR, 7700, 8099, , R008
DE FOREST AVE, 4300, 4398, E, C087
DE FOREST AVE, 4301, 4399, O, C086
```

- `even_odd` is `E` (even addresses only), `O` (odd addresses only), or blank (both)
- `carrier_number` is formatted as `C###` (city route) or `R###` (rural route)
- Streets with multiple address ranges appear as multiple rows
- Route `98` (Glastonbury) is hardcoded in `setup_db.py` — all addresses on Glastonbury go to Route 98

---

## Setup

### Requirements

- Python 3.7+
- Flask (`pip3 install flask`)

### Install & Run

```bash
git clone https://github.com/rgthane/waynedale-routes.git
cd waynedale-routes

pip3 install -r requirements.txt

# Build the database from the CSV source files
python3 setup_db.py

# Start the app
python3 app.py
```

Then open **http://localhost:5000** in a browser.

The server runs on `0.0.0.0:5000` so it's accessible from any device on the same network (useful if the Pi is headless and you browse from a phone or tablet).

### Rebuilding the Database

If you update either CSV file, re-run:

```bash
python3 setup_db.py
```

This wipes and reloads `data/routes.db` from both CSVs plus the Glastonbury special case.

---

## Raspberry Pi Deployment

### Auto-start on boot

Create `/etc/systemd/system/waynedale.service`:

```ini
[Unit]
Description=Waynedale Routes
After=network.target

[Service]
WorkingDirectory=/home/pi/waynedale-routes
ExecStart=/usr/bin/python3 app.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Then enable it:

```bash
sudo systemctl enable waynedale
sudo systemctl start waynedale
```

### Kiosk mode (full-screen browser on boot)

Add to `/etc/xdg/lxsession/LXDE-pi/autostart`:

```
@chromium-browser --kiosk --app=http://localhost:5000
```

### Voice input

Voice uses the **Web Speech API** built into Chromium — no extra libraries needed, just a USB or built-in microphone. Hold the 🎤 button and speak; release when done.

---

## Project Structure

```
waynedale-routes/
├── app.py                  # Flask app — search API + server
├── setup_db.py             # Loads CSVs into SQLite
├── requirements.txt        # Python dependencies (just Flask)
├── templates/
│   └── index.html          # Single-page UI with voice input
├── data/
│   ├── routes.db                              # SQLite database (built by setup_db.py)
│   ├── carrier_routes_46809_extracted.csv     # Source data — zip 46809
│   ├── carrier_routes_46819_extracted.cvs.csv # Source data — zip 46819
│   └── untitled folder/                       # Original Numbers spreadsheets
└── Route images/                              # Photos of original printed route sheets
```
