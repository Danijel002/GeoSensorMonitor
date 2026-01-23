from pymongo import MongoClient
import datetime


client = MongoClient("localhost", 27017)
db = client["Baza5"]
collection = db["Kolekcija5"]


def sacuvani_podaci(node_num, temp, hum, uv):
    doc = {
        "datum_vrijeme": datetime.datetime.now(),
        "id": node_num,
        "Temperature": temp,
        "Humidity": hum,
        "UV": uv
    }
    collection.insert_one(doc)


def poslednja_vrednost(node_num):
    return collection.find_one({"id": node_num}, sort=[("datum_vrijeme", -1)])


def poslednje_vrednosti_svih_nodeova():
    result = {}
    svi = collection.aggregate([
        {"$sort": {"datum_vrijeme": -1}},
        {"$group": {"_id": "$id", "Temperature": {"$first": "$Temperature"},
                    "Humidity": {"$first": "$Humidity"}, "UV": {"$first": "$UV"}}}
    ])
    for doc in svi:
        result[doc["_id"]] = (doc["Temperature"], doc["Humidity"], doc["UV"])
    return result


def poslednjih_10_vrednosti(node_num):
    poslednjih_10 = list(collection.find({"id": node_num}).sort("datum_vrijeme", -1).limit(10))
    rezultat = []
    for doc in poslednjih_10:
        rezultat.append({
            "datum_vrijeme": doc["datum_vrijeme"].strftime("%Y-%m-%d %H:%M:%S"),
            "Temperature": doc["Temperature"],
            "Humidity": doc["Humidity"],
            "UV": doc["UV"]
        })
    return rezultat
