import os
from flask import Flask, render_template
from adminpanel.views import adminpanel_bp

app = Flask(__name__)
# Secret key required for session-based admin auth.
# Override via environment variable in production.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dianisma-dev-secret-2024')

# Register the admin panel Blueprint (namespace: adminpanel, prefix: /admin)
app.register_blueprint(adminpanel_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/politiki')
def politiki():
    return render_template('politiki.html')

@app.route('/oikonomia')
def oikonomia():
    return render_template('oikonomia.html')

@app.route('/koinonia')
def koinonia():
    return render_template('koinonia.html')

@app.route('/analyseis')
def analyseis():
    return render_template('analyseis.html')

@app.route('/apopseis')
def apopseis():
    return render_template('apopseis.html')

@app.route('/dialogues')
def dialogues():
    return render_template('dialogues.html')

if __name__ == '__main__':
    app.run(debug=True)
