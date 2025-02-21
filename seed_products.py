from app import app, db, Product
from sqlalchemy.exc import IntegrityError

def seed_products():
    # Sample product categories
    products_data = [
        # Notebooks
        {
            'name': 'Classic Hardcover Notebook',
            'description': 'Premium hardcover notebook with high-quality paper. Perfect for journaling, note-taking, and sketching.',
            'price': 15.99,
            'category': 'Notebooks',
            'stock': 50,
            'image_url': '/static/images/notebook1.jpg'
        },
        {
            'name': 'Minimalist Softcover Notebook',
            'description': 'Sleek and lightweight softcover notebook with smooth, lined pages. Ideal for professionals and students.',
            'price': 12.50,
            'category': 'Notebooks',
            'stock': 75,
            'image_url': '/static/images/notebook2.jpg'
        },
        # Pens
        {
            'name': 'Luxury Ballpoint Pen Set',
            'description': 'Elegant ballpoint pen set with smooth writing experience. Comes in a gift box with multiple ink colors.',
            'price': 29.99,
            'category': 'Pens',
            'stock': 30,
            'image_url': '/static/images/pen1.jpg'
        },
        {
            'name': 'Gel Pen Collection',
            'description': 'Vibrant gel pen set with 12 unique colors. Perfect for creative writing and drawing.',
            'price': 18.75,
            'category': 'Pens',
            'stock': 60,
            'image_url': '/static/images/pen2.jpg'
        },
        # Pencils
        {
            'name': 'Professional Sketching Pencil Set',
            'description': 'High-quality graphite pencils with varying hardness levels. Ideal for artists and designers.',
            'price': 22.50,
            'category': 'Pencils',
            'stock': 40,
            'image_url': '/static/images/pencil1.jpg'
        },
        {
            'name': 'Mechanical Pencil with Extra Lead',
            'description': 'Precision mechanical pencil with extra lead refills. Smooth and consistent writing experience.',
            'price': 14.99,
            'category': 'Pencils',
            'stock': 55,
            'image_url': '/static/images/pencil2.jpg'
        },
        # Art Supplies
        {
            'name': 'Watercolor Paint Set',
            'description': 'Professional watercolor paint set with 24 vibrant colors. Includes high-quality brushes.',
            'price': 45.99,
            'category': 'Art Supplies',
            'stock': 25,
            'image_url': '/static/images/art1.jpg'
        },
        {
            'name': 'Colored Pencil Collection',
            'description': 'Premium colored pencils with rich, blendable colors. Perfect for artists and coloring enthusiasts.',
            'price': 34.50,
            'category': 'Art Supplies',
            'stock': 35,
            'image_url': '/static/images/art2.jpg'
        }
    ]

    with app.app_context():
        for product_data in products_data:
            existing_product = Product.query.filter_by(name=product_data['name']).first()
            if not existing_product:
                product = Product(**product_data)
                db.session.add(product)
        
        try:
            db.session.commit()
            print("Products seeded successfully!")
        except IntegrityError:
            db.session.rollback()
            print("Error seeding products. Some products might already exist.")

if __name__ == '__main__':
    seed_products()