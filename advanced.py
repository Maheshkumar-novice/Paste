import os
import secrets
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For flash messages
DB_PATH = "pastes_advanced.db"


def init_db():
    """Initialize the SQLite database with the pastes table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS pastes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            title TEXT,
            language TEXT DEFAULT 'plaintext',
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
    language = request.form.get("language", "plaintext")

    if not content:
        flash("Paste content cannot be empty!", "danger")
        return redirect(url_for("index"))

    paste_id = generate_paste_id()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO pastes (id, content, title, password, language) VALUES (?, ?, ?, ?, ?)",
            (paste_id, content, title, password, language),
        )

    flash("Paste created successfully!", "success")
    return redirect(url_for("view_paste", paste_id=paste_id))


@app.route("/paste/<paste_id>")
def view_paste(paste_id):
    """View a specific paste."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT content, title, created_at, password, language FROM pastes WHERE id = ?",
            (paste_id,),
        )
        paste = cursor.fetchone()

    if not paste:
        flash("Paste not found!", "danger")
        return redirect(url_for("index"))

    content, title, created_at, has_password, language = paste
    if has_password and request.args.get("password") != has_password:
        return render_template("password.html", paste_id=paste_id)

    return render_template(
        "view.html",
        content=content,
        title=title,
        created_at=created_at,
        paste_id=paste_id,
        language=language,
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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-okaidia.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/monokai.min.css" rel="stylesheet">
    <style>
        .CodeMirror {
            height: auto;
            min-height: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/javascript/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/css/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/clike/clike.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/sql/sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/shell/shell.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/yaml/yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/edit/matchbrackets.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/edit/closebrackets.min.js"></script>
    <!-- Keep existing Prism components for viewing -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-java.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-cpp.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-csharp.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
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
                <label for="language" class="form-label">Language</label>
                <select class="form-select" id="language" name="language">
                    <option value="plaintext">Plain Text</option>
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="css">CSS</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                    <option value="csharp">C#</option>
                    <option value="sql">SQL</option>
                    <option value="bash">Bash</option>
                    <option value="yaml">YAML</option>
                    <option value="json">JSON</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="content" class="form-label">Content</label>
                <textarea class="form-control" id="content" name="content" rows="10"></textarea>
            </div>
            <script>
                // Wait for the DOM and scripts to be fully loaded
                document.addEventListener('DOMContentLoaded', function() {
                    // Make sure CodeMirror is loaded
                    if (typeof CodeMirror !== 'undefined') {
                        initializeEditor();
                    } else {
                        // If CodeMirror isn't loaded yet, wait a bit and try again
                        setTimeout(initializeEditor, 1000);
                    }
                });

                function initializeEditor() {
                    // Check again if CodeMirror is available
                    if (typeof CodeMirror === 'undefined') {
                        console.error('CodeMirror failed to load');
                        return;
                    }

                    // Initialize CodeMirror
                    var editor = CodeMirror.fromTextArea(document.getElementById("content"), {
                        lineNumbers: true,
                        theme: "monokai",
                        mode: "plaintext",
                        matchBrackets: true,
                        autoCloseBrackets: true,
                        indentUnit: 4,
                        indentWithTabs: false
                    });

                    // Map language selections to CodeMirror modes
                    const languageModes = {
                        'plaintext': 'plaintext',
                        'python': 'python',
                        'javascript': 'javascript',
                        'css': 'css',
                        'java': 'text/x-java',
                        'cpp': 'text/x-c++src',
                        'csharp': 'text/x-csharp',
                        'sql': 'sql',
                        'bash': 'shell',
                        'yaml': 'yaml',
                        'json': { name: 'javascript', json: true }
                    };

                    // Update editor mode when language is changed
                    document.getElementById('language').addEventListener('change', function() {
                        const mode = languageModes[this.value] || 'plaintext';
                        editor.setOption('mode', mode);
                    });

                    // Ensure form submission includes the editor content
                    document.querySelector('form').addEventListener('submit', function() {
                        editor.save();
                    });
                }
            </script>
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
            <div class="card-header d-flex justify-content-between">
                <p class="text-muted">{{ language }}</p>
                <button class="btn btn-sm btn-secondary" onclick="copyContent()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-clipboard me-1" viewBox="0 0 16 16">
                        <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                        <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                    </svg>
                    Copy
                </button>
            </div>
            <div class="card-body">
                <pre class="line-numbers"><code class="language-{{ language }}">{{ content }}</code></pre>
            </div>
        </div>
        <div class="mt-3">
            <a href="{{ url_for('index') }}" class="btn btn-secondary">Back to Home</a>
        </div>
    </div>
</div>

<script>
function copyContent() {
    // Get the content from the code element
    const codeElement = document.querySelector('pre code');
    const textToCopy = codeElement.textContent;
    
    // Copy to clipboard
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Change button text temporarily to show success
        const button = document.querySelector('button');
        const originalHTML = button.innerHTML;
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-lg me-1" viewBox="0 0 16 16">
                <path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z"/>
            </svg>
            Copied!
        `;
        
        // Reset button text after 2 seconds
        setTimeout(() => {
            button.innerHTML = originalHTML;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        alert('Failed to copy text to clipboard');
    });
}
</script>
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
