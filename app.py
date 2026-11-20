import os
import csv
import sqlite3
from io import StringIO
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "raga_emotion.db")
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")
ALLOWED_AUDIO = {"mp3", "wav", "ogg", "m4a"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")

EMOTIONS = [
    ("sringara", "Śṛṅgāra", "Love"),
    ("hasya", "Hāsya", "Joy / Laughter"),
    ("karuna", "Karuṇa", "Compassion / Sadness"),
    ("raudra", "Raudra", "Anger"),
    ("vira", "Vīra", "Heroism"),
    ("bhayanaka", "Bhayānaka", "Fear"),
    ("bibhatsa", "Bībhatsa", "Disgust"),
    ("adbhuta", "Adbhuta", "Wonder"),
    ("shanta", "Śānta", "Peace / Tranquility"),
]

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'participant',
        age TEXT, gender TEXT, education TEXT, occupation TEXT, location TEXT,
        native_language TEXT, musical_background TEXT, years_training TEXT,
        familiarity_music TEXT, familiarity_raga TEXT, listening_frequency TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ragas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        thaat TEXT,
        performer TEXT,
        rendition_type TEXT,
        duration TEXT,
        audio_file TEXT,
        recording_info TEXT
    );
    CREATE TABLE IF NOT EXISTS listening (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        raga_id INTEGER NOT NULL,
        listened_seconds INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, raga_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(raga_id) REFERENCES ragas(id)
    );
    CREATE TABLE IF NOT EXISTS annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        raga_id INTEGER NOT NULL,
        listened_seconds INTEGER NOT NULL,
        sringara INTEGER NOT NULL, hasya INTEGER NOT NULL, karuna INTEGER NOT NULL,
        raudra INTEGER NOT NULL, vira INTEGER NOT NULL, bhayanaka INTEGER NOT NULL,
        bibhatsa INTEGER NOT NULL, adbhuta INTEGER NOT NULL, shanta INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, raga_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(raga_id) REFERENCES ragas(id)
    );
    """)
    # Add a few starter raga records. Upload your own audio files from the admin page.
    count = conn.execute("SELECT COUNT(*) FROM ragas").fetchone()[0]
    if count == 0:
        starter = [
            ("Yaman", "Kalyan", "Add performer", "Instrumental", "3+ minutes", None, ""),
            ("Bhairav", "Bhairav", "Add performer", "Vocal", "3+ minutes", None, ""),
            ("Bageshri", "Kafi", "Add performer", "Instrumental", "3+ minutes", None, ""),
        ]
        conn.executemany("""INSERT INTO ragas
            (name, thaat, performer, rendition_type, duration, audio_file, recording_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)""", starter)
    # Create a local demo admin if one does not already exist.
    admin_name = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin1234")
    admin = conn.execute("SELECT id FROM users WHERE username = ?", (admin_name,)).fetchone()
    if not admin:
        conn.execute("""INSERT INTO users
            (username, password_hash, role, created_at)
            VALUES (?, ?, 'admin', ?)""",
            (admin_name, generate_password_hash(admin_password), datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Administrator access is required.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_common():
    return {"current_user": session.get("username"), "current_role": session.get("role")}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            flash("Username must have at least 3 characters and password at least 8 characters.", "danger")
            return render_template("register.html")
        fields = [
            username, generate_password_hash(password), "participant",
            request.form.get("age", ""), request.form.get("gender", ""),
            request.form.get("education", ""), request.form.get("occupation", ""),
            request.form.get("location", ""), request.form.get("native_language", ""),
            request.form.get("musical_background", ""), request.form.get("years_training", ""),
            request.form.get("familiarity_music", ""), request.form.get("familiarity_raga", ""),
            request.form.get("listening_frequency", ""), datetime.now().isoformat(timespec="seconds")
        ]
        conn = get_db()
        try:
            conn.execute("""INSERT INTO users
                (username,password_hash,role,age,gender,education,occupation,location,native_language,
                 musical_background,years_training,familiarity_music,familiarity_raga,listening_frequency,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", fields)
            conn.commit()
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken. Please choose another.", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("admin") if user["role"] == "admin" else url_for("ragas"))
        flash("Incorrect username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/ragas")
@login_required
def ragas():
    if session.get("role") == "admin":
        return redirect(url_for("admin"))
    conn = get_db()
    rows = conn.execute("SELECT * FROM ragas ORDER BY name").fetchall()
    completed = {r["raga_id"] for r in conn.execute(
        "SELECT raga_id FROM annotations WHERE user_id = ?", (session["user_id"],)).fetchall()}
    conn.close()
    return render_template("ragas.html", ragas=rows, completed=completed)

@app.route("/listen/<int:raga_id>")
@login_required
def listen(raga_id):
    if session.get("role") != "participant":
        return redirect(url_for("admin"))
    conn = get_db()
    raga = conn.execute("SELECT * FROM ragas WHERE id = ?", (raga_id,)).fetchone()
    progress = conn.execute("SELECT listened_seconds FROM listening WHERE user_id=? AND raga_id=?",
                            (session["user_id"], raga_id)).fetchone()
    already = conn.execute("SELECT id FROM annotations WHERE user_id=? AND raga_id=?",
                           (session["user_id"], raga_id)).fetchone()
    conn.close()
    if not raga:
        flash("Raga not found.", "danger")
        return redirect(url_for("ragas"))
    return render_template("player.html", raga=raga,
                           listened_seconds=progress["listened_seconds"] if progress else 0,
                           already_annotated=bool(already), emotions=EMOTIONS)

@app.route("/api/listen-progress", methods=["POST"])
@login_required
def listen_progress():
    data = request.get_json(silent=True) or {}
    try:
        raga_id = int(data.get("raga_id"))
        seconds = int(data.get("seconds", 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Invalid progress data"), 400
    # A single browser update can add at most 10 seconds.
    seconds = max(0, min(seconds, 10))
    conn = get_db()
    exists = conn.execute("SELECT id FROM ragas WHERE id=?", (raga_id,)).fetchone()
    if not exists:
        conn.close()
        return jsonify(ok=False, error="Raga not found"), 404
    conn.execute("""INSERT INTO listening (user_id,raga_id,listened_seconds,updated_at)
        VALUES (?,?,?,?)
        ON CONFLICT(user_id,raga_id) DO UPDATE SET
        listened_seconds = listened_seconds + excluded.listened_seconds,
        updated_at = excluded.updated_at""",
        (session["user_id"], raga_id, seconds, datetime.now().isoformat(timespec="seconds")))
    total = conn.execute("SELECT listened_seconds FROM listening WHERE user_id=? AND raga_id=?",
                         (session["user_id"], raga_id)).fetchone()["listened_seconds"]
    conn.commit()
    conn.close()
    return jsonify(ok=True, total=total, unlocked=total >= 60)

@app.route("/submit-annotation/<int:raga_id>", methods=["POST"])
@login_required
def submit_annotation(raga_id):
    if session.get("role") != "participant":
        return redirect(url_for("admin"))
    conn = get_db()
    progress = conn.execute("SELECT listened_seconds FROM listening WHERE user_id=? AND raga_id=?",
                            (session["user_id"], raga_id)).fetchone()
    if not progress or progress["listened_seconds"] < 60:
        conn.close()
        flash("Please listen for at least one minute before submitting your ratings.", "warning")
        return redirect(url_for("listen", raga_id=raga_id))
    values = []
    try:
        for key, _, _ in EMOTIONS:
            value = int(request.form.get(key, "0"))
            if value < 0 or value > 4:
                raise ValueError
            values.append(value)
    except ValueError:
        conn.close()
        flash("Please choose a rating from 0 to 4 for every emotion.", "danger")
        return redirect(url_for("listen", raga_id=raga_id))
    try:
        conn.execute("""INSERT INTO annotations
            (user_id,raga_id,listened_seconds,sringara,hasya,karuna,raudra,vira,bhayanaka,bibhatsa,adbhuta,shanta,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [session["user_id"], raga_id, progress["listened_seconds"], *values,
             datetime.now().isoformat(timespec="seconds")])
        conn.commit()
        flash("Thank you! Your emotion ratings have been saved.", "success")
    except sqlite3.IntegrityError:
        flash("You have already submitted ratings for this raga.", "warning")
    finally:
        conn.close()
    return redirect(url_for("ragas"))

@app.route("/admin")
@admin_required
def admin():
    conn = get_db()
    participants = conn.execute("""SELECT id,username,age,gender,education,occupation,location,
        native_language,musical_background,years_training,familiarity_music,familiarity_raga,
        listening_frequency,created_at FROM users WHERE role='participant' ORDER BY id DESC""").fetchall()
    annotations = conn.execute("""SELECT a.*,u.username,r.name AS raga_name
        FROM annotations a JOIN users u ON a.user_id=u.id JOIN ragas r ON a.raga_id=r.id
        ORDER BY a.id DESC""").fetchall()
    ragas_list = conn.execute("SELECT * FROM ragas ORDER BY name").fetchall()
    total_listening = conn.execute("SELECT COUNT(*) FROM listening").fetchone()[0]
    conn.close()
    return render_template("admin.html", participants=participants, annotations=annotations,
                           ragas=ragas_list, total_listening=total_listening, emotions=EMOTIONS)

@app.route("/admin/add-raga", methods=["POST"])
@admin_required
def add_raga():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Raga name is required.", "danger")
        return redirect(url_for("admin"))
    audio = request.files.get("audio")
    filename = None
    if audio and audio.filename:
        safe = secure_filename(audio.filename)
        ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
        if ext not in ALLOWED_AUDIO:
            flash("Please upload an MP3, WAV, OGG or M4A audio file.", "danger")
            return redirect(url_for("admin"))
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe}"
        audio.save(os.path.join(AUDIO_DIR, filename))
    conn = get_db()
    conn.execute("""INSERT INTO ragas(name,thaat,performer,rendition_type,duration,audio_file,recording_info)
        VALUES(?,?,?,?,?,?,?)""",
        (name, request.form.get("thaat",""), request.form.get("performer",""),
         request.form.get("rendition_type","Instrumental"), request.form.get("duration","3+ minutes"),
         filename, request.form.get("recording_info","")))
    conn.commit()
    conn.close()
    flash("Raga record added.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/export.csv")
@admin_required
def export_csv():
    conn = get_db()
    rows = conn.execute("""SELECT u.username, u.age, u.gender, u.education, u.occupation,
        u.location, u.native_language, u.musical_background, u.years_training,
        u.familiarity_music, u.familiarity_raga, u.listening_frequency,
        r.name AS raga_name, a.listened_seconds, a.sringara, a.hasya, a.karuna,
        a.raudra, a.vira, a.bhayanaka, a.bibhatsa, a.adbhuta, a.shanta, a.created_at
        FROM annotations a JOIN users u ON a.user_id=u.id JOIN ragas r ON a.raga_id=r.id
        ORDER BY a.id""").fetchall()
    conn.close()
    output = StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow([row[k] for k in row.keys()])
    else:
        writer.writerow(["No annotations have been submitted yet"])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=raga_emotion_annotations.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


# Initialize database when the application starts
init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )


