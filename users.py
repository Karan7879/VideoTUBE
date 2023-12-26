from pydantic import BaseModel
from dbconfig import dbusers
from fastapi import  HTTPException,Depends
from bson import ObjectId
from typing import  List,Annotated
from datetime import datetime
from fastapi import  APIRouter, status
from passlib.context import CryptContext
#     montization
from fastapi import HTTPException,Security
# import jwt
from jose import JWTError,jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime,timedelta
import secrets

secret_key = 'secret'
algorith = 'HS256'
bcrypt_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/login')

class Token(BaseModel):
    access_token:str
    token_type:str

class Creator(BaseModel):
    channel_name: str
    channel_link: str = None
    channel_description: str 
    channel_profile_picture: str = None
    monetization_info: dict =None   # You might customize this based on your needs
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    social_media_links: dict = {}  # You might customize this based on your needs
    creation_date: str =None # You might use a datetime field for this

class History(BaseModel):
    video_link: str
    timestamp: datetime

class Liked(BaseModel):
    video_link: str
    timestamp: datetime

class User(BaseModel):
    name: str
    email: str
    password: str
    premium_member: bool =  False
    history: List[History] = []
    liked: List[Liked] = []
    creator_info: Creator = None

    def create_users(self):
        user_dict = self.model_dump()

        if dbusers.find_one({'email':self.email}):
            raise HTTPException(status_code=400,detail='User already exist')
        result = dbusers.insert_one(user_dict)
        if result:
            return {**user_dict, "_id": str(result.inserted_id)}
        else:
            return {'Fail to add'}

    def creatorsInfo(self,creator:Creator,email:str):
        if not self.creator_info:
            dbusers.update_one(
                {'email': email},
                {'$push':creator}
            )
        else:
            return 'channel exist'
    @classmethod
    def getUsers(cls,email:str):
        user = dbusers.find_one({"email": email})
        if user:
            return {**user, "_id": str(user["_id"])}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    @classmethod
    def updatePremiumUsers(cls,user_id: str, update_data: dict):
    # Define a list of sensitive fields that should not be updated
        sensitive_fields = ["email", "password"]

        # Check if any sensitive fields are present in the update data
        if any(field in sensitive_fields for field in update_data):
            raise HTTPException(status_code=400, detail="Update of sensitive fields not allowed")

        # Prepare the update operation using $set for other fields
        update_operation = {"$set": update_data}

        # Perform the find_one_and_update operation
        updated_user = dbusers.find_one_and_update(
            {"_id": ObjectId(user_id)},
            update_operation,
            return_document=True  # Return the updated document
        )

        # Check if the document was found and updated
        if updated_user:
            return updated_user
        else:
            raise HTTPException(status_code=404, detail="User not found")

    def addHistory(self,video_id,email):
        timestamp = datetime.utcnow()
        result = dbusers.update_one(
            {"email": email},
            {"$push": {"history": {"video_id": video_id, "timestamp": timestamp}}},
        )
        # db[USERS_COLLECTION].update(
        #     {"email": email}, "history.video_link": video_id},
        #     {
        # $addToSet: {
        #     videos: {
        # $each: [{'video_id': "existingVideoID", 'timestamp': timestamp}],
        # $sort: {timestamp: -1},
        # $slice: 1
        # }
        # }
        # }
        # )

        if result.modified_count > 0:
            print("Video added to watch history")
        else:
            print("Failed to add video to watch history")

    def addLiked(self,video_id,email):
        timestamp = datetime.utcnow()
        query = {"email": email, "liked.video_link": video_id}
        existing = dbusers.find_one(query)
        update_operationID = {"email": email}
        if existing:
            dbusers.update_one(update_operationID,{
            "$pull": {"liked": {"video_link": video_id}},
        })
        else:
           dbusers.update_one(update_operationID,{
                "$addToSet": {"liked": {"video_link": video_id, "timestamp": timestamp}},
            })





usersRoute = APIRouter(tags=['Users'])


@usersRoute.post('/v1/CreateUser/')
def createUsers(user:User):
        user = user.model_dump()
        
        if dbusers.find_one({'email':user['email']}):
            raise HTTPException(status_code=400,detail='User already exist')
        user['password'] = bcrypt_context.hash(user['password'])
        result = dbusers.insert_one(user)
        if result:
            return {**user, "_id": str(result.inserted_id)}
        else:
            return {'Fail to add'}


# def create_access_token(data: dict, expires_delta: timedelta):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = timedelta(minutes=expires_delta)
#         to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorith)
#     return encoded_jwt

def create_jwt_token(user_id):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    token = jwt.encode(payload, secret_key, algorithm=algorith)
    return {"access_token": token, "token_type": "bearer"}

# Function to decode JWT token
# def decode_token(token: str = Depends(oauth2_bearer)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, secret_key, algorithms=[algorith])
#         return payload
#     except JWTError:
#         raise credentials_exception


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorith])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Protected login route
@usersRoute.post("/login", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Your authentication logic here (e.g., check username and password)
    # Simulating a user authentication check for demonstration purposes
    print(form_data.username)
    fake_user = {"sub": form_data.username}

    # Create a new JWT token for the authenticated user
    # access_token_expires = timedelta(minutes=30)
    access_token = create_jwt_token(form_data.username)

    return access_token


@usersRoute.get('/v1/GetUser/')
def getUsers(email:str):
        user = dbusers.find_one({"email": email})
        if user:
            return {**user, "_id": str(user["_id"])}
        else:
            raise HTTPException(status_code=404, detail="User not found")

@usersRoute.patch('/v1/updatetoPremiumUsers/')
def updateUsers(update_data: dict,decoded_token: str = Depends(oauth2_bearer)):
    # Define a list of sensitive fields that should not be updated
    payload  = decode_jwt_token(decoded_token)
    # if payload.get('sub')
    sensitive_fields = ["email", "password"]
    # print(email)
    print(update_data)

    update_operation = {"$set": update_data}

    # Perform the find_one_and_update operation
    updated_user = dbusers.find_one_and_update(
        {"email": update_data['email']},
        update_operation,
        return_document=True  # Return the updated document
    )
    print(updated_user)

    # # Check if the document was found and updated
    if updated_user:
        return 'Updates Successfully'
    else:
        raise HTTPException(status_code=404, detail="User not found")


@usersRoute.post('/v1/becomeCreator',status_code=status.HTTP_201_CREATED)
def becomeCreator(creator:Creator,decoded_token: str = Depends(oauth2_bearer)):
    payload = decode_jwt_token(decoded_token)
    payload = payload.get('sub')
    getusers = dbusers.find_one({'email':payload})
    print(getusers.get('creator_info'))
    if getusers.get('creator_info') is not None:
        raise HTTPException(401,detail='User is already a creator')
    
    creator.channel_link = (str(creator.channel_name).strip())+str(secrets.token_hex(3))
    creator.creation_date = str(datetime.utcnow().isoformat())
    query = {'email':payload}
    creator = creator.model_dump()
    update = {
    "$set": {
        'creator_info':creator
    }}
    
    # print(update)
    id = dbusers.update_one(query,update)
    if id:
        return 'Creator Created'
    else:
        return 'something went wrong'

    

















































#
# q = User(
# name = 'karan',
# email= 'ksaj@mdjs',
# password= 'kbkjb',
# premium_member= False
# )
# q.create_users()
#
# User.getUsers('ksaj@mdjs')



# class Comment(BaseModel):
#     user_id: str
#     video_id: str
#     text: str
#
# class Like(BaseModel):
#     user_id: str
#     video_id: str
#
# class Video(BaseModel):
#     title: str
#     url: str


