# email-wakod17343@wenkuu.com
# password-1wakod17343@wenkuu.com
# sl.BsN1GRl5lB30LRBfO4TSNOX1amQM2o6n_zQqBHq6GsWa92Ve5EJGMUtejno8x6ea9CyLgqpYmVOWgZUXyOxvNApwEclfGxD-y_EhPzpbvSZ715H296fed94WwGZmMvCUOANb_T9jxhqN
# DropBOX
import os
import json
import secrets
from enum import Enum
from fastapi.responses import StreamingResponse
import pydantic
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter,Depends
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Union,Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from starlette.responses import JSONResponse
VIDEO_DIRECTORY = 'C:/Users/iwizards/Desktop/vidTume/videos/video_path/'
# from main import 
from userConfig.users import decode_jwt_token,oauth2_bearer
from dbconfig import dbusers
from dbconfig import videos as vd
class UserInfo(BaseModel):
    email: str
    name: str

class AccessControl(str, Enum):
    public = "public"
    private = "private"
    restricted = "restricted"

class MonetizationInfo(BaseModel):
    monetized: bool
    revenue_share: float

class Comment(BaseModel):
    user_info: UserInfo
    text: str
    timestamp: datetime


class Video(BaseModel):
    title: str
    description: str
    # # thumbnail: str
    tags: List[str] = []
    # visibility: List[str]
    # access_control: AccessControl
    # user_info: UserInfo
    likes: int = 0
    dislikes: int = 0
    views_count: int = 0
    comments: List[Comment] = []  # List of comments linked to the video
    # video_url: str
    # monetization_info: MonetizationInfo # it should go in channel level and videos level pe bi hona chahiye
    published:bool=False

    @model_validator(mode="before")
    @classmethod
    def to_py_dict(cls, data):
        return json.loads(data)

    class Config:
        populate_by_name = True

def check_file_size(fileSize):
    max_size = 1000 * 1024 * 1024
    if fileSize > max_size:
        return True


videos_routes = APIRouter(tags=['Videos'])


@videos_routes.post("/api/upload-video")
async def upload_video(videos:str=Form(...),video_file: UploadFile = File(...),decoded_token: str = Depends(oauth2_bearer)):
    # if user is a creator or not this can be checked if creator info is None or not
    
    payload = decode_jwt_token(decoded_token)
    payload = dbusers.find_one({'email':payload.get('sub')})
    if payload['creator_info'] is None:
        raise HTTPException(404,detail='Pls register as creator')
    user_info_internal = UserInfo(email=payload['email'], name=payload['name'])
    extension = ['mp4', 'mkv', 'avi']
    file_ext = video_file.filename.split(".").pop()
    print(file_ext)
    if file_ext not in extension:
        raise HTTPException(status_code=404, detail='Wrong file format seleted')
    fileSize = video_file.size


    if check_file_size(fileSize):
        raise HTTPException(status_code=404, detail='File size exceed')
    # Save the video file to a local directory
    # upload_folder = "C:\\Users\\iwizards\\Desktop\\vidTume\\videos\\video_path"  # Change this to your desired directory

    file_name = secrets.token_hex(10)
    file_path = f"{file_name}.{file_ext}"
    video_url = f"{file_name}.{file_ext}"

    file_path = VIDEO_DIRECTORY+file_path
    print('file_path',file_path)

    with open(file_path, "wb") as file:
        file.write(video_file.file.read())


    videos = json.dumps(videos)
    try:
        model = Video.model_validate_json(videos)
    except pydantic.ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        ) from e
    print(type(model))


    # Update the video details with the file information
    video_dict = model.model_dump(by_alias=True)
    # video_dict["video_file"] = file_path
    Video.video_file = video_file.filename
    video_dict.update(
        upload_datetime=datetime.utcnow().isoformat(),
        video_url = video_url,
        user_info=(user_info_internal).model_dump()
    )

    print(video_dict)

    result = vd.insert_one(video_dict)

    return JSONResponse(content={"message": "Video details and file uploaded successfully"}, status_code=201)


