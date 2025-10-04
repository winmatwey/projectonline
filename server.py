
import os
import json
import bcrypt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

USERS_FILE = "users.json"
NOTES_FILE = "notes.json"
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

# --- Testing system endpoints ---
TESTS_FILE = "tests.json"
RESULTS_FILE = "results.json"

tests = load_json(TESTS_FILE, [])
results = load_json(RESULTS_FILE, [])

# Return tests for students (hide correct answers)
@app.get("/tests")
def get_tests_public():
    safe = []
    for t in tests:
        tcopy = {k: v for k, v in t.items() if k != 'questions'}
        # include questions but remove 'correct' keys
        qs = []
        for q in t.get('questions', []):
            qcopy = {'q': q.get('q'), 'choices': q.get('choices')}
            qs.append(qcopy)
        tcopy['questions'] = qs
        safe.append(tcopy)
    return jsonify(safe)

# Submit test answers: {test_id, answers: [choice_index,...], user}
@app.post("/tests/submit")
def submit_test():
    data = request.json or {}
    test_id = data.get('test_id')
    answers = data.get('answers', [])
    user = data.get('user', 'unknown')
    # find test
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

# Admin: list tests with answers
@app.post("/admin/tests/list")
def admin_tests_list():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    return jsonify(tests)

# Admin: add or update test (send full test object; if id matches update)
@app.post("/admin/tests/add_or_update")
def admin_tests_add_update():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    test = data.get('test')
    if not test or 'title' not in test or 'questions' not in test:
        return jsonify({'error':'invalid test structure'}), 400
    # assign id if missing
    if 'id' not in test:
        test['id'] = (max([t.get('id',0) for t in tests]) + 1) if tests else 1
        tests.append(test)
    else:
        # update existing
        for i,t in enumerate(tests):
            if t.get('id') == test.get('id'):
                tests[i] = test
                break
        else:
            tests.append(test)
    save_json(TESTS_FILE, tests)
    return jsonify({'ok':True, 'id': test['id']})

# Admin: delete test by id
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

# Admin: get results
@app.post("/admin/results")
def admin_results():
    data = request.json or {}
    if not check_admin_payload(data):
        return jsonify({"error":"admin auth required"}), 403
    return jsonify(results)
# --- end testing system ---


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
