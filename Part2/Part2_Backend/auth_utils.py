# auth_utils.py
from jose import jwt
import requests

COGNITO_REGION = 'us-east-1'
USER_POOL_ID = 'us-east-1_Bep0PJNNp'
APP_CLIENT_ID = '6s0tgt4tnp6s02o1j8tmhgqnem'
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

jwks = requests.get(JWKS_URL).json()

def get_public_key(kid):
    for key in jwks['keys']:
        if key['kid'] == kid:
            return key
    raise Exception('Public key not found.')

def verify_token(token):
    headers = jwt.get_unverified_header(token)
    key = get_public_key(headers['kid'])
    return jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        audience=APP_CLIENT_ID,
        issuer=COGNITO_ISSUER
    )
