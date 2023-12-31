from fastapi import HTTPException,Security
import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime,timedelta

class AuthHandler():
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
    secret  = 'secret'

    def get_password_hash(self,password):
        return self.pwd_context.hash(password)
    
    def verify_password(self,plain_password,password):
        return self.pwd_context.verify(plain_password,password)

    def encode_token(self,user_id):
        payload = {
            'exp':datetime.utcnow()+timedelta(days=0,minutes=30),
            'iat':datetime.utcnow(),
            'sub':user_id
        }
    
    def decode_token(self,token):
        try:
            payload = jwt.decode(token,self.secret,algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(401,detail='Signature expired')
        except jwt.InvalidTokenError as e:
            raise HTTPException(401,detail='Invalid Token')
    
    def auth_wrapper(self,auth:HTTPAuthorizationCredentials=Security(security)):
        return self.decode_token(auth.credentials)