@videos_routes.get('/v1/getAllVideos')
def getVideos():
    pipeline = [
    {
        '$match': {
            'published': True
        }
    }]
    result = list(vd.aggregate(pipeline))
    print(result)
    op = []
    for i in result:
        op.append(i.get('video_url'))
    return op

# @videos_routes.get("/v1/video/{video_name}")
# async def stream_video(video_name: str,range_header: str = None):
#     video_path = (video_name)
#     print(video_name)

#     if not os.path.exists(video_path):
#         raise HTTPException(status_code=404, detail="Video not found")
#     file_size = os.path.getsize(video_path)
#     query = {'video_url': video_name}  # Replace with your actual query

#     # Specify the field to increment and the value to increment by
#     update = {'$inc': {'views_count': 1}}  # Increment the 'views_count' field by 1

#     # Perform the update operation
#     result = vd.update_one(query, update)
    

#     if range_header:
#         start, end = map(int, range_header.strip("bytes=").split("-"))
#         # start = int(start) if start else 0
#         # end = int(end) if end else file_size - 1
#     else:
#         start, end = 0, file_size - 1

#     content_length = end - start + 1
#     headers = {
#         "Content-Range": f"bytes {start}-{end}/{file_size}",
#         "Content-Length": str(content_length),
#         "Accept-Ranges": "bytes",
#     }
#     def generate():
#         with open(video_path, "rb") as video_file:
#             while chunk := video_file.read(8192):  # 8 KB chunks
#                 yield chunk
#     headers = {"Accept-Ranges": "bytes"}  # Set Accept-Ranges header
#     return StreamingResponse(generate(), media_type="video/mp4", headers=headers)

@videos_routes.get("/video/{video_name}")
async def stream_video(video_name: str,range_header: str = None):
    video_path = VIDEO_DIRECTORY+video_name
    print(video_path)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    file_size = os.path.getsize(video_path)
    print(video_path)
    query = {'video_url': video_name}  # Replace with your actual query

#     # Specify the field to increment and the value to increment by
    update = {'$inc': {'views_count': 1}}  # Increment the 'views_count' field by 1

#     # Perform the update operation
    result = vd.find_one_and_update(query, update,return_document=True)
    print(result)
    if range_header:
        start, end = map(int, range_header.strip("bytes=").split("-"))
        # start = int(start) if start else 0
        # end = int(end) if end else file_size - 1
    else:
        start, end = 0, file_size - 1

    content_length = end - start + 1
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
        "Accept-Ranges": "bytes",
    }
    def generate():
        with open(video_path, "rb") as video_file:
            while chunk := video_file.read(8192):  # 8 KB chunks
                yield chunk
    headers = {"Accept-Ranges": "bytes"}  # Set Accept-Ranges header
    return StreamingResponse(generate(), media_type="video/mp4", headers=headers)




            




'''
{
  "title": "Sample Video",
  "description": "This is a sample video description",
  "video_file": "sample_video.mp4",
  "thumbnail": "sample_thumbnail.jpg",
  "tags": ["tag1", "tag2"],
  "visibility": "public",
  "access_control": {
    "permissions": {
      "read": "public",
      "write": "private"
    }
  },
  "upload_datetime": "2023-01-01T12:00:00Z",
  "duration": "00:10:30",
  "user_info": {
    "user_id": "123",
    "username": "sample_user"
  },
  "likes": 100,
  "dislikes": 5,
  "views_count": 1000,
  "comments": [
    {
      "user_info": {
        "user_id": "456",
        "username": "commenter1"
      },
      "text": "Great video!",
      "timestamp": "2023-01-01T12:05:00Z"
    },
    {
      "user_info": {
        "user_id": "789",
        "username": "commenter2"
      },
      "text": "Awesome content!",
      "timestamp": "2023-01-01T12:10:00Z"
    }
  ],
  "video_url": "http://example.com/sample_video",
  "monetization_info": {
    "monetized": true,
    "revenue_share": 0.5
  },
  "quality_resolution": "1080p"
}
'''













