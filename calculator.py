import os


def int_or_zero(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def get_pts(team):
    return int_or_zero(team.get("Pts", 0))


def get_pj(team):
    return int_or_zero(team.get("PJ", 0))


def get_gf(team):
    return int_or_zero(team.get("GF", 0))


def get_gc(team):
    return int_or_zero(team.get("GC", 0))


def get_dg(team):
    return int_or_zero(team.get("DG", 0))


def _empty_cat():
    return {"pts": 0, "pj": 0, "gf": 0, "gc": 0, "dg": 0}


def _assign_status(division, rank, total, promotion_spots, relegation_spots):
    if division == "ORO":
        return "descenso" if rank > total - relegation_spots else "estabilidad"
    elif division == "PLATA":
        if rank <= promotion_spots:
            return "ascenso"
        elif rank > total - relegation_spots:
            return "descenso"
        return "estabilidad"
    elif division == "BRONCE":
        return "ascenso" if rank <= promotion_spots else "estabilidad"
    return "estabilidad"


def _build_zone_rows(zone_name, division, all_data, promotion_spots, relegation_spots):
    """Build combined rows for one zone across all categories."""
    clubs = {}

    for category in ["C15", "C17", "C20"]:
        zones = all_data.get(category, {}).get(division, [])
        zone_data = next((z for z in zones if z["name"] == zone_name), None)
        if not zone_data:
            continue
        for team in zone_data.get("teams", []):
            normalized = team.get("normalized", "")
            if not normalized:
                continue
            if normalized not in clubs:
                clubs[normalized] = {
                    "name": normalized,
                    "C15": _empty_cat(),
                    "C17": _empty_cat(),
                    "C20": _empty_cat(),
                }
            gf = get_gf(team)
            gc = get_gc(team)
            clubs[normalized][category] = {
                "pts": get_pts(team),
                "pj":  get_pj(team),
                "gf":  gf,
                "gc":  gc,
                "dg":  get_dg(team) or (gf - gc),
            }

    rows = []
    for club_name, data in clubs.items():
        c15, c17, c20 = data["C15"], data["C17"], data["C20"]
        total_pts = c15["pts"] + c17["pts"] + c20["pts"]
        total_pj  = c15["pj"]  + c17["pj"]  + c20["pj"]
        total_dg  = c15["dg"]  + c17["dg"]  + c20["dg"]
        rows.append({
            "name":     club_name,
            "pts_c15":  c15["pts"], "pj_c15": c15["pj"],
            "pts_c17":  c17["pts"], "pj_c17": c17["pj"],
            "pts_c20":  c20["pts"], "pj_c20": c20["pj"],
            "total_pts": total_pts,
            "total_pj":  total_pj,
            "dg_sum":    total_dg,
        })

    rows.sort(key=lambda x: (-x["total_pts"], -x["dg_sum"]))
    for i, row in enumerate(rows, 1):
        row["rank"] = i
        row["status"] = _assign_status(division, i, len(rows), promotion_spots, relegation_spots)

    return rows


def combine_standings(all_data):
    """Return combined standings grouped by zone for each division.

    Structure: {"ORO": [{"zone": "Zona A", "rows": [...]}, ...], ...}
    """
    promotion_spots = int(os.environ.get("PROMOTION_SPOTS", 1))
    relegation_spots = int(os.environ.get("RELEGATION_SPOTS", 2))
    combined = {"ORO": [], "PLATA": [], "BRONCE": []}

    for division in ["ORO", "PLATA", "BRONCE"]:
        seen = set()
        zone_names = []
        for category in ["C15", "C17", "C20"]:
            for z in all_data.get(category, {}).get(division, []):
                if z["name"] not in seen:
                    seen.add(z["name"])
                    zone_names.append(z["name"])

        for zone_name in sorted(zone_names):
            rows = _build_zone_rows(zone_name, division, all_data, promotion_spots, relegation_spots)
            combined[division].append({"zone": zone_name, "rows": rows})

    return combined


if __name__ == "__main__":
    from scraper import scrape_all

    all_data, errors = scrape_all()
    combined = combine_standings(all_data)

    for division in ["ORO", "PLATA", "BRONCE"]:
        print(f"\n{division}:")
        for zone_combined in combined[division]:
            print(f"  {zone_combined['zone']}:")
            for row in zone_combined["rows"][:3]:
                print(f"    {row['rank']}. {row['name']} - {row['total_pts']} pts ({row['total_pj']} PJ) [{row['status']}]")
