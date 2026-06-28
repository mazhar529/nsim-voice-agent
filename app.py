"""
╔══════════════════════════════════════════════════════════════════════╗
║              NSIM AI VOICE ASSISTANT — app.py                       ║
║                                                                      ║
║  SETUP (only 2 steps):                                              ║
║                                                                      ║
║  Step 1 — Get your FREE Puter token (30 seconds, no card):         ║
║    a) Go to  https://puter.com  and sign up free                   ║
║    b) Open browser console (F12 → Console tab)                     ║
║    c) Type:  puter.auth.getUser().then(u => console.log(puter.authToken)) ║
║    d) Copy the long token that appears                              ║
║    e) Paste it below where it says  PASTE_YOUR_PUTER_TOKEN_HERE    ║
║                                                                      ║
║  Step 2 — Deploy on Render.com (free):                             ║
║    See DEPLOY.md for exact steps                                    ║
║                                                                      ║
║  Then in Twilio → set webhook to:  https://YOURAPP.onrender.com/call ║
║                                                                      ║
║  COST: Only Twilio number. Everything else FREE.                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ★★★ PASTE YOUR PUTER TOKEN HERE ★★★
PUTER_TOKEN = "PASTE_YOUR_PUTER_TOKEN_HEREeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InYyIn0.eyJ0IjoiZ3VpIiwidiI6IjIiLCJ1IjoidkRpRjk3UzhRUDZPUlMycTI0Z3QrZz09Iiwic3UiOiJ2RGlGOTdTOFFQNk9SUzJxMjRndCtnPT0iLCJ1dSI6ImZPZG9iWEU1UklHTms2M3Vtendyd1E9PSIsImFpIjoiZk9kb2JYRTVSSUdOazYzdW16d3J3UT09IiwiaWF0IjoxNzgyNjM0NTg5fQ.MiTIZD4i8qG-o1ykB2U929IzNMj7ZwEZUvssLW9pgWU"
# Get it free in 30 sec — see instructions above
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★


import os, uuid, json, time, threading, urllib.request, urllib.parse
from pathlib import Path
from flask import Flask, request, Response
from database import (
    build_knowledge, INTEREST_KEYWORDS,
    CONTACT_NUMBER, WHATSAPP_NUMBER, COURSES
)

app     = Flask(__name__)
PORT    = int(os.environ.get("PORT", 5000))

AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ── Puter AI endpoint (OpenAI-compatible, free) ──────────────────────
PUTER_API  = "https://api.puter.com/puterai/openai/v1/chat/completions"
AI_MODEL   = "gemini-3.5-flash"   # Best free model on Puter — fast + smart
NSIM_INFO  = build_knowledge()    # Built from database.py

# ── Concurrent call counter ───────────────────────────────────────────
active_calls    = 0
calls_lock      = threading.Lock()
MAX_CALLS       = 200   # Handle up to 200 simultaneous callers

# ── Conversation memory (per call session) ────────────────────────────
_sessions = {}
_sess_lock = threading.Lock()

def get_history(sid):
    with _sess_lock: return list(_sessions.get(sid, []))

def add_to_history(sid, role, text):
    with _sess_lock:
        _sessions.setdefault(sid, [])
        _sessions[sid].append({"role": role, "content": text})
        if len(_sessions[sid]) > 10:          # Keep last 5 turns
            _sessions[sid] = _sessions[sid][-10:]

def clear_session(sid):
    with _sess_lock:
        _sessions.pop(sid, None)

def _purge_old_sessions():
    """Delete sessions older than 30 min — runs in background"""
    while True:
        time.sleep(900)
        with _sess_lock:
            keys = list(_sessions.keys())
            if len(keys) > MAX_CALLS:
                for k in keys[:len(keys)//2]:
                    del _sessions[k]

threading.Thread(target=_purge_old_sessions, daemon=True).start()

# ── Audio file cleanup ────────────────────────────────────────────────
def cleanup_audio():
    now = time.time()
    for f in AUDIO_DIR.glob("*.mp3"):
        try:
            if now - f.stat().st_mtime > 600: f.unlink()
        except: pass


# ════════════════════════════════════════════════════════════════════
#  LANGUAGE DETECTION — Hindi or English, no library needed
# ════════════════════════════════════════════════════════════════════
_HI_WORDS = {
    "kya","hai","hain","kaise","kitni","kitna","kab","kahan","kahaan",
    "mujhe","mera","meri","aap","tum","hum","batao","bataaiye","chahiye",
    "nahi","nahin","haan","bhi","aur","ya","lekin","toh","fees","admission",
    "batch","karein","karo","mein","ka","ki","ke","se","par","ko","wala",
    "kuch","sab","agar","abhi","course","timing","kitne","kaun","accha",
    "bata","dijiye","lena","milegi","milega","karna","samjhao","sawaal",
    "free","demo","join","lena","dena","start","iska","uska","yahan",
}

def detect_lang(text: str) -> str:
    if not text: return "hi"
    if any("\u0900" <= c <= "\u097F" for c in text): return "hi"
    words = set(text.lower().split())
    if words & _HI_WORDS: return "hi"
    ascii_alpha = sum(1 for c in text if c.isalpha() and c.isascii())
    return "en" if ascii_alpha > len(text) * 0.65 else "hi"


# ════════════════════════════════════════════════════════════════════
#  INTEREST DETECTION — should we send WhatsApp lead?
# ════════════════════════════════════════════════════════════════════
def is_interested(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in INTEREST_KEYWORDS)


# ════════════════════════════════════════════════════════════════════
#  WHATSAPP LEAD NOTIFICATION via Twilio WhatsApp Sandbox (free)
# ════════════════════════════════════════════════════════════════════
TWILIO_SID    = os.environ.get("TWILIO_SID", "")
TWILIO_TOKEN  = os.environ.get("TWILIO_TOKEN", "")
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"  # Twilio sandbox number

def send_whatsapp_lead(caller_number: str, caller_said: str):
    """
    Sends a WhatsApp message to NSIM when a caller shows interest.
    Uses Twilio WhatsApp Sandbox — free to use.
    Runs in background thread so it doesn't slow down the call.
    """
    if not TWILIO_SID or not TWILIO_TOKEN:
        print(f"[LEAD] {caller_number} interested — set TWILIO_SID and TWILIO_TOKEN env vars to enable WhatsApp")
        return

    def _send():
        try:
            msg = (
                f"🔔 *New NSIM Lead!*\n\n"
                f"📞 Caller number: {caller_number}\n"
                f"💬 They said: {caller_said[:200]}\n"
                f"⏰ Time: {time.strftime('%d %b %Y %I:%M %p')}\n\n"
                f"Follow up kar lo! 🎯"
            )
            to = f"whatsapp:+{WHATSAPP_NUMBER}"
            payload = urllib.parse.urlencode({
                "From": TWILIO_WHATSAPP_FROM,
                "To"  : to,
                "Body": msg,
            }).encode()
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
            req = urllib.request.Request(url, data=payload, method="POST")
            # Basic auth
            import base64
            creds = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
            req.add_header("Authorization", f"Basic {creds}")
            with urllib.request.urlopen(req, timeout=10) as r:
                print(f"[LEAD] WhatsApp sent to {WHATSAPP_NUMBER} for caller {caller_number}")
        except Exception as e:
            print(f"[LEAD] WhatsApp error: {e}")

    threading.Thread(target=_send, daemon=True).start()


# ════════════════════════════════════════════════════════════════════
#  PUTER AI — Gemini 3.5 Flash via Puter (free, no key)
# ════════════════════════════════════════════════════════════════════
def ask_ai(user_text: str, lang: str, history: list) -> str:
    if lang == "hi":
        system = (
            "Aap NSIM ke phone voice assistant hain. Yeh niyam hamesha follow karein:\n"
            "1. Sirf simple aur asaan Hindi mein jawab dein. Koi mushkil shabd nahi.\n"
            "2. Koi bhi symbol bilkul nahi — na star, na slash, na percent, na bracket,\n"
            "   na hash, na dash line mein, koi special character nahi.\n"
            "3. Koi list ya numbering nahi. Seedhe aam bolne wali bhasha mein bolo.\n"
            "4. Bahut chhota jawab — sirf do ya teen vaakya.\n"
            "5. Sirf NSIM ke baare mein sawaalon ka jawab dein.\n"
            "6. Agar kuch pata nahi to bolein: zyada jaankari ke liye "
            f"{CONTACT_NUMBER} par call karein.\n\n"
            f"NSIM ki poori jaankari:\n{NSIM_INFO}"
        )
    else:
        system = (
            "You are the phone voice assistant for NSIM. Always follow these rules:\n"
            "1. Reply only in simple, short English sentences.\n"
            "2. Never use any symbols — no asterisk, slash, percent, bracket, dash, hash, nothing.\n"
            "3. No lists or numbering. Speak naturally like a real person on the phone.\n"
            "4. Very short answer — only two or three sentences maximum.\n"
            "5. Only answer questions about NSIM.\n"
            "6. If unsure say: please call us at "
            f"{CONTACT_NUMBER} for more details.\n\n"
            f"NSIM information:\n{NSIM_INFO}"
        )

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    payload = json.dumps({
        "model"      : AI_MODEL,
        "messages"   : messages,
        "max_tokens" : 130,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        PUTER_API, data=payload,
        headers={
            "Content-Type" : "application/json",
            "Authorization": f"Bearer {PUTER_TOKEN}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data  = json.loads(r.read())
            reply = data["choices"][0]["message"]["content"].strip()
            # Strip any accidental symbols
            for sym in ["*","#","\\","|","`","~","^","_","[","]","(",")","{","}"]:
                reply = reply.replace(sym, "")
            return reply.strip()

    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"[AI] Puter error {e.code}: {err[:300]}")
        if "401" in str(e.code) or "token" in err.lower():
            return _err(lang, token_err=True)
        return _err(lang)
    except Exception as e:
        print(f"[AI] error: {e}")
        return _err(lang)

def _err(lang, token_err=False):
    if token_err:
        return ("Puter token sahi nahi laga hai. "
                "App.py mein apna token daalein.") if lang == "hi" else (
                "Puter token is not configured. Please add it in app.py.")
    if lang == "hi":
        return f"Abhi kuch takneeki dikkat hai. Kripya {CONTACT_NUMBER} par call karein."
    return f"Sorry, technical issue. Please call {CONTACT_NUMBER}."


# ════════════════════════════════════════════════════════════════════
#  GOOGLE TTS — natural Hindi/English voice, completely free
# ════════════════════════════════════════════════════════════════════
def make_audio(text: str, lang: str) -> str | None:
    name = f"{uuid.uuid4().hex}.mp3"
    path = AUDIO_DIR / name
    safe = text[:180].replace("\n", " ")
    gtts_lang = "hi" if lang == "hi" else "en"
    params = urllib.parse.urlencode({
        "ie": "UTF-8", "q": safe, "tl": gtts_lang,
        "client": "tw-ob", "ttsspeed": "0.85",
    })
    url = f"https://translate.google.com/translate_tts?{params}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"),
            "Referer": "https://translate.google.com/",
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            path.write_bytes(r.read())
        host = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
        return f"{host}/static/audio/{name}"
    except Exception as e:
        print(f"[TTS] error: {e}")
        return None


# ════════════════════════════════════════════════════════════════════
#  TWIML HELPERS
# ════════════════════════════════════════════════════════════════════
def _xml(body: str) -> Response:
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n{body}\n</Response>',
        mimetype="text/xml"
    )

def _host() -> str:
    return os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")

def _speak(text: str, lang: str) -> str:
    url = make_audio(text, lang)
    if url:
        return f'  <Play>{url}</Play>'
    safe = text.replace("&","and").replace("<","").replace(">","")
    tl   = "hi-IN" if lang == "hi" else "en-IN"
    return f'  <Say language="{tl}">{safe}</Say>'

def _listen(action: str) -> str:
    return (f'  <Gather input="speech" action="{_host()}{action}" method="POST" '
            f'speechTimeout="auto" timeout="8" language="hi-IN,en-IN"></Gather>')


# ════════════════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════════════

@app.route("/call", methods=["GET","POST"])
def incoming_call():
    """Twilio calls this when someone dials the NSIM number."""
    global active_calls
    cleanup_audio()

    with calls_lock:
        active_calls += 1
        current = active_calls
    print(f"[CALL] New call — active: {current}")

    # If too many callers, give a polite message
    if current > MAX_CALLS:
        with calls_lock: active_calls -= 1
        msg = ("Abhi bahut saare log ek saath baat kar rahe hain. "
               "Kripya thodi der baad call karein ya "
               f"{CONTACT_NUMBER} par seedha call karein. Shukriya.")
        return _xml(f"{_speak(msg,'hi')}\n  <Hangup/>")

    greet = ("Namaste! Aap NSIM ke AI assistant se baat kar rahe hain. "
             "Digital Marketing, Data Science, aur aur bhi courses ke baare mein "
             "Hindi ya English mein poochhein. Main aapki madad karoonga.")

    return _xml(f"""
{_speak(greet, "hi")}
{_listen("/answer")}
  <Redirect method="POST">{_host()}/silent</Redirect>""")


@app.route("/answer", methods=["POST"])
def answer():
    """Main handler — gets caller's speech, asks AI, speaks reply."""
    global active_calls
    sid          = request.form.get("CallSid", "x")
    user_text    = request.form.get("SpeechResult", "").strip()
    caller_num   = request.form.get("From", "unknown")

    print(f"[{sid[:8]}] Said: {user_text!r}")

    if not user_text:
        return silent()

    lang    = detect_lang(user_text)
    history = get_history(sid)

    # Ask AI
    reply = ask_ai(user_text, lang, history)
    print(f"[{sid[:8]}] AI ({lang}): {reply!r}")

    # Save to history
    add_to_history(sid, "user",      user_text)
    add_to_history(sid, "assistant", reply)

    # Check if caller is interested → send WhatsApp lead
    if is_interested(user_text):
        send_whatsapp_lead(caller_num, user_text)
        # Slip in a gentle call-to-action in the reply
        if lang == "hi":
            reply += f" Hum aapko call karke aur madad karenge."
        else:
            reply += f" We will reach out to you with more details."

    # Continue listening
    prompt = "Aur koi sawaal?" if lang == "hi" else "Any other questions?"

    return _xml(f"""
{_speak(reply, lang)}
{_speak(prompt, lang)}
{_listen("/answer")}
  <Redirect method="POST">{_host()}/bye</Redirect>""")


