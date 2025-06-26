#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

# ---------------------------
# SIGNUP RESOURCE
# ---------------------------
class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")
        bio = data.get("bio")

        if not username or not password:
            return {"errors": ["Username and password are required."]}, 422

        try:
            user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }, 201
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username already exists."]}, 422
        except Exception as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422

# ---------------------------
# CHECK SESSION RESOURCE
# ---------------------------
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio
                }, 200
        return {"error": "Unauthorized"}, 401

# ---------------------------
# LOGIN RESOURCE
# ---------------------------
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }, 200
        return {"error": "Invalid username or password"}, 401

# ---------------------------
# LOGOUT RESOURCE
# ---------------------------
class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return {}, 204
        return {"error": "Unauthorized"}, 401

# ---------------------------
# RECIPE INDEX RESOURCE
# ---------------------------
class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {"error": "Unauthorized"}, 401
        recipes = Recipe.query.all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "instructions": r.instructions,
                "minutes_to_complete": r.minutes_to_complete,
                "user": {
                    "id": r.user.id,
                    "username": r.user.username,
                    "image_url": r.user.image_url,
                    "bio": r.user.bio
                }
            } for r in recipes
        ], 200

    def post(self):
        if not session.get('user_id'):
            return {"error": "Unauthorized"}, 401
        data = request.get_json()
        try:
            recipe = Recipe(
                title=data.get("title"),
                instructions=data.get("instructions"),
                minutes_to_complete=data.get("minutes_to_complete"),
                user_id=session['user_id']
            )
            db.session.add(recipe)
            db.session.commit()
            return {
                "id": recipe.id,
                "title": recipe.title,
                "instructions": recipe.instructions,
                "minutes_to_complete": recipe.minutes_to_complete,
                "user": {
                    "id": recipe.user.id,
                    "username": recipe.user.username,
                    "image_url": recipe.user.image_url,
                    "bio": recipe.user.bio
                }
            }, 201
        except Exception as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422

# Register resources with endpoints
api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')
