import os
import json
from typing import List, Dict, Any, Optional
import math

# Optional scikit-learn import for TF-IDF and cosine similarity
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

PROCESSED_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "destinations_processed.json")

def load_processed_destinations() -> List[Dict[str, Any]]:
    if os.path.exists(PROCESSED_DATA_PATH):
        try:
            with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def get_interest_keywords(interests: List[str]) -> List[str]:
    keywords = []
    mapping = {
        "heritage": ["heritage", "history", "monument", "palace", "fort", "temple", "architecture", "ancient"],
        "history": ["heritage", "history", "monument", "palace", "fort", "temple", "architecture", "ancient"],
        "beaches": ["beach", "coastal", "sea", "ocean", "shore", "sand", "watersports"],
        "coastal": ["beach", "coastal", "sea", "ocean", "shore", "sand", "watersports"],
        "mountains": ["mountain", "hill", "trek", "trekking", "peak", "valley", "altitude"],
        "trekking": ["mountain", "hill", "trek", "trekking", "peak", "valley", "altitude"],
        "wildlife": ["wildlife", "nature", "sanctuary", "park", "forest", "safari", "animal", "flora"],
        "nature": ["wildlife", "nature", "sanctuary", "park", "forest", "safari", "animal", "flora"],
        "spiritual": ["spiritual", "temple", "ashram", "wellness", "yoga", "meditation", "sacred", "holy"],
        "wellness": ["spiritual", "temple", "ashram", "wellness", "yoga", "meditation", "sacred", "holy"],
        "culinary": ["food", "culinary", "cuisine", "taste", "eat", "market", "spice"],
        "food": ["food", "culinary", "cuisine", "taste", "eat", "market", "spice"],
        "adventure": ["adventure", "sports", "trekking", "rafting", "safari", "thrill"]
    }
    for interest in interests:
        interest_lower = interest.lower()
        matched = False
        for key, words in mapping.items():
            if key in interest_lower:
                keywords.extend(words)
                matched = True
        if not matched:
            keywords.extend([w.lower() for w in interest.split() if len(w) > 2])
    return list(set(keywords))

def recommend_attractions(
    destination: str,
    interests: List[str],
    origin: Optional[str] = None,
    limit: int = 5,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Content-based recommendation engine for tourist attractions.
    Uses TF-IDF & cosine similarity when scikit-learn is available, combined with
    destination matching and interest boosting.
    """
    destinations = load_processed_destinations()
    if not destinations:
        return []

    if limit < 1:
        limit = 5
    if limit > 50:
        limit = 50

    dest_query = destination.strip().lower()
    origin_query = origin.strip().lower() if origin else None

    scored_items = []

    corpus = []
    for d in destinations:
        text = f"{d.get('name', '')} {d.get('category', '')} {d.get('description', '')} {d.get('district_city', '')} {d.get('state_ut', '')}"
        corpus.append(text)

    tfidf_scores = [0.0] * len(destinations)
    if SKLEARN_AVAILABLE and len(destinations) > 0:
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)

            interest_kw_list = get_interest_keywords(interests)
            query_text = f"{destination} {' '.join(interests)} {' '.join(interest_kw_list)}"
            query_vec = vectorizer.transform([query_text])

            sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
            for idx, sim in enumerate(sims):
                tfidf_scores[idx] = float(sim)
        except Exception:
            pass

    interest_keywords = get_interest_keywords(interests)

    for idx, d in enumerate(destinations):
        name = d.get("name", "")
        name_lower = name.lower()
        district = d.get("district_city", "").lower()
        state = d.get("state_ut", "").lower()
        category = d.get("category", "").lower()
        description = d.get("description", "").lower()

        # 1. Destination Matching Score
        dest_match = 0.0
        if dest_query in district or dest_query in state or dest_query in name_lower or dest_query in description:
            dest_match = 1.0
        elif any(part in district or part in state or part in name_lower for part in dest_query.split() if len(part) > 2):
            dest_match = 0.6
        else:
            dest_match = 0.0

        if dest_match == 0.0:
            continue

        # 2. Origin exclusion check: Do not recommend the origin as an attraction
        if origin_query and (origin_query == district or origin_query == state or origin_query == name_lower or name_lower in origin_query):
            continue

        # 3. Interest & Category Match Score
        interest_match = 0.0
        matched_reasons = []

        if not interests:
            interest_match = 0.5
            matched_reasons.append(f"General attraction in {d.get('district_city', state)} ({d.get('category', 'General')})")
        else:
            hit_count = 0
            for kw in interest_keywords:
                if kw in description or kw in category or kw in name_lower or kw in district:
                    hit_count += 1

            if hit_count > 0:
                interest_match = min(1.0, 0.4 + (hit_count * 0.2))
                matched_reasons.append(f"Matches your interest keywords in category '{d.get('category', '')}'")
            else:
                interest_match = 0.2
                matched_reasons.append(f"Popular location in {d.get('district_city', state)}")

        for interest in interests:
            interest_clean = interest.lower()
            if any(term in category for term in interest_clean.split() if len(term) > 3):
                interest_match = min(1.0, interest_match + 0.3)
                matched_reasons.append(f"Directly aligns with interest '{interest}'")

        tfidf_val = tfidf_scores[idx] if idx < len(tfidf_scores) else 0.0

        raw_score = (0.4 * dest_match) + (0.4 * interest_match) + (0.2 * min(1.0, tfidf_val * 3.0))
        final_score = round(max(0.0, min(1.0, raw_score)), 3)

        if final_score < min_score:
            continue

        reason = " — ".join(list(dict.fromkeys(matched_reasons)))
        if not reason:
            reason = f"Recommended attraction in {d.get('district_city', state)}"

        scored_items.append({
            "attraction": {
                "id": d.get("id"),
                "source": d.get("source", "Manually Curated Development Fixture"),
                "source_id": d.get("source_id", "fixture_poi"),
                "name": name,
                "category": d.get("category"),
                "latitude": d.get("latitude"),
                "longitude": d.get("longitude"),
                "state_ut": d.get("state_ut"),
                "district_city": d.get("district_city"),
                "description": d.get("description", ""),
                "license": d.get("license", "Public Domain"),
                "version_date": d.get("version_date", "2026-10-23")
            },
            "relevance_score": final_score,
            "reason": reason
        })

    scored_items.sort(key=lambda x: (x["relevance_score"], x["attraction"]["name"]), reverse=True)

    seen_ids = set()
    unique_recommendations = []
    for item in scored_items:
        att_id = item["attraction"]["id"]
        if att_id not in seen_ids:
            seen_ids.add(att_id)
            unique_recommendations.append(item)
            if len(unique_recommendations) >= limit:
                break

    return unique_recommendations