@app.route("/call_ended", methods=["POST"])
def call_ended():
    """Called by Twilio status callback when call ends — clean up session."""
    global active_calls
    sid = request.form.get("CallSid", "x")
    clear_session(sid)
    with calls_lock:
        active_calls = max(0, active_calls - 1)
    print(f"[CALL] Ended {sid[:8]} — active: {active_calls}")
    return "", 204


@app.route("/silent", methods=["GET","POST"])
def silent():
    msg = ("Aapki awaaz nahi aayi. Kripya apna sawaal poochhein "
           f"ya {CONTACT_NUMBER} par seedha call karein. Shukriya.")
    return _xml(f"{_speak(msg,'hi')}\n  <Hangup/>")


@app.route("/bye", methods=["GET","POST"])
def bye():
    msg = ("Shukriya NSIM ko call karne ke liye. "
           "Agar koi sawaal ho to dobaara zaroor call karein. Namaste.")
    return _xml(f"{_speak(msg,'hi')}\n  <Hangup/>")


@app.route("/health")
def health():
    token_ok = PUTER_TOKEN != "PASTE_YOUR_PUTER_TOKEN_HERE" and len(PUTER_TOKEN) > 20
    return {
        "status"       : "running",
        "agent"        : "NSIM Voice Assistant",
        "puter_token"  : "set ✓" if token_ok else "❌ NOT SET — add your token in app.py",
        "active_calls" : active_calls,
        "ai_model"     : AI_MODEL,
        "courses_loaded": len(COURSES),
        "render_url"   : os.environ.get("RENDER_EXTERNAL_URL", "local"),
    }, 200


