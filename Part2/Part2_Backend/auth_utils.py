# auth_utils.py
from flask import jsonify
from jose import jwt
import requests
import time

from exception_templates.auth_exception import MissingTokenError
from exception_templates.auth_exception import TokenVerificationError

# Constants
COGNITO_REGION = 'us-east-1'
USER_POOL_ID = 'us-east-1_Bep0PJNNp'
APP_CLIENT_ID = '6s0tgt4tnp6s02o1j8tmhgqnem'
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

# Cache
_jwks_cache = None
_jwks_last_fetch_time = 0
JWKS_REFRESH_INTERVAL = 3600  # 1 hour (in seconds)

def fetch_jwks(force=False):
    global _jwks_cache, _jwks_last_fetch_time
    now = time.time()

    # Only fetch if cache is stale or force refresh
    if _jwks_cache is None or force or (now - _jwks_last_fetch_time > JWKS_REFRESH_INTERVAL):
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_last_fetch_time = now

    return _jwks_cache

def get_public_key(kid):
    jwks = fetch_jwks()

    for key in jwks['keys']:
        if key['kid'] == kid:
            return key

    # If the key was not found, refresh and try again once
    jwks = fetch_jwks(force=True)
    for key in jwks['keys']:
        if key['kid'] == kid:
            return key

    raise Exception('Public key not found after refresh.')

def verify_token(token, access_token=None):
    try:
        headers = jwt.get_unverified_header(token)
        key = get_public_key(headers['kid'])
    except Exception:
        raise TokenVerificationError()
    options = {"verify_at_hash": bool(access_token)}
    return jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        audience=APP_CLIENT_ID,
        issuer=COGNITO_ISSUER,
        access_token=access_token,
        options=options
    )


def authenticate_user(request):
    auth_header = request.headers.get('Authorization', '')
    access_token = auth_header.replace('Bearer ', '')
    id_token = request.headers.get('X-ID-Token', '')
    if not access_token:
        raise MissingTokenError()
    try:
        access_claims = verify_token(access_token)
        id_claims = None
        if id_token:
            id_claims = verify_token(id_token, access_token=access_token)
    except TokenVerificationError:
        raise TokenVerificationError()
    return access_claims, id_claims
