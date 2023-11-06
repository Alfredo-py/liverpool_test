from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
db = SQLAlchemy(app)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.String(10), nullable=False)
    cancelation_date = db.Column(db.String(10))
    customer_name = db.Column(db.String(50), nullable=False)
    article_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'creation_date': self.creation_date,
            'cancelation_date': self.cancelation_date,
            'customer_name': self.customer_name,
            'article_name': self.article_name,
            'price': self.price,
            'quantity': self.quantity,
            'subtotal': self.price * self.quantity,
            'iva': (self.price * self.quantity) * 0.16,
            'total': (self.price * self.quantity) * 1.16
        }

# Create the database
with app.app_context():
    db.create_all()

# Route to create multiple sales orders
@app.route('/orders', methods=['POST'])
def create_orders():
    data = request.json

    if not data or not isinstance(data, list):
        return jsonify({'error': 'Invalid data format. Expected a list of products'}), 400

    created_orders = []

    for product_data in data:
        if 'customer_name' not in product_data or 'article_name' not in product_data or 'price' not in product_data or 'quantity' not in product_data:
            return jsonify({'error': 'Missing required fields in a product'}), 400

        if not isinstance(product_data['price'], (float, int)) or not isinstance(product_data['quantity'], int):
            return jsonify({'error': 'Price must be a number and quantity must be an integer'}), 400

        if product_data['price'] <= 0 or product_data['quantity'] <= 0:
            return jsonify({'error': 'Price and quantity must be positive numbers'}), 400

        existing_order = Order.query.filter_by(article_name=product_data['article_name']).first()
        if existing_order:
            product_data['price'] = existing_order.price

        order = Order(
            creation_date=datetime.now().strftime("%d/%m/%Y"),
            customer_name=product_data['customer_name'],
            article_name=product_data['article_name'],
            price=product_data['price'],
            quantity=product_data['quantity']
        )

        db.session.add(order)
        created_orders.append(order.to_dict())

    db.session.commit()
    return jsonify(created_orders), 201

# Route to retrieve sales orders
@app.route('/orders', methods=['GET'])
def get_orders():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            datetime.strptime(start_date, "%d/%m/%Y")
            datetime.strptime(end_date, "%d/%m/%Y")
        except ValueError:
            return jsonify({'error': 'Dates should be in the format dd/mm/yyyy'}), 400

    if start_date and end_date:
        orders = Order.query.filter(Order.creation_date >= start_date, Order.creation_date <= end_date).all()
    else:
        orders = Order.query.all()
    
    return jsonify([order.to_dict() for order in orders])

# Route to retrieve a sales order by ID
@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get(id)
    if not order:
        return jsonify({'error': 'Sales order not found'}), 404
    return jsonify(order.to_dict())

# Route to cancel a sales order by ID
@app.route('/orders/<int:id>', methods=['DELETE'])
def cancel_order(id):
    order = Order.query.get(id)
    if not order:
        return jsonify({'error': 'Sales order not found'}), 404
    
    if order.cancelation_date:
        return jsonify({'error': 'The sales order has already been canceled'}), 400
    
    order.cancelation_date = datetime.now().strftime("%d/%m/%Y")
    db.session.commit()
    return jsonify({'message': 'Sales order canceled successfully'})

if __name__ == '__main__':
    app.run(debug=True)
