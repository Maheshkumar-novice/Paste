import os
import secrets
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For flash messages
DB_PATH = "pastes_simple.db"


def init_db():
    """Initialize the SQLite database with the pastes table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS pastes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            password TEXT
        )
        """)


def generate_paste_id(length=8):
    """Generate a random paste ID."""
    return secrets.token_urlsafe(length)[:length]


@app.route("/")
def index():
    """Display the home page with recent pastes."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
        SELECT id, title, created_at 
        FROM pastes 
        WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP 
        ORDER BY created_at DESC 
        LIMIT 10
        """)
        recent_pastes = cursor.fetchall()
    return render_template("index.html", recent_pastes=recent_pastes)


@app.route("/paste", methods=["POST"])
def create_paste():
    """Create a new paste."""
    content = request.form.get("content")
    title = request.form.get("title", "Untitled")
    password = request.form.get("password")

    if not content:
        flash("Paste content cannot be empty!", "error")
        return redirect(url_for("index"))

    paste_id = generate_paste_id()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO pastes (id, content, title, password) VALUES (?, ?, ?, ?)",
            (paste_id, content, title, password),
        )

    flash("Paste created successfully!", "success")
    return redirect(url_for("view_paste", paste_id=paste_id))


@app.route("/paste/<paste_id>")
def view_paste(paste_id):
    """View a specific paste."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT content, title, created_at, password FROM pastes WHERE id = ?",
            (paste_id,),
        )
        paste = cursor.fetchone()

    if not paste:
        flash("Paste not found!", "error")
        return redirect(url_for("index"))

    content, title, created_at, has_password = paste
    if has_password and request.args.get("password") != has_password:
        return render_template("password.html", paste_id=paste_id)

    return render_template(
        "view.html",
        content=content,
        title=title,
        created_at=created_at,
        paste_id=paste_id,
    )


# Templates directory structure:
# templates/
#   ├── base.html
#   ├── index.html
#   ├── view.html
#   └── password.html

# Create the templates directory
if not os.path.exists("templates"):
    os.makedirs("templates")

# base.html template
base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Personal Pastebin{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">Personal Pastebin</a>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# index.html template
index_html = """
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <h2>Create New Paste</h2>
        <form method="POST" action="{{ url_for('create_paste') }}">
            <div class="mb-3">
                <label for="title" class="form-label">Title</label>
                <input type="text" class="form-control" id="title" name="title" placeholder="Optional title">
            </div>
            <div class="mb-3">
                <label for="content" class="form-label">Content</label>
                <textarea class="form-control" id="content" name="content" rows="10" required></textarea>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password (optional)</label>
                <input type="password" class="form-control" id="password" name="password">
            </div>
            <button type="submit" class="btn btn-primary">Create Paste</button>
        </form>
    </div>
    
    <div class="col-md-4">
        <h2>Recent Pastes</h2>
        {% if recent_pastes %}
            <ul class="list-group">
            {% for paste_id, title, created_at in recent_pastes %}
                <li class="list-group-item">
                    <a href="{{ url_for('view_paste', paste_id=paste_id) }}">
                        {{ title or 'Untitled' }}
                    </a>
                    <br>
                    <small class="text-muted">{{ created_at }}</small>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No recent pastes.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
"""

# view.html template
view_html = """
{% extends "base.html" %}

{% block title %}{{ title }} - Personal Pastebin{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2>{{ title or 'Untitled' }}</h2>
        <p class="text-muted">Created: {{ created_at }}</p>
        <div class="card">
            <div class="card-body">
                <pre><code>{{ content }}</code></pre>
            </div>
        </div>
        <div class="mt-3">
            <a href="{{ url_for('index') }}" class="btn btn-secondary">Back to Home</a>
        </div>
    </div>
</div>
{% endblock %}
"""

# password.html template
password_html = """
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-6 offset-md-3">
        <h2>Password Protected Paste</h2>
        <form method="GET">
            <div class="mb-3">
                <label for="password" class="form-label">Enter Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Access Paste</button>
        </form>
    </div>
</div>
{% endblock %}
"""

# Write templates to files
with open("templates/base.html", "w") as f:
    f.write(base_html)
with open("templates/index.html", "w") as f:
    f.write(index_html)
with open("templates/view.html", "w") as f:
    f.write(view_html)
with open("templates/password.html", "w") as f:
    f.write(password_html)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
