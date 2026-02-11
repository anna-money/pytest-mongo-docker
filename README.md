Data directory is mounted to a tmpfs for speed.

# How to use?

```
import pymongo


def test_pymongo(mongo):
    client = pymongo.MongoClient(host=mongo.host, port=mongo.port)

    db = client["test_db"]
    collection = db["test_collection"]

    collection.insert_one({"key": "value"})
    doc = collection.find_one({"key": "value"})

    assert doc["key"] == "value"

    client.close()
```
