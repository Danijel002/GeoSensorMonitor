"""MongoDB persistence layer for sensor readings."""

from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
import config

client=MongoClient(config.MONGO_HOST,config.MONGO_PORT)
db=client[config.MONGO_DB]
collection=db[config.MONGO_COLLECTION]

def save_reading(node_id, temperature, humidity,uv):
    """Insert a single reading with the current timestamp."""
    collection.insert_one(
        {
        "timestamp": datetime.now(),
        "node_id": node_id,
        "temperature": temperature,
        "humidity": humidity,
        "uv": uv,
        }
    )

def get_latest_per_node():
    """Return {node_id: (temperature, humidity, uv)} for the newest reading of each node."""
    pipline=[
        {"$sort":{"timestamp":DESCENDING}},
        {"$group":{
            "id":"$node_id",
            "temperature":{"$first":"$temperature"},
            "humidity":{"$first":"$humidity"},
            "uv":{"$first":"$uv"},
        }},
    ]

    return {
        doc["id"]:(doc["temperature"],doc["humidity"],doc["uv"])
        for doc in collection.aggregate(pipline)
    }

def get_recent_readings(node_id,limit=config.HISTORY_LIMIT):
    """Return the most recent readings for a node, newest first."""
    cursor=(
        collection.find({"node_id":node_id})
        .sort("timestamp",DESCENDING)
        .limit(limit)
    )

    return [
        {
            "timestamp": doc["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": doc["temperature"],
            "humidity": doc["humidity"],
            "uv": doc["uv"],
        }
        for doc in cursor
    ]

def get_readings_between(node_id, start, end):
    """Return all readings for a node in [start, end], oldest first."""
    cursor = collection.find({
        "node_id": node_id,
        "timestamp": {"$gte": start, "$lte": end},
    }).sort("timestamp", ASCENDING)
    return list(cursor)


