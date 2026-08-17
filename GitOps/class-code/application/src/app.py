from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/healthz', methods=['GET'])
def health():
    return 200

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    
    # Extract data from request
    num1 = data.get('num1')
    num2 = data.get('num2')
    operation = data.get('operation')
    
    # Validate inputs
    if num1 is None or num2 is None or not operation:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        num1 = float(num1)
        num2 = float(num2)
    except ValueError:
        return jsonify({'error': 'Inputs must be numbers'}), 400

    # Perform calculation
    result = None
    if operation == 'add':
        result = num1 + num2
    elif operation == 'subtract':
        result = num1 - num2
    elif operation == 'multiply':
        result = num1 * num2
    elif operation == 'divide':
        if num2 == 0:
            return jsonify({'error': 'Cannot divide by zero'}), 400
        result = num1 / num2
    else:
        return jsonify({'error': 'Invalid operation'}), 400

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0' ,port=5000)
