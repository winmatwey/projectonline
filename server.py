
import os
import json
import bcrypt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

USERS_FILE = "users.json"
NOTES_FILE = "notes.json"
NEWS_FILE = "news.json"
GUIDES_FILE = "guides.json"
SETTINGS_FILE = "settings.json"

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_users(raw):
    if not isinstance(raw, dict):
        return {}
    new = {}
    for k,v in raw.items():
        if isinstance(v, dict):
            pwd = v.get("password", "")
            role = v.get("role", "student")
            new[k] = {"password": pwd, "role": role}
        else:
            new[k] = {"password": v, "role": "student"}
    return new

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if isinstance(stored, str) and stored.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            return False
    return password == stored

_raw_users = load_json(USERS_FILE, {})
users = normalize_users(_raw_users)
if any(not isinstance(_raw_users.get(k), dict) for k in _raw_users):
    save_json(USERS_FILE, users)

if not users:
    users = {
        "admin": {"password": hash_password("admin123"), "role": "admin"},
        "ivan":  {"password": hash_password("ivanpass"), "role": "student"},
        "masha": {"password": hash_password("mashapass"), "role": "student"}
    }
    save_json(USERS_FILE, users)

notes = load_json(NOTES_FILE, [])
news = load_json(NEWS_FILE, [])
guides = load_json(GUIDES_FILE, [])
settings = load_json(SETTINGS_FILE, {"theme": "light"})

def check_admin_payload(payload):
    if not payload:
        return False
    admin_login = payload.get("admin_login")
    admin_password = payload.get("admin_password")
    if not admin_login or not admin_password:
        return False
    u = users.get(admin_login)
    return bool(u and check_password(admin_password, u.get("password")) and u.get("role") == "admin")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(path):
        return send_from_directory(".", path)
    return send_from_directory(".", "index.html")

@app.post("/login")
def login():
    data = request.json or {}
    login = data.get("login")
    password = data.get("password")
    if not login or not password:
        return jsonify({"ok": False, "error":"login and password required"}), 400
    u = users.get(login)
    if not u or not check_password(password, u.get("password","")):
        return jsonify({"ok": False, "error":"invalid credentials"}), 401
    return jsonify({"ok": True, "role": u.get("role", "student")})

# NOTES endpoints
@app.get("/notes")
def list_notes():
    return jsonify(notes)

@app.post("/notes")
def add_note():
    data = request.json or {}
    note = {
        "title": data.get("title", ""),
        "desc": data.get("desc", ""),
        "user": data.get("user", ""),
        "image": data.get("image", "")
    }
    notes.append(note)
    save_json(NOTES_FILE, notes)
    return jsonify({"ok": True})

@app.post("/admin/notes/delete")
def admin_delete_note():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    try:
        idx = int(data.get("index"))
    except:
        return jsonify({"error":"invalid index"}), 400
    if idx < 0 or idx >= len(notes):
        return jsonify({"error":"invalid index"}), 400
    notes.pop(idx)
    save_json(NOTES_FILE, notes)
    return jsonify({"ok": True})

@app.post("/admin/notes/update")
def admin_update_note():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    try:
        idx = int(data.get("index"))
    except:
        return jsonify({"error":"invalid index"}), 400
    if idx < 0 or idx >= len(notes):
        return jsonify({"error":"invalid index"}), 400
    if "title" in data:
        notes[idx]["title"] = data.get("title", notes[idx].get("title",""))
    if "desc" in data:
        notes[idx]["desc"] = data.get("desc", notes[idx].get("desc",""))
    if "image" in data:
        notes[idx]["image"] = data.get("image", notes[idx].get("image",""))
    save_json(NOTES_FILE, notes)
    return jsonify({"ok": True})

# NEWS endpoints
@app.get("/news")
def list_news():
    return jsonify(news)

@app.post("/news")
def add_news():
    data = request.json or {}
    news_item = {
        "title": data.get("title", ""),
        "desc": data.get("desc", ""),
        "user": data.get("user", ""),
        "image": data.get("image", "")
    }
    news.append(news_item)
    save_json(NEWS_FILE, news)
    return jsonify({"ok": True})

@app.post("/admin/news/delete")
def admin_delete_news():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    try:
        idx = int(data.get("index"))
    except:
        return jsonify({"error":"invalid index"}), 400
    if idx < 0 or idx >= len(news):
        return jsonify({"error":"invalid index"}), 400
    news.pop(idx)
    save_json(NEWS_FILE, news)
    return jsonify({"ok": True})

@app.post("/admin/news/update")
def admin_update_news():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    try:
        idx = int(data.get("index"))
    except:
        return jsonify({"error":"invalid index"}), 400
    if idx < 0 or idx >= len(news):
        return jsonify({"error":"invalid index"}), 400
    if "title" in data:
        news[idx]["title"] = data.get("title", news[idx].get("title",""))
    if "desc" in data:
        news[idx]["desc"] = data.get("desc", news[idx].get("desc",""))
    if "image" in data:
        news[idx]["image"] = data.get("image", news[idx].get("image",""))
    save_json(NEWS_FILE, news)
    return jsonify({"ok": True})

# GUIDES endpoints
@app.get("/guides")
def list_guides():
    return jsonify(guides)

@app.post("/guides")
def add_guide():
    data = request.json or {}
    guide = {
        "title": data.get("title", ""),
        "desc": data.get("desc", ""),
        "user": data.get("user", ""),
        "image": data.get("image", "")
    }
    guides.append(guide)
    save_json(GUIDES_FILE, guides)
    return jsonify({"ok": True})

@app.post("/admin/guides/delete")
def admin_delete_guide():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    try:
        idx = int(data.get("index"))
    except:
        return jsonify({"error":"invalid index"}), 400
    if idx < 0 or idx >= len(guides):
        return jsonify({"error":"invalid index"}), 400
    guides.pop(idx)
    save_json(GUIDES_FILE, guides)
    return jsonify({"ok": True})

