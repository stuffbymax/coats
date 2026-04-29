from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
import os
import click
from flask.cli import with_appcontext

app = Flask(__name__)
DB_PATH = "coats_of_arms.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    # Drop the table if it exists to ensure a clean slate on init
    c.execute("DROP TABLE IF EXISTS coats_of_arms")
    c.execute("""
        CREATE TABLE coats_of_arms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            motto_latin TEXT,
            motto_english TEXT,
            motto_other TEXT,
            colors TEXT,
            symbols TEXT,
            shield_shape TEXT,
            created_at TEXT,
            designer TEXT,
            image TEXT,
            description TEXT,
            usage_official_documents INTEGER DEFAULT 0,
            usage_flags INTEGER DEFAULT 0,
            usage_seal INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def seed_db(json_data):
    conn = get_db()
    c = conn.cursor()

    for item in json_data.get("coatOfArms", []):
        motto = item.get("motto", {})
        usage = item.get("usage", {})
        colors = json.dumps(item.get("colors", []))
        symbols = json.dumps(item.get("symbols", []))

        # Build motto_other from any non-latin/english keys
        other_keys = {k: v for k, v in motto.items() if k not in ("latin", "english")}
        motto_other = json.dumps(other_keys) if other_keys else None

        c.execute("""
            INSERT INTO coats_of_arms
            (name, motto_latin, motto_english, motto_other, colors, symbols,
             shield_shape, created_at, designer, image, description,
             usage_official_documents, usage_flags, usage_seal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("name", ""),
            motto.get("latin", ""),
            motto.get("english", ""),
            motto_other,
            colors,
            symbols,
            item.get("shieldShape", ""),
            str(item.get("createdAt", "")),
            item.get("designer", ""),
            item.get("image", ""),
            item.get("description", ""),
            1 if usage.get("officialDocuments") else 0,
            1 if usage.get("flags") else 0,
            1 if usage.get("seal") else 0,
        ))

    conn.commit()
    conn.close()


# ── Database Command ──────────────────────────────────────────────────

