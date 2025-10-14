from flask import Flask, render_template, jsonify
from flask import request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- Database config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    yes_price = db.Column(db.Float, default=50)
    no_price = db.Column(db.Float, default=50)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Market {self.question}>"

# --- Create database if not exists ---
with app.app_context():
    db.create_all()

# --- Routes ---
@app.route('/')
def home():
    markets = Market.query.all()
    return render_template('index.html', markets=markets)

@app.route('/api/markets')
def api_markets():
    markets = Market.query.all()
    return jsonify([
        {
            "id": m.id,
            "question": m.question,
            "yes": m.yes_price,
            "no": m.no_price,
            "category": m.category,
        }])

@app.route('/add', methods=['GET', 'POST'])
def add_market():
    SECRET_KEY = "pierogiadmin"  # change this later!
    key = request.args.get("key")
    if key != SECRET_KEY:
        abort(403)  # show a 403 Forbidden page if wrong key
    if request.method == 'POST':
        question = request.form['question']
        category = request.form['category']
        new_market = Market(question=question, category=category)
        db.session.add(new_market)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_market.html')

@app.route('/delete/<int:id>')
def delete_market(id):
    SECRET_KEY = "pierogiadmin"
    if request.args.get("key") != SECRET_KEY:
        abort(403)
    market = Market.query.get_or_404(id)
    db.session.delete(market)
    db.session.commit()
    return redirect(url_for('home'))