@app.route("/")
def root():
    token_ok = PUTER_TOKEN != "PASTE_YOUR_PUTER_TOKEN_HERE" and len(PUTER_TOKEN) > 20
    color    = "#22c55e" if token_ok else "#ef4444"
    msg      = "Agent is live and ready ✓" if token_ok else "⚠ Add your Puter token in app.py"
    return f"""<!DOCTYPE html>
<html><head><title>NSIM Voice Agent</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:640px;margin:60px auto;padding:24px;background:#f9fafb}}
  h1{{color:#1e293b;margin-bottom:4px}}
  .sub{{color:#64748b;margin-bottom:32px}}
  .card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:99px;font-size:13px;font-weight:600;
          background:{color}20;color:{color}}}
  .row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;
        border-bottom:1px solid #f1f5f9}}
  .row:last-child{{border-bottom:none}}
  code{{background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:13px}}
</style></head>
<body>
<h1>NSIM Voice Assistant</h1>
<p class="sub">AI-powered phone agent for nsim.in</p>
<div class="card">
  <span class="badge">{msg}</span>
  <div class="row"><span>Active calls</span><strong>{active_calls}</strong></div>
  <div class="row"><span>AI model</span><code>{AI_MODEL} via Puter</code></div>
  <div class="row"><span>Courses loaded</span><strong>{len(COURSES)}</strong></div>
  <div class="row"><span>Twilio webhook</span><code>/call</code></div>
  <div class="row"><span>Health check</span><a href="/health"><code>/health</code></a></div>
</div>
<div class="card">
  <strong>Twilio status callback URL:</strong><br>
  <code>{os.environ.get("RENDER_EXTERNAL_URL","https://yourapp.onrender.com")}/call_ended</code><br>
  <small style="color:#64748b">Set this in Twilio → Phone Number → Call Status Callbacks</small>
</div>
</body></html>"""


if __name__ == "__main__":
    token_ok = PUTER_TOKEN != "PASTE_YOUR_PUTER_TOKEN_HERE" and len(PUTER_TOKEN) > 20
    print("=" * 60)
    print("  NSIM AI Voice Agent")
    print(f"  Puter token : {'set ✓' if token_ok else '❌ NOT SET — add it above'}")
    print(f"  AI model    : {AI_MODEL}")
    print(f"  Courses     : {len(COURSES)} loaded from database.py")
    print("=" * 60)
    if not token_ok:
        print("  ⚠  Go to puter.com → F12 console → paste token above")
    print(f"  Twilio webhook → http://localhost:{PORT}/call")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PORT, debug=False)
