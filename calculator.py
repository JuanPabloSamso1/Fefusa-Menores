import os


def int_or_zero(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def get_pts(team):
    for key in ["Pts", "PTS", "pts"]:
        if key in team:
            return int_or_zero(team.get(key))
    return 0


def get_gf(team):
    for key in ["GF", "GF", "gf"]:
        if key in team:
            return int_or_zero(team.get(key))
    return 0


def get_gc(team):
    for key in ["GC", "GC", "gc"]:
        if key in team:
            return int_or_zero(team.get(key))
    return 0


def get_dg(team):
    for key in ["DG", "DG", "dg"]:
        if key in team:
            return int_or_zero(team.get(key))
    return 0


def combine_standings(all_data):
    """Combine standings by club within each division."""
    promotion_spots = int(os.environ.get("PROMOTION_SPOTS", 2))
    combined = {"ORO": [], "PLATA": [], "BRONCE": []}

    clubs = {"ORO": {}, "PLATA": {}, "BRONCE": {}}

    for category in ["C15", "C17", "C20"]:
        for division in ["ORO", "PLATA", "BRONCE"]:
            standings = all_data.get(category, {}).get(division, [])
            if not standings:
                continue

            for team in standings:
                normalized = team.get("normalized", "")
                if not normalized:
                    continue

                if normalized not in clubs[division]:
                    clubs[division][normalized] = {
                        "name": normalized,
                        "C15": {"pts": 0, "gf": 0, "gc": 0, "dg": 0},
                        "C17": {"pts": 0, "gf": 0, "gc": 0, "dg": 0},
                        "C20": {"pts": 0, "gf": 0, "gc": 0, "dg": 0},
                    }

                pts = get_pts(team)
                gf = get_gf(team)
                gc = get_gc(team)
                dg = get_dg(team)
                if dg == 0:
                    dg = gf - gc

                clubs[division][normalized][category] = {
                    "pts": pts,
                    "gf": gf,
                    "gc": gc,
                    "dg": dg,
                }

    for division in ["ORO", "PLATA", "BRONCE"]:
        for club_name, data in clubs[division].items():
            c15_pts = data["C15"]["pts"]
            c17_pts = data["C17"]["pts"]
            c20_pts = data["C20"]["pts"]
            total_pts = c15_pts + c17_pts + c20_pts

            c15_dg = data["C15"]["dg"]
            c17_dg = data["C17"]["dg"]
            c20_dg = data["C20"]["dg"]
            total_dg = c15_dg + c17_dg + c20_dg

            combined[division].append({
                "name": club_name,
                "pts_c15": c15_pts,
                "pts_c17": c17_pts,
                "pts_c20": c20_pts,
                "total_pts": total_pts,
                "dg_sum": total_dg,
            })

    for division in ["ORO", "PLATA", "BRONCE"]:
        combined[division].sort(key=lambda x: (-x["total_pts"], -x["dg_sum"]))
        for i, row in enumerate(combined[division], start=1):
            row["rank"] = i

            if division == "ORO":
                if i > len(combined[division]) - promotion_spots:
                    row["status"] = "descenso"
                else:
                    row["status"] = "estabilidad"
            elif division == "PLATA":
                if i <= promotion_spots:
                    row["status"] = "ascenso"
                elif i > len(combined[division]) - promotion_spots:
                    row["status"] = "descenso"
                else:
                    row["status"] = "estabilidad"
            elif division == "BRONCE":
                if i <= promotion_spots:
                    row["status"] = "ascenso"
                else:
                    row["status"] = "estabilidad"

    return combined


if __name__ == "__main__":
    from scraper import scrape_all

    all_data, errors = scrape_all()
    combined = combine_standings(all_data)

    for division in ["ORO", "PLATA", "BRONCE"]:
        print(f"\n{division}:")
        for row in combined[division][:5]:
            print(f"  {row['rank']}. {row['name']} - {row['total_pts']} pts")