from fastapi import FastAPI
# from users import usersRoute
from userConfig.users import usersRoute
from videos.video_upload import videos_routes

# subsciber count
# likes count
# 
app  = FastAPI()

app.include_router(usersRoute)
app.include_router(videos_routes)