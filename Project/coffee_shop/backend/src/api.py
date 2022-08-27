import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})


db_drop_and_create_all()

# AFTER REQUEST ORIGIN
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')

    return response


# ROUTES
# This endpoint displays all drinks does not need authorization
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks_query = Drink.query.order_by(Drink.id).all()        
        drinks = []

        for drink in drinks_query:
            drinks.append(drink.short())

        return jsonify({
            'success':True,
            'drinks': drinks
        }, 200)
    except: 
        abort(404)

#This endpoint displays drinks-details with authorization
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):
    try:
        drinks_query = Drink.query.order_by(Drink.id).all()
        drinks_details = [drink.long() for drink in drinks_query]
    
        return jsonify({
            'success':True,
            'drinks':drinks_details
        }, 200)
    except:
        abort(404)

# This endpoint creates a new drink with authorization
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def new_drink(payload):
    try:
        body = request.get_json()
        newTitle = body["title"]
        newRecipe = body["recipe"]
        # New Drink
        newDrink = Drink(title=newTitle, recipe=newRecipe) #cREATE NEW DRINK

        newDrink.insert()   #INSERT NEW DRINK TO DBS

        drink_query = Drink.query.order_by(Drink.id).all()
        return jsonify({
            'success':True,
            'drinks':[drink.long() for drink in drink_query]
        }, 200)
    except:
        abort(422)


# This endpoint implements patch drink with authorization
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload,drink_id):
    
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        body = request.get_json
        if drink is None:
            abort(404)
        if 'title' in  body:
            drink.title = body.get('title')
        elif 'recipe' in body:
            recipe = body.get('recipe')
            drink.recipe = json.dumps(recipe)

        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }, 200)
    except:
        abort(404)


# This endpoint implements delete with authorization
@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload,drink_id):
    try:
        drink = Drink.query.filter(Drink.id==drink_id).one_or_none

        if drink is None:
            abort(404)
        drink.delete()

        return jsonify({
            'success': True,
            'delete':drink_id
        }, 200)
    except:
        abort(404)



# Error Handling
# unprocesssable request error handler
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


# Bad request error handler
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False, 
        "error": 400, 
        "message": "bad request"
        }), 400
# Method not allowed error handler
@app.errorhandler(405)
def bad_request(error):
    return jsonify({
        "success": False, 
        "error": 405, 
        "message": "Method Not Allowed"
        }), 405

# Resource not found error handler
@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )

# Authentication error handler
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success':False,
        'error': error.status_code,
        'message': error.error
    }), error.status_code
    

