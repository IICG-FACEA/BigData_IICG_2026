from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

uri = "mongodb://nicolegarcia_db_user:Ternurines123@ac-iq19sqr-shard-00-00.uia9vsi.mongodb.net:27017,ac-iq19sqr-shard-00-01.uia9vsi.mongodb.net:27017,ac-iq19sqr-shard-00-02.uia9vsi.mongodb.net:27017/BigData_UCN?ssl=true&replicaSet=atlas-t7etb5-shard-0&authSource=admin&retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("Conexión exitosa a Atlas")
except Exception as e:
    print("Error:", e)
