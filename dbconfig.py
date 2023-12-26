from pymongo import MongoClient



try:
    client = MongoClient("mongodb+srv://<>:<>@cluster0.jwi0z9m.mongodb.net/?retryWrites=true&w=majority")

    # MONGO_DB_NAME = "youtube"
    db= client["youtube"]
    dbusers = db["users"]
    dbcreators = db['creators']
    videos = db["videos"]
    videoStats = db["videostat"]

except:
    raise "error"