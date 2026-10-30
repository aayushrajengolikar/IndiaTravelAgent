import urllib.request
import urllib.parse
import json
import os
from datetime import datetime

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

REGIONS = [
    {
        "name": "Goa",
        "state_ut": "Goa",
        "bbox": (14.9, 73.6, 15.8, 74.4)
    },
    {
        "name": "Delhi",
        "state_ut": "Delhi",
        "bbox": (28.4, 76.8, 28.8, 77.4)
    }
]

def fetch_region_osm(region_info):
    name = region_info["name"]
    state_ut = region_info["state_ut"]
    min_lat, min_lon, max_lat, max_lon = region_info["bbox"]

    query = f"""
    [out:json][timeout:30];
    (
      node["tourism"~"attraction|museum|viewpoint|artwork"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["tourism"~"attraction|museum|viewpoint|artwork"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["historic"~"monument|castle|ruins|fort|memorial"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["historic"~"monument|castle|ruins|fort|memorial"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out body;
    >;
    out skel qt;
    """

    print(f"Querying Overpass API for {name} (bbox: {min_lat},{min_lon},{max_lat},{max_lon})...")
    data_encoded = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data_encoded, headers={"User-Agent": "IndiaTravelAgent/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            if response.status != 200:
                print(f"Overpass API error for {name}: status {response.status}")
                return []
            body = response.read().decode("utf-8")
            data = json.loads(body)
            elements = data.get("elements", [])
            return parse_elements(elements, state_ut)
    except Exception as e:
        print(f"Network error querying Overpass API for {name}: {e}")
        return []

def parse_elements(elements, default_state):
    node_coords = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_coords[el["id"]] = (el["lat"], el["lon"])

    sourced_records = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for el in elements:
        tags = el.get("tags", {})
        if not tags or "name" not in tags:
            continue

        name = tags.get("name")
        if not name:
            continue

        el_type = el.get("type", "node")
        el_id = el.get("id")
        source_id = f"{el_type}_{el_id}"
        source_url = f"https://www.openstreetmap.org/{el_type}/{el_id}"

        lat, lon = None, None
        if el_type == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        elif el_type == "way" and "nodes" in el:
            lats = [node_coords[nid][0] for nid in el["nodes"] if nid in node_coords]
            lons = [node_coords[nid][1] for nid in el["nodes"] if nid in node_coords]
            if lats and lons:
                lat = sum(lats) / len(lats)
                lon = sum(lons) / len(lons)

        if lat is None or lon is None:
            continue

        tourism = tags.get("tourism", "")
        historic = tags.get("historic", "")

        category = "Attraction"
        if historic in ["monument", "castle", "fort", "ruins", "memorial"]:
            category = "Heritage & History"
        elif tourism == "beach":
            category = "Beaches & Coastal"
        elif tourism in ["museum", "gallery"]:
            category = "Museum & Art"
        elif tourism in ["viewpoint", "attraction"]:
            category = "Nature & Sightseeing"
        elif historic:
            category = "Heritage & History"

        district_city = tags.get("addr:city") or tags.get("addr:district") or default_state
        state_ut = tags.get("addr:state") or default_state
        description = tags.get("description") or tags.get("note") or f"Sourced OpenStreetMap tourist POI ({category}) in {district_city}, {state_ut}."

        record = {
            "source": "OpenStreetMap (Overpass API)",
            "source_id": source_id,
            "source_url": source_url,
            "name": name,
            "category": category,
            "latitude": float(lat),
            "longitude": float(lon),
            "state_ut": state_ut,
            "district_city": district_city,
            "description": description,
            "license": "Open Database License (ODbL) v1.0 © OpenStreetMap contributors",
            "version_date": today_str
        }
        sourced_records.append(record)

    return sourced_records

def main():
    all_records = []
    for region in REGIONS:
        recs = fetch_region_osm(region)
        print(f"Retrieved {len(recs)} valid records for {region['name']}")
        all_records.extend(recs)

    unique_records = {}
    for r in all_records:
        unique_records[r["source_id"]] = r

    final_records = list(unique_records.values())
    print(f"Total unique sourced records retrieved: {len(final_records)}")

    if len(final_records) > 0:
        raw_output_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osm_attractions_raw.json")
        os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)
        with open(raw_output_path, "w", encoding="utf-8") as f:
            json.dump(final_records, f, indent=2, ensure_ascii=False)
        print(f"Saved sourced raw data to {raw_output_path}")
    else:
        print("Warning: No records retrieved from Overpass API.")

if __name__ == "__main__":
    main()
