import requests
from bs4 import BeautifulSoup
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

URLS = {
    "C20": {
        "ORO": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C20-M-ORO-A-2026/standings",
        "PLATA": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C20-M-PLATA-A-2026/standings",
        "BRONCE": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C20-M-BRONCE-A-2026/standings",
    },
    "C17": {
        "ORO": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C17-M-ORO-A-2026/standings",
        "PLATA": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C17-M-PLATA-A-2026/standings",
        "BRONCE": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C17-M-BRONCE-A-2026/standings",
    },
    "C15": {
        "ORO": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C15-M-ORO-A-2026/standings",
        "PLATA": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C15-M-PLATA-A-2026/standings",
        "BRONCE": "https://scorefy.app/futsal/mendoza/fefusa-mendoza/FFM-C15-M-BRONCE-A-2026/standings",
    },
}

TEAM_ALIASES = {
    "cooperativo fray luis": "Coop. Fray Luis",
    "coop fray luis": "Coop. Fray Luis",
    "cooperativo san martin": "Cooperativo San Martin",
    "coop san martin": "Cooperativo San Martin",
    "godoro": "Godoy Cruz",
    "godoy": "Godoy Cruz",
    "huracan": "Huracan",
    "atletico palmares": "Atlético Palmares",
    "palmares": "Atlético Palmares",
    "san martin": "San Martin",
}

ZONE_LABELS = ["Zona A", "Zona B", "Zona C", "Zona D", "Zona E", "Zona F"]


def normalize_team_name(name):
    if not name:
        return ""
    normalized = name.strip().title()
    for alias, standard in TEAM_ALIASES.items():
        if alias.lower() == normalized.lower():
            return standard
    return normalized


def _parse_int(val):
    v = val.strip().lstrip('-') if val else ""
    if v.isdigit():
        return int(val.strip())
    return 0


def _parse_table(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 10:
            continue
        first_text = cells[0].get_text(strip=True)
        if not first_text.isdigit():
            continue
        team_name = cells[2].get_text(strip=True)
        if not team_name:
            continue
        dg_raw = cells[10].get_text(strip=True) if len(cells) > 10 else "0"
        rows.append({
            "position": int(first_text),
            "Equipo": team_name,
            "Pts": _parse_int(cells[3].get_text(strip=True)),
            "PJ": _parse_int(cells[4].get_text(strip=True)),
            "PG": _parse_int(cells[5].get_text(strip=True)),
            "PE": _parse_int(cells[6].get_text(strip=True)),
            "PP": _parse_int(cells[7].get_text(strip=True)),
            "GF": _parse_int(cells[8].get_text(strip=True)),
            "GC": _parse_int(cells[9].get_text(strip=True)),
            "DG": _parse_int(dg_raw),
            "normalized": normalize_team_name(team_name),
        })
    return rows


def _get_table_heading(table):
    el = table
    for _ in range(30):
        prev = el.find_previous_sibling()
        if prev:
            el = prev
        else:
            el = el.parent
        if not el:
            break
        if el.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return el.get_text(strip=True)
    return None


def scrape_standings(url):
    """Returns list of zones: [{"name": str, "teams": [dict, ...]}]"""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        tables = soup.find_all("table")
        if not tables:
            logger.warning(f"No tables found in {url}")
            return []

        zones = []
        auto_idx = 0
        for table in tables:
            teams = _parse_table(table)
            if len(teams) < 4:
                continue
            heading = _get_table_heading(table)
            if heading:
                zone_name = heading
            else:
                zone_name = ZONE_LABELS[auto_idx] if auto_idx < len(ZONE_LABELS) else f"Zona {auto_idx + 1}"
                auto_idx += 1
            zones.append({"name": zone_name, "teams": teams})

        total = sum(len(z["teams"]) for z in zones)
        logger.info(f"Scraped {total} teams in {len(zones)} zones from {url}")
        return zones

    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing {url}: {e}")
        return []


def scrape_all():
    """Scrape all URLs and return organized data."""
    all_data = {"C20": {}, "C17": {}, "C15": {}}
    errors = []

    for category in ["C20", "C17", "C15"]:
        for division in ["ORO", "PLATA", "BRONCE"]:
            url = URLS[category][division]
            zones = scrape_standings(url)
            if zones:
                all_data[category][division] = zones
            else:
                all_data[category][division] = []
                errors.append(f"{category}-{division}")

    return all_data, errors


if __name__ == "__main__":
    all_data, errors = scrape_all()
    for category in ["C20", "C17", "C15"]:
        for division in ["ORO", "PLATA", "BRONCE"]:
            zones = all_data[category].get(division, [])
            total = sum(len(z["teams"]) for z in zones)
            print(f"  {category} {division}: {len(zones)} zonas, {total} equipos")
            for z in zones:
                sample = z["teams"][0] if z["teams"] else {}
                print(f"    {z['name']}: {len(z['teams'])} equipos | lider: {sample.get('Equipo','?')} pts={sample.get('Pts','?')}")
    if errors:
        print(f"Errors: {errors}")