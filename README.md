# AVENIR — AI Career Navigator

An AI-powered personal career navigator (internal hackathon / SIH 2026 prelude).

**Flow:** Student Profile → AI Analysis → Career Recommendations → Skill Gap Analysis → Learning Roadmap → Courses/Certifications → College/Degree Options → Scholarships → Trackable 3–5 Year Roadmap (+ profile-aware career chat).

## Run it

```bash
python server.py            # serves http://127.0.0.1:8000
PORT=9000 python server.py  # custom port
```

No dependencies — pure Python 3 stdlib. No build step, no install, works offline.

## Database Setup (Supabase)

Profiles and roadmaps are persisted to Supabase. To set up:

1. Go to your Supabase project → **SQL Editor**
2. Paste and run the contents of `schema.sql`
3. This adds the required columns to the existing `profiles` and `roadmap` tables and enables RLS policies

The connection is configured in `db.py` with your project URL and anon key. Data is saved on every `/api/generate` call (best-effort, never blocks the response).

## DEMO_MODE (offline fallback)

By default the server runs in **DEMO_MODE**: the `/api/generate` endpoint returns deterministic, rule-based recommendations generated from the student's profile (no internet, no API key). This is the offline fallback for tomorrow's demo.

- `DEMO_MODE=1` — force mock mode even if an AI key exists.
- Without `OPENAI_API_KEY`, mock mode is used automatically.
- Check the mode via `GET /api/health`.

## Plugging in a real AI (later)

The AI layer lives in `ai_client.py` — a stub with the prompt template ready. Implement `generate_roadmap_with_ai(profile)` (structured JSON in the same schema) and set `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`). The server auto-detects the key and falls back to mock mode on any error, so the demo never breaks.

## Structure

```
career-navigator/
  server.py       # stdlib HTTP server: static files + JSON API
  db.py           # Supabase REST API integration
  mock_data.py    # rule-based career engine (scoring, skill gaps, roadmap, scholarships)
  ai_client.py    # real AI stub (TODO: plug provider)
  schema.sql      # Supabase migration (run in SQL Editor)
  static/         # frontend (no build step)
    index.html
    app.js
    styles.css
    avenir-logo.jpeg
```

## API

| Endpoint | Method | Body | Returns |
|---|---|---|---|
| `/api/generate` | POST | `{ profile }` | `{ recommendations[], skill_gaps[], roadmap{...}, mode, profile_id }` |
| `/api/chat` | POST | `{ message, profile }` | `{ reply, mode }` (profile-aware) |
| `/api/health` | GET | — | `{ ok, mode, demo_mode, db_connected }` |
| `/api/roadmaps` | GET | — | `{ roadmaps[] }` (recent roadmaps with profile info) |

The response schema is fixed (see `mock_data.generate_roadmap`) so the frontend renders the same cards whether the data comes from mock mode or a real AI.

Generated roadmaps are automatically persisted to Supabase on every `/api/generate` call.