@app.cli.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables, then seed with data.json."""
    # First, initialize the schema
    init_db()
    click.echo("Initialized the database.")

    # Then, load and seed from JSON
    json_file = "data.json"
    if os.path.exists(json_file):
        with open(json_file) as f:
            seed_db(json.load(f))
            click.echo("Seeded the database from data.json.")
    else:
        click.echo("data.json not found. Database seeded empty.")


# ── Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_db()
    search = request.args.get("q", "").strip()
    if search:
        rows = conn.execute(
            "SELECT * FROM coats_of_arms WHERE name LIKE ? ORDER BY name",
            (f"%{search}%",)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM coats_of_arms ORDER BY name").fetchall()
    conn.close()
    return render_template("index.html", items=rows, search=search)


@app.route("/item/<int:item_id>")
def detail(item_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM coats_of_arms WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not row:
        return redirect(url_for("index"))
    
    # Safely load JSON strings, providing default empty lists if None or invalid
    try:
        colors = json.loads(row["colors"]) if row["colors"] else []
    except (json.JSONDecodeError, TypeError):
        colors = []
        
    try:
        symbols = json.loads(row["symbols"]) if row["symbols"] else []
    except (json.JSONDecodeError, TypeError):
        symbols = []

    return render_template("detail.html", item=row, colors=colors, symbols=symbols)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        d = request.form
        conn = get_db()
        conn.execute("""
            INSERT INTO coats_of_arms
            (name, motto_latin, motto_english, colors, symbols, shield_shape,
             created_at, designer, image, description,
             usage_official_documents, usage_flags, usage_seal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d.get("name", ""),
            d.get("motto_latin", ""),
            d.get("motto_english", ""),
            json.dumps([c.strip() for c in d.get("colors", "").split(",") if c.strip()]),
            "[]",  # Symbols are not handled in the add form yet
            d.get("shield_shape", ""),
            d.get("created_at", ""),
            d.get("designer", ""),
            d.get("image", ""),
            d.get("description", ""),
            1 if d.get("usage_official_documents") else 0,
            1 if d.get("usage_flags") else 0,
            1 if d.get("usage_seal") else 0,
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add.html")


@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit(item_id):
    conn = get_db()
    if request.method == "POST":
        d = request.form
        conn.execute("""
            UPDATE coats_of_arms SET
            name=?, motto_latin=?, motto_english=?, colors=?, shield_shape=?,
            created_at=?, designer=?, image=?, description=?,
            usage_official_documents=?, usage_flags=?, usage_seal=?
            WHERE id=?
        """, (
            d.get("name", ""),
            d.get("motto_latin", ""),
            d.get("motto_english", ""),
            json.dumps([c.strip() for c in d.get("colors", "").split(",") if c.strip()]),
            d.get("shield_shape", ""),
            d.get("created_at", ""),
            d.get("designer", ""),
            d.get("image", ""),
            d.get("description", ""),
            1 if d.get("usage_official_documents") else 0,
            1 if d.get("usage_flags") else 0,
            1 if d.get("usage_seal") else 0,
            item_id,
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("detail", item_id=item_id))

    row = conn.execute("SELECT * FROM coats_of_arms WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not row:
        return redirect(url_for("index"))
    
    # Safely load colors for display in the edit form
    try:
        colors = json.loads(row["colors"]) if row["colors"] else []
    except (json.JSONDecodeError, TypeError):
        colors = []
        
    return render_template("edit.html", item=row, colors=colors)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    conn = get_db()
    conn.execute("DELETE FROM coats_of_arms WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# ── API endpoints ────────────────────────────────────────────────────────

@app.route("/api/items")
def api_items():
    conn = get_db()
    rows = conn.execute("SELECT * FROM coats_of_arms ORDER BY name").fetchall()
    conn.close()
    result = []
    for r in rows:
        # Convert row object to a dictionary for easier manipulation
        item = dict(r)
        
        # Safely parse JSON fields
        try:
            item["colors"] = json.loads(item["colors"]) if item["colors"] else []
        except (json.JSONDecodeError, TypeError):
            item["colors"] = []
            
        try:
            item["symbols"] = json.loads(item["symbols"]) if item["symbols"] else []
        except (json.JSONDecodeError, TypeError):
            item["symbols"] = []
            
        try:
            item["motto_other"] = json.loads(item["motto_other"]) if item["motto_other"] else {}
        except (json.JSONDecodeError, TypeError):
            item["motto_other"] = {}

        result.append(item)
        
    return jsonify(result)


@app.route("/api/items/<int:item_id>")
def api_item(item_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM coats_of_arms WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    
    # Convert row to dict and parse JSON fields for a clean API response
    item = dict(row)
    try:
        item["colors"] = json.loads(item["colors"]) if item["colors"] else []
    except (json.JSONDecodeError, TypeError):
        item["colors"] = []
    try:
        item["symbols"] = json.loads(item["symbols"]) if item["symbols"] else []
    except (json.JSONDecodeError, TypeError):
        item["symbols"] = []

    return jsonify(item)


@app.route("/api/items", methods=["POST"])
def api_create_item():
    # A more complete API create that handles more fields from a potential JSON payload
    data = request.json
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO coats_of_arms (
            name, motto_latin, motto_english, motto_other, colors, symbols,
            shield_shape, created_at, designer, image, description,
            usage_official_documents, usage_flags, usage_seal
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name"),
        data.get("motto", {}).get("latin"),
        data.get("motto", {}).get("english"),
        json.dumps(data.get("motto_other", {})),
        json.dumps(data.get("colors", [])),
        json.dumps(data.get("symbols", [])),
        data.get("shield_shape"),
        data.get("created_at"),
        data.get("designer"),
        data.get("image"),
        data.get("description"),
        1 if data.get("usage", {}).get("officialDocuments") else 0,
        1 if data.get("usage", {}).get("flags") else 0,
        1 if data.get("usage", {}).get("seal") else 0,
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"id": new_id, "message": "Item created successfully"}), 201


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def api_update_item(item_id):
    # A more complete API update
    data = request.json
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    conn = get_db()
    # Check if item exists
    item = conn.execute("SELECT id FROM coats_of_arms WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    conn.execute("""
        UPDATE coats_of_arms SET
        name=?, motto_latin=?, motto_english=?, colors=?, shield_shape=?,
        created_at=?, designer=?, image=?, description=?,
        usage_official_documents=?, usage_flags=?, usage_seal=?
        WHERE id=?
    """, (
        data.get("name"),
        data.get("motto", {}).get("latin"),
        data.get("motto", {}).get("english"),
        json.dumps(data.get("colors", [])),
        data.get("shield_shape"),
        data.get("created_at"),
        data.get("designer"),
        data.get("image"),
        data.get("description"),
        1 if data.get("usage", {}).get("officialDocuments") else 0,
        1 if data.get("usage", {}).get("flags") else 0,
        1 if data.get("usage", {}).get("seal") else 0,
        item_id,
    ))
    conn.commit()
    conn.close()

    return jsonify({"status": "updated", "id": item_id})


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    conn = get_db()
    conn.execute("DELETE FROM coats_of_arms WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


# We no longer run the init/seed logic here.
# It is now handled by the 'flask init-db' command.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
