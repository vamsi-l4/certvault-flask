from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import secrets
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['rediron']
certificates_collection = db['certificates']

@app.route('/api/certs', methods=['POST'])
def create_cert():
    try:
        print("Raw request data:", request.data)
        data = request.get_json()
        print("Received data:", data)
        title = data.get('title')
        issuer = data.get('issuer', 'unknown')
        public_url = data.get('publicUrl')
        date = data.get('date')

        if not title or not public_url:
            return jsonify({'message': 'Title and publicUrl are required'}), 400

        short_id = secrets.token_hex(3)
        cert = {
            'title': title,
            'issuer': issuer,
            'date': date,
            'publicUrl': public_url,
            'shortId': short_id,
            'verified': False,
            'createdAt': datetime.now(timezone.utc)
        }
        result = certificates_collection.insert_one(cert)
        cert['_id'] = str(result.inserted_id)
        return jsonify(cert), 201
    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

@app.route('/api/certs', methods=['GET'])
def get_all_certs():
    try:
        certs = list(certificates_collection.find().sort('createdAt', -1))
        for cert in certs:
            cert['_id'] = str(cert['_id'])
        return jsonify(certs)
    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

@app.route('/api/certs/<id>', methods=['GET'])
def get_cert_by_id(id):
    try:
        from bson import ObjectId
        cert = certificates_collection.find_one({'_id': ObjectId(id)})
        if not cert:
            return jsonify({'message': 'Not found'}), 404
        cert['_id'] = str(cert['_id'])
        return jsonify(cert)
    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

@app.route('/api/certs/short/<short_id>', methods=['GET'])
def get_cert_by_short_id(short_id):
    try:
        cert = certificates_collection.find_one({'shortId': short_id})
        if not cert:
            return jsonify({'message': 'Not found'}), 404
        cert['_id'] = str(cert['_id'])
        return jsonify(cert)
    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

@app.route('/api/certs/<id>', methods=['PUT'])
def update_cert(id):
    try:
        from bson import ObjectId
        data = request.get_json()
        result = certificates_collection.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'message': 'Not found'}), 404
        updated_cert = certificates_collection.find_one({'_id': ObjectId(id)})
        updated_cert['_id'] = str(updated_cert['_id'])
        return jsonify(updated_cert)
    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

@app.route('/api/certs/<id>', methods=['DELETE'])
def delete_cert(id):
    try:
        from bson import ObjectId
        result = certificates_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'message': 'Not found'}), 404
        return jsonify({'message': 'Deleted'})
    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', debug=True, port=port)
