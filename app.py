from flask import Flask, render_template, jsonify
from flask import request, redirect, url_for, abort, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'  # Needed for session

# --- Database config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    points = db.Column(db.Integer, default=100)

    def __repr__(self):
        return f"<User {self.username} ({self.points} pts)>"

class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    yes_price = db.Column(db.Float, default=50)
    no_price = db.Column(db.Float, default=50)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Market {self.question}>"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    outcome = db.Column(db.String(3), nullable=False)  # 'yes' or 'no'
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('purchases', lazy=True))
    market = db.relationship('Market', backref=db.backref('purchases', lazy=True))

    def __repr__(self):
        return f"<Purchase {self.user_id} {self.market_id} {self.outcome} {self.amount}>"

# --- Create database if not exists ---
with app.app_context():
    db.create_all()

# --- User Registration & Login (simple, no password) ---
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'message': 'Registered', 'user_id': user.id, 'points': user.points})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    session['user_id'] = user.id
    return jsonify({'message': 'Logged in', 'user_id': user.id, 'points': user.points})

# --- Buy Yes/No Shares ---
@app.route('/buy', methods=['POST'])
def buy():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    market_id = request.form.get('market_id', type=int)
    outcome = request.form.get('outcome')  # 'yes' or 'no'
    amount = request.form.get('amount', type=int)
    if not market_id or outcome not in ('yes', 'no') or not amount or amount <= 0:
        return jsonify({'error': 'Invalid input'}), 400
    market = Market.query.get(market_id)
    if not market:
        return jsonify({'error': 'Market not found'}), 404
    if user.points < amount:
        return jsonify({'error': 'Not enough points'}), 400
    # Deduct points and record purchase
    user.points -= amount
    purchase = Purchase(user_id=user.id, market_id=market.id, outcome=outcome, amount=amount)
    # Optionally update price (simple: +0.1 per point spent)
    if outcome == 'yes':
        market.yes_price += 0.1 * amount
    else:
        market.no_price += 0.1 * amount
    db.session.add(purchase)
    db.session.commit()
    return jsonify({'message': f'Bought {amount} {outcome} on market {market.id}', 'points': user.points, 'yes_price': market.yes_price, 'no_price': market.no_price})
from flask import Flask, render_template, jsonify
from flask import request, redirect, url_for, abort, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'  # Needed for session

# --- Database config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    points = db.Column(db.Integer, default=100)

    def __repr__(self):
        return f"<User {self.username} ({self.points} pts)>"

class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    yes_price = db.Column(db.Float, default=50)
    no_price = db.Column(db.Float, default=50)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Market {self.question}>"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    outcome = db.Column(db.String(3), nullable=False)  # 'yes' or 'no'
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('purchases', lazy=True))
    market = db.relationship('Market', backref=db.backref('purchases', lazy=True))

    def __repr__(self):
        return f"<Purchase {self.user_id} {self.market_id} {self.outcome} {self.amount}>"


# --- Create database if not exists ---
with app.app_context():
    db.create_all()

# --- User Registration & Login (simple, no password) ---
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'message': 'Registered', 'user_id': user.id, 'points': user.points})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    session['user_id'] = user.id
    return jsonify({'message': 'Logged in', 'user_id': user.id, 'points': user.points})

# --- Buy Yes/No Shares ---
@app.route('/buy', methods=['POST'])
def buy():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    market_id = request.form.get('market_id', type=int)
    outcome = request.form.get('outcome')  # 'yes' or 'no'
    amount = request.form.get('amount', type=int)
    if not market_id or outcome not in ('yes', 'no') or not amount or amount <= 0:
        return jsonify({'error': 'Invalid input'}), 400
    market = Market.query.get(market_id)
    if not market:
        return jsonify({'error': 'Market not found'}), 404
    if user.points < amount:
        return jsonify({'error': 'Not enough points'}), 400
    # Deduct points and record purchase
    user.points -= amount
    purchase = Purchase(user_id=user.id, market_id=market.id, outcome=outcome, amount=amount)
    # Optionally update price (simple: +0.1 per point spent)
    if outcome == 'yes':
        market.yes_price += 0.1 * amount
    else:
        market.no_price += 0.1 * amount
    db.session.add(purchase)
    db.session.commit()
    return jsonify({'message': f'Bought {amount} {outcome} on market {market.id}', 'points': user.points, 'yes_price': market.yes_price, 'no_price': market.no_price})

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
        } for m in markets
    ])

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
