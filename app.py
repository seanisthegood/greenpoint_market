
from flask import Flask, render_template, jsonify, request, redirect, url_for, abort, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'upersecretpierogi'  # Needed for session

# --- Database config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    points = db.Column(db.Integer, default=100)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.points} pts)>"

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


# --- User Registration & Login (with email and password) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        if not email or not password:
            return render_template('register.html', error='Email and password required')
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already registered')
        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username or user.email
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username or user.email
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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
    username = session.get('username')
    user_points = None
    is_admin = False
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user_points = user.points
            is_admin = getattr(user, 'is_admin', False)
    return render_template('index.html', markets=markets, username=username, user_points=user_points, is_admin=is_admin)



# --- RESTful API for Markets ---
from flask import make_response

@app.route('/api/markets', methods=['GET', 'POST'])
def api_markets():
    if request.method == 'GET':
        markets = Market.query.all()
        return jsonify([
            {
                "id": m.id,
                "question": m.question,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "category": m.category,
            } for m in markets
        ])
    elif request.method == 'POST':
        data = request.get_json()
        question = data.get('question')
        category = data.get('category', '')
        yes_price = data.get('yes_price')
        no_price = data.get('no_price')
        if not question or yes_price is None or no_price is None:
            return make_response(jsonify({'error': 'Missing required fields'}), 400)
        if yes_price + no_price <= 100:
            return make_response(jsonify({'error': 'The sum of Yes and No prices must be greater than 100 (spread required).'}), 400)
        market = Market(question=question, category=category, yes_price=yes_price, no_price=no_price)
        db.session.add(market)
        db.session.commit()
        return jsonify({
            "id": market.id,
            "question": market.question,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "category": market.category,
        }), 201

@app.route('/api/markets/<int:market_id>', methods=['GET', 'PUT', 'DELETE'])
def api_market_detail(market_id):
    market = Market.query.get_or_404(market_id)
    if request.method == 'GET':
        return jsonify({
            "id": market.id,
            "question": market.question,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "category": market.category,
        })
    elif request.method == 'PUT':
        data = request.get_json()
        market.question = data.get('question', market.question)
        market.category = data.get('category', market.category)
        yes_price = data.get('yes_price', market.yes_price)
        no_price = data.get('no_price', market.no_price)
        if yes_price + no_price <= 100:
            return make_response(jsonify({'error': 'The sum of Yes and No prices must be greater than 100 (spread required).'}), 400)
        market.yes_price = yes_price
        market.no_price = no_price
        db.session.commit()
        return jsonify({
            "id": market.id,
            "question": market.question,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "category": market.category,
        })
    elif request.method == 'DELETE':
        db.session.delete(market)
        db.session.commit()
        return jsonify({'message': 'Market deleted'})


# --- Admin-only Market Creation ---
@app.route('/create_market', methods=['GET', 'POST'])
def create_market():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_admin', False):
        abort(403)
    error = None
    if request.method == 'POST':
        question = request.form['question']
        category = request.form.get('category', '')
        try:
            yes_price = float(request.form.get('yes_price', 50))
            no_price = float(request.form.get('no_price', 50))
        except (TypeError, ValueError):
            error = 'Invalid price values.'
        else:
            if yes_price + no_price <= 100:
                error = 'The sum of Yes and No prices must be greater than 100 (spread required).'
            else:
                new_market = Market(question=question, category=category, yes_price=yes_price, no_price=no_price)
                db.session.add(new_market)
                db.session.commit()
                return redirect(url_for('home'))
    return render_template('create_market.html', error=error)

@app.route('/delete/<int:id>')
def delete_market(id):
    SECRET_KEY = "pierogiadmin"
    if request.args.get("key") != SECRET_KEY:
        abort(403)
    market = Market.query.get_or_404(id)
    db.session.delete(market)
    db.session.commit()
    return redirect(url_for('home'))
