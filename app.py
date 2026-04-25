import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify
from scraper import scrape_all
from calculator import combine_standings

app = Flask(__name__)

CACHE = {
    "all_data": {},
    "combined": {},
    "errors": [],
    "last_updated": None,
}


@app.route("/")
def index():
    return render_template("index.html", combined=CACHE["combined"], all_data=CACHE["all_data"], errors=CACHE["errors"], last_updated=CACHE["last_updated"])


@app.route("/refresh")
def refresh():
    all_data, errors = scrape_all()
    combined = combine_standings(all_data)

    CACHE["all_data"] = all_data
    CACHE["combined"] = combined
    CACHE["errors"] = errors
    CACHE["last_updated"] = datetime.now().isoformat()

    return jsonify({"success": True, "errors": errors, "last_updated": CACHE["last_updated"]})


@app.route("/api/standings")
def api_standings():
    return jsonify({
        "all_data": CACHE["all_data"],
        "combined": CACHE["combined"],
        "errors": CACHE["errors"],
        "last_updated": CACHE["last_updated"],
    })


def init_cache():
    all_data, errors = scrape_all()
    combined = combine_standings(all_data)
    CACHE["all_data"] = all_data
    CACHE["combined"] = combined
    CACHE["errors"] = errors
    CACHE["last_updated"] = datetime.now().isoformat()


init_cache()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)