from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os

app = Flask(__name__)
CORS(app)

USERS_FILE = "users.json"
NOTES_FILE = "notes.json"

# Load data from files
def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_data(USERS_FILE)
notes = load_data(NOTES_FILE).get("notes", [])

@app.post("/register")
def register():
    data = request.json
    email, password = data["email"], data["password"]
    if email in users:
        return {"error":"User exists"}, 400
    users[email] = password
    save_data(USERS_FILE, users)
    return {"ok":True}

@app.post("/login")
def login():
    data = request.json
    email, password = data["email"], data["password"]
    if users.get(email) != password:
        return {"error":"Invalid credentials"}, 401
    return {"ok":True}

@app.get("/notes")
def list_notes():
    return jsonify(notes)

@app.post("/notes")
def add_note():
    data = request.json
    note = {
        "title": data.get("title"),
        "desc": data.get("desc"),
        "user": data.get("user"),
        "image": data.get("image", "")
    }
    notes.append(note)
    save_data(NOTES_FILE, {"notes": notes})
    return {"ok":True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
