"""
smoke_test.py — Verifies the full app in one shot, no shell job control needed.

Starts the server in-process on a random port and exercises:
    GET  /            (static index)
    GET  /api/health
    POST /api/generate
    POST /api/chat

Run:  python smoke_test.py
"""

import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, ".")
import server  # noqa: E402


def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.read()


def post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.read()


def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    ok = True

    def check(name, cond, extra=""):
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"[{status}] {name} {extra}")

    try:
        status, body = get(f"{base}/")
        check("GET / serves index.html", status == 200 and b"AVENIR" in body)

        status, body = get(f"{base}/api/health")
        health = json.loads(body)
        check("GET /api/health", status == 200 and health.get("ok") is True,
              f"-> mode={health.get('mode')}")

        profile = {
            "name": "Aarav",
            "educationLevel": "Class 11/12",
            "subjects": "Maths, Physics, Computer Science",
            "marks": "82",
            "interests": "coding, chess, gaming",
            "skills": "Python basics, Excel",
            "careerInterests": "tech",
            "location": "Patna, Bihar",
            "financialPreference": "Need scholarships/grants",
            "preferredEducationPath": "University degree",
        }
        status, body = post(f"{base}/api/generate", {"profile": profile})
        data = json.loads(body)
        check("POST /api/generate", status == 200 and len(data.get("recommendations", [])) == 3,
              f"-> top: {data['recommendations'][0]['career']} {data['recommendations'][0]['match_score']}%")
        check("schema: skill_gaps present", isinstance(data.get("skill_gaps"), list))
        roadmap = data.get("roadmap", {})
        check("schema: roadmap.years", len(roadmap.get("years", [])) == 4)
        check("schema: courses/certs/degrees/scholarships",
              roadmap.get("courses") and roadmap.get("certifications")
              and roadmap.get("degree_options") and roadmap.get("scholarships"))
        check("mode flag", data.get("mode") == "mock")

        # A commerce student should score differently (engine adapts to input)
        profile2 = dict(profile, subjects="Commerce, Accountancy, Economics", interests="business, money",
                        skills="Excel", preferredEducationPath="University degree")
        status, body = post(f"{base}/api/generate", {"profile": profile2})
        data2 = json.loads(body)
        top2 = data2["recommendations"][0]["career"]
        check("engine adapts to profile (commerce -> finance/business)",
              any(k in top2 for k in ("Analyst", "Manager", "Accountant", "Marketer", "Entrepreneur")),
              f"-> top: {top2}")

        status, body = post(f"{base}/api/chat",
                            {"message": "I like mathematics but don't want engineering. What options do I have?",
                             "profile": profile})
        chat = json.loads(body)
        check("POST /api/chat", status == 200 and len(chat.get("reply", "")) > 40, "-> reply ok")

        # Bad input
        try:
            post(f"{base}/api/generate", {})
            check("POST /api/generate empty -> 400", False)
        except urllib.error.HTTPError as e:
            check("POST /api/generate empty -> 400", e.code == 400)
    finally:
        httpd.shutdown()

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