@app.post("/admin/guides/update")
def admin_update_guide():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    try:
        idx = int(data.get("index"))
    except:
        return jsonify({"error":"invalid index"}), 400
    if idx < 0 or idx >= len(guides):
        return jsonify({"error":"invalid index"}), 400
    if "title" in data:
        guides[idx]["title"] = data.get("title", guides[idx].get("title",""))
    if "desc" in data:
        guides[idx]["desc"] = data.get("desc", guides[idx].get("desc",""))
    if "image" in data:
        guides[idx]["image"] = data.get("image", guides[idx].get("image",""))
    save_json(GUIDES_FILE, guides)
    return jsonify({"ok": True})

# USER & SETTINGS endpoints
@app.post("/admin/users/list")
def admin_users_list():
    payload = request.json or {}
    if not check_admin_payload(payload):
        return jsonify({"error":"admin auth required"}), 403
    return jsonify({k: {"role": v["role"]} for k,v in users.items()})

@app.post("/admin/users/add_or_update")
def admin_users_add_update():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    login = data.get("login")
    password = data.get("password")
    role = data.get("role", "student")
    if not login:
        return jsonify({"error":"login required"}), 400
    if password:
        users[login] = {"password": hash_password(password), "role": role}
    else:
        if login in users:
            users[login]["role"] = role
        else:
            return jsonify({"error":"password required for new user"}), 400
    save_json(USERS_FILE, users)
    return jsonify({"ok": True})

@app.post("/admin/users/delete")
def admin_users_delete():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    login = data.get("login")
    if not login or login not in users:
        return jsonify({"error":"user not found"}), 404
    if users[login].get("role") == "admin":
        admins = [k for k,v in users.items() if v.get("role") == "admin"]
        if len(admins) <= 1:
            return jsonify({"error":"cannot delete the last admin"}), 400
    users.pop(login, None)
    save_json(USERS_FILE, users)
    return jsonify({"ok": True})

@app.get("/admin/settings/theme")
def get_theme():
    return jsonify(settings)

@app.post("/admin/settings/theme")
def set_theme():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    theme = data.get("theme")
    if theme not in ["light","dark"]:
        return jsonify({"error":"invalid theme"}), 400
    settings["theme"] = theme
    save_json(SETTINGS_FILE, settings)
    return jsonify({"ok": True})

# TESTS endpoints
TESTS_FILE = "tests.json"
RESULTS_FILE = "results.json"
tests = load_json(TESTS_FILE, [])
results = load_json(RESULTS_FILE, [])

@app.get("/tests")
def get_tests_public():
    safe = []
    for t in tests:
        tcopy = {k: v for k, v in t.items() if k != 'questions'}
        qs = []
        for q in t.get('questions', []):
            if not isinstance(q, dict):
                qtext = str(q) if q is not None else ''
                qcopy = {'q': qtext, 'choices': []}
            else:
                qtext = q.get('q') or q.get('question') or q.get('text') or ''
                choices_raw = q.get('choices', [])
                if choices_raw is None:
                    choices = []
                elif isinstance(choices_raw, list):
                    normalized = []
                    for c in choices_raw:
                        if c is None:
                            continue
                        if isinstance(c, dict):
                            normalized.append(str(c.get('text') or c.get('label') or c.get('choice') or json.dumps(c, ensure_ascii=False)))
                        else:
                            normalized.append(str(c))
                    choices = normalized
                else:
                    if isinstance(choices_raw, dict):
                        choices = [str(choices_raw.get('text') or choices_raw.get('label') or json.dumps(choices_raw, ensure_ascii=False))]
                    else:
                        choices = [str(choices_raw)]
                qcopy = {'q': qtext, 'choices': choices}
            qs.append(qcopy)
        tcopy['questions'] = qs
        safe.append(tcopy)
    return jsonify(safe)

@app.post("/tests/submit")
def submit_test():
    data = request.json or {}
    test_id = data.get('test_id')
    answers = data.get('answers', [])
    user = data.get('user', 'unknown')
    t = next((x for x in tests if x.get('id') == test_id), None)
    if not t:
        return jsonify({'error':'test not found'}), 404
    correct = 0
    for i, q in enumerate(t.get('questions', [])):
        if i < len(answers) and isinstance(q.get('correct'), int) and answers[i] == q.get('correct'):
            correct += 1
    score = {'user': user, 'test_id': test_id, 'score': correct, 'total': len(t.get('questions', []))}
    results.append(score)
    save_json(RESULTS_FILE, results)
    return jsonify(score)

@app.post("/admin/tests/list")
def admin_tests_list():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    return jsonify(tests)

@app.post("/admin/tests/add_or_update")
def admin_tests_add_update():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    test = data.get('test')
    if not test or 'title' not in test or 'questions' not in test:
        return jsonify({'error':'invalid test structure'}), 400
    if 'id' not in test:
        test['id'] = (max([t.get('id',0) for t in tests]) + 1) if tests else 1
        tests.append(test)
    else:
        for i,t in enumerate(tests):
            if t.get('id') == test.get('id'):
                tests[i] = test
                break
        else:
            tests.append(test)
    save_json(TESTS_FILE, tests)
    return jsonify({'ok':True, 'id': test['id']})

@app.post("/admin/tests/delete")
def admin_tests_delete():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    tid = data.get('id')
    for i,t in enumerate(tests):
        if t.get('id') == tid:
            tests.pop(i); save_json(TESTS_FILE, tests); return jsonify({'ok':True})
    return jsonify({'error':'not found'}), 404

@app.post("/admin/results")
def admin_results():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
