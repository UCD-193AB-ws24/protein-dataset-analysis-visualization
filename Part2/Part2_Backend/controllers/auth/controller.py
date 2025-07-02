from flask import jsonify


from database.models import Base, User, Group, File

from database import session_scope
from database.crud import get_first_or_none
from database.crud import create_user


from auth_utils import verify_token


def login(username, password):
    try:
        with session_scope() as session:
            user = get_first_or_none(session, User, username=username)
            if user and user.password_hash == password:
                return jsonify({"msg": "login success"}), 200
            else:
                return jsonify({"msg": "login failed"}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def verify(access_token, id_token=None):
    try:
        with session_scope() as session:
            access_claims = verify_token(access_token)
            user_id = access_claims['sub']

            id_claims = None
            email = None
            if id_token:
                id_claims = verify_token(id_token, access_token=access_token)
                email = id_claims['email']

            #check if user exists
            user = get_first_or_none(session, User, id=user_id)
            #if not, create new user
            if not user:
                user = create_user(session, user_id, email)

            return jsonify({
                'message': 'Hello, authenticated user!',
                'user': {
                    'id': user_id,
                    'email': email,
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 401
