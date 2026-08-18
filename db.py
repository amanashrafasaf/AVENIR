"""
db.py — Supabase REST API integration (stdlib only, no extra deps).

Stores profiles and generated roadmaps so they persist across sessions.
Tables: profiles, roadmaps
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://dsvalxhzglyawsfpfwxo.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRzdmFseGh6Z2x5YXdzZnBmd3hvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY3MTkxNjAsImV4cCI6MjEwMjI5NTE2MH0.O21KoQl4lPEh_xhvyGJ8k2BgJencr1r6KzWcL8J-dAQ",
)
REST_BASE = f"{SUPABASE_URL}/rest/v1"

# Flag: True if the database is reachable
_available = False


def _headers(extra=None):
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if extra:
        h.update(extra)
    return h


def _request(method, path, body=None):
    """Make a REST request to Supabase. Returns parsed JSON or None on failure."""
    url = f"{REST_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"[db] {method} {path} failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def is_available():
    """Return True if the Supabase connection works."""
    global _available
    if _available:
        return True
    result = _request("GET", "/profiles?select=id&limit=1")
    if result is not None:
        _available = True
    return _available


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def save_profile(profile):
    """Upsert a student profile. Returns the profile id (UUID).
    
    The existing Supabase 'profiles' table has columns:
      id, full_name, email, skills, created_at
    Plus new columns added by schema.sql:
      education_level, subjects, marks, interests, career_interests,
      location, financial_preference, preferred_education_path
    """
    row = {
        "full_name": profile.get("name", ""),
        "education_level": profile.get("educationLevel", ""),
        "subjects": profile.get("subjects", ""),
        "marks": profile.get("marks", ""),
        "interests": profile.get("interests", ""),
        "skills": profile.get("skills", ""),
        "career_interests": profile.get("careerInterests", ""),
        "location": profile.get("location", ""),
        "financial_preference": profile.get("financialPreference", ""),
        "preferred_education_path": profile.get("preferredEducationPath", ""),
    }

    # Try to find existing profile by full_name + subjects (simple dedup)
    name = row["full_name"]
    subjects = row["subjects"]
    if name:
        existing = _request(
            "GET",
            f"/profiles?full_name=eq.{urllib.parse.quote(name)}"
            f"&subjects=eq.{urllib.parse.quote(subjects)}&select=id&limit=1",
        )
        if existing and len(existing) > 0:
            profile_id = existing[0]["id"]
            _request("PATCH", f"/profiles?id=eq.{profile_id}", row)
            return profile_id

    result = _request("POST", "/profiles", row)
    if result and len(result) > 0:
        return result[0]["id"]
    return None


def get_profile(profile_id):
    """Fetch a profile by id."""
    result = _request("GET", f"/profiles?id=eq.{profile_id}&select=*")
    if result and len(result) > 0:
        return result[0]
    return None


# ---------------------------------------------------------------------------
# Roadmaps
# ---------------------------------------------------------------------------

def save_roadmap(profile_id, roadmap_data):
    """Save a generated roadmap. Returns the roadmap id.
    
    The existing Supabase 'roadmap' table has columns:
      id, profile_id, created_at
    Plus new columns added by schema.sql:
      mode, recommendations, skill_gaps, roadmap_data
    """
    row = {
        "profile_id": profile_id,
        "mode": roadmap_data.get("mode", "mock"),
        "recommendations": json.dumps(roadmap_data.get("recommendations", [])),
        "skill_gaps": json.dumps(roadmap_data.get("skill_gaps", [])),
        "roadmap_data": json.dumps(roadmap_data.get("roadmap", {})),
    }

    # Check if a roadmap already exists for this profile
    if profile_id:
        existing = _request(
            "GET",
            f"/roadmap?profile_id=eq.{profile_id}&select=id&limit=1",
        )
        if existing and len(existing) > 0:
            roadmap_id = existing[0]["id"]
            _request("PATCH", f"/roadmap?id=eq.{roadmap_id}", row)
            return roadmap_id

    result = _request("POST", "/roadmap", row)
    if result and len(result) > 0:
        return result[0]["id"]
    return None


def get_roadmap(profile_id):
    """Fetch the latest roadmap for a profile."""
    result = _request(
        "GET",
        f"/roadmap?profile_id=eq.{profile_id}"
        "&select=*&order=created_at.desc&limit=1",
    )
    if result and len(result) > 0:
        row = result[0]
        # Deserialize JSON strings back to objects
        for key in ("recommendations", "skill_gaps", "roadmap_data"):
            if isinstance(row.get(key), str):
                try:
                    row[key] = json.loads(row[key])
                except json.JSONDecodeError:
                    pass
        return row
    return None


def list_recent_roadmaps(limit=10):
    """List recent roadmaps with profile info."""
    result = _request(
        "GET",
        f"/roadmap?select=*,profiles(full_name,subjects)"
        f"&order=created_at.desc&limit={limit}",
    )
    return result or []


# Need this for URL encoding in queries
import urllib.parse  # noqa: E402
