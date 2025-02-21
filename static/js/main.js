document.addEventListener('DOMContentLoaded', function() {
    // Cart functionality
    const cartButtons = document.querySelectorAll('.add-to-cart');
    
    cartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            const quantity = document.getElementById(`quantity-${productId}`).value;
            
            fetch('/add-to-cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Product added to cart!');
                    updateCartCount(data.cart_count);
                } else {
                    alert('Failed to add product to cart.');
                }
            });
        });
    });

    // Cart count update function
    function updateCartCount(count) {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = count;
        }
    }

    // Checkout process
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const stripe = Stripe('your_stripe_publishable_key');
            
            fetch('/create-checkout-session', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(session => {
                return stripe.redirectToCheckout({ sessionId: session.id });
            })
            .then(function(result) {
                if (result.error) {
                    alert(result.error.message);
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
            });
        });
    }
});