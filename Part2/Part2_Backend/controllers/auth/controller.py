from flask import jsonify


from database.models import User

from database import session_scope
from database.crud import get_first_or_none
from database.crud import create_user


def verify_user_entry(user_id, email):
    try:
        with session_scope() as session:
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
