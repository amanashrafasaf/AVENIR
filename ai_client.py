"""
ai_client.py — Real AI integration point (TODO: plug your provider).

The server uses mock mode (mock_data.generate_roadmap) by default. When you
implement `generate_roadmap_with_ai` below and set OPENAI_API_KEY, the server
will call the real AI and fall back to mock mode on ANY error, so the demo
never breaks.

The AI must return STRICT structured JSON matching the schema produced by
mock_data.generate_roadmap (recommendations / skill_gaps / roadmap). The
frontend renders both identically — that JSON contract is the whole point.
"""

import json
import os
import urllib.request
import urllib.error

from mock_data import generate_roadmap as mock_generate

SYSTEM_PROMPT = """You are the career-analysis engine of an AI Career Navigator. \
You receive a student profile and must respond with STRICT JSON only — no prose, \
no markdown. The JSON must exactly match this schema:

{
  "profile": <echo the input profile>,
  "mode": "ai",
  "recommendations": [
    {
      "career": "string",
      "match_score": <int 0-100>,
      "match_reasons": ["string"],
      "summary": "string",
      "salary_range": "string",
      "demand_outlook": "string",
      "education_paths": ["string"]
    }
  ],
  "skill_gaps": [
    { "skill": "string", "importance": "high|medium", "how_to_learn": "string" }
  ],
  "roadmap": {
    "years": [
      { "year": "Year N — Phase", "phase": "string",
        "milestones": [ { "title": "string", "type": "course|project|skill|internship|certification|education|scholarship|career", "detail": "string" } ] }
    ],
    "courses": ["string"],
    "certifications": ["string"],
    "degree_options": ["string"],
    "scholarships": [ { "name": "string", "for": "string", "amount": "string" } ],
    "demand_outlook": "string",
    "salary_range": "string",
    "match_summary": "string"
  }
}

Rules:
- Score careers against the student's actual subjects, marks, skills, interests,
  location, financial preference and preferred education path. Never invent data.
- Give 3 recommendations ranked by match. Be honest about mismatches.
- Recommend free/cheap learning resources first; respect financial preference.
- Indian context: use INR, Indian exams (NEET, CA, JEE, NSP scholarships), Indian colleges.
"""

USER_PROMPT_TEMPLATE = """Student profile (JSON): {profile_json}

Generate the personalized career roadmap as strict JSON."""


def generate_roadmap_with_ai(profile):
    """Call the real AI. Returns a dict matching the schema, or None on failure.

    Implement the actual request below. Uses only stdlib (urllib) so there are
    no extra dependencies. Swap in your preferred provider/HTTP client freely.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        return None

    try:
        body = json.dumps({
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(profile_json=json.dumps(profile))},
            ],
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
        # Validate we got the expected shape
        if "recommendations" not in result or "roadmap" not in result:
            return None
        result["profile"] = profile
        result["mode"] = "ai"
        return result
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ai_client] AI call failed, falling back to mock: {exc}")
        return None


def generate_roadmap(profile):
    """Top-level: try AI, fall back to DEMO_MODE mock. Never throws."""
    if os.environ.get("DEMO_MODE") == "1":
        return mock_generate(profile)
    result = generate_roadmap_with_ai(profile)
    if result is not None:
        return result
    mock = mock_generate(profile)
    mock["mode"] = "mock"
    return mock


def answer_chat(message, profile):
    """Profile-aware chat. Real AI integration is a TODO; mock is deterministic."""
    from mock_data import answer_chat as mock_answer
    if os.environ.get("DEMO_MODE") == "1" or not os.environ.get("OPENAI_API_KEY"):
        return {"reply": mock_answer(message, profile), "mode": "mock"}
    # TODO: real chat call with profile grounding (same system-prompt pattern).
    return {"reply": mock_answer(message, profile), "mode": "mock"}
