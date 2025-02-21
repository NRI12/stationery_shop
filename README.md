<<<<<<< HEAD
# ssssssss
=======
# Stationery Shop Web Application

## Features
- User Authentication (Register, Login, Logout)
- Product Browsing
- Shopping Cart
- Checkout with Stripe Integration
- Responsive Design

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Installation Steps
1. Clone the repository
2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
- Create a `.env` file
- Add Stripe keys and other configurations

5. Initialize the database
```bash
flask db upgrade
```

6. Run the application
```bash
python app.py
```

## Configuration
- Update Stripe keys in `app.py`
- Configure database connection
- Set up CORS and security settings

## Deployment
- Use gunicorn for production
- Set up NGINX or Apache as a reverse proxy
- Configure environment variables securely

## Technologies Used
- Flask
- SQLAlchemy
- Bootstrap
- Stripe
- Flask-Login
>>>>>>> 27d319a (beta)
