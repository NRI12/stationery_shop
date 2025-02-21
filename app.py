from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
import stripe
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stationery_shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Stripe configuration
stripe.api_key = 'your_stripe_secret_key'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_login = db.Column(db.DateTime, nullable=True)
    
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def get_full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
    
    def update_profile(self, data):
        self.first_name = data.get('first_name', self.first_name)
        self.last_name = data.get('last_name', self.last_name)
        self.email = data.get('email', self.email)
        self.address = data.get('address', self.address)
        self.city = data.get('city', self.city)
        self.state = data.get('state', self.state)
        self.zip_code = data.get('zip_code', self.zip_code)
        self.phone = data.get('phone', self.phone)
        
        return self

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    def is_available(self, quantity=1):
        return self.stock >= quantity
    
    def reduce_stock(self, quantity):
        if self.is_available(quantity):
            self.stock -= quantity
            return True
        return False

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Create new user
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get_or_404(product_id)
    
    if not product.is_available(quantity):
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
    
    # Use session to manage cart
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    session.modified = True
    
    return jsonify({
        'success': True, 
        'cart_count': sum(cart.values()),
        'message': 'Product added to cart'
    })

@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total_price += item_total
    
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove-from-cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('index'))
    
    cart_items = []
    total_price = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total_price += item_total
    
    if request.method == 'POST':
        try:
            # Create Stripe Checkout Session
            line_items = [{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(item['total'] * 100),
                    'product_data': {
                        'name': item['product'].name,
                    },
                },
                'quantity': item['quantity'],
            } for item in cart_items]
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=url_for('order_success', _external=True),
                cancel_url=url_for('cart', _external=True)
            )
            
            # Create order
            order = Order(
                user_id=current_user.id,
                total_price=total_price,
                status='Pending'
            )
            db.session.add(order)
            
            # Create order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    quantity=item['quantity'],
                    price=item['total']
                )
                db.session.add(order_item)
                
                # Reduce product stock
                item['product'].reduce_stock(item['quantity'])
            
            db.session.commit()
            
            # Clear cart
            session['cart'] = {}
            session.modified = True
            
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            db.session.rollback()
            flash(f'Checkout error: {str(e)}', 'danger')
            return redirect(url_for('cart'))
    
    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

@app.route('/order-success')
def order_success():
    return render_template('order_success.html')

@app.route('/products')
def product_list():
    category = request.args.get('category')
    search_query = request.args.get('search')
    
    query = Product.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    
    products = query.all()
    categories = db.session.query(Product.category.distinct()).all()
    
    return render_template('products.html', 
                           products=products, 
                           categories=[c[0] for c in categories],
                           selected_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category=product.category).filter(Product.id != product_id).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    return render_template('search_results.html', products=products, query=query)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Update user profile
            current_user.update_profile({
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'address': request.form.get('address'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'zip_code': request.form.get('zip_code'),
                'phone': request.form.get('phone')
            })
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    return render_template('profile.html')

@app.route('/order-history')
@login_required
def order_history():
    # Fetch user's orders with related items
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Prepare order details with product information
    order_details = []
    for order in orders:
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        items_info = []
        
        for item in order_items:
            product = Product.query.get(item.product_id)
            items_info.append({
                'product': product,
                'quantity': item.quantity,
                'price': item.price
            })
        
        order_details.append({
            'order': order,
            'items': items_info
        })
    
    return render_template('order_history.html', order_details=order_details)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('change_password.html')

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)