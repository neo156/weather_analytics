from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb+srv://ninoespe:ninoespe@cluster0.9gbawhm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["weatherDB"]
collection = db["weather_data"]

# Print total number of documents
print(f"Total documents: {collection.count_documents({})}")

# Print all distinct station IDs
stations = collection.distinct("station_meta.station_id")
print(f"\nAll stations: {stations}")

# Check specifically for Mati station
mati_count = collection.count_documents({"station_meta.station_id": "mati"})
print(f"\nMati station documents: {mati_count}")

# Get one document from Mati station
mati_doc = collection.find_one({"station_meta.station_id": "mati"})
if mati_doc:
    print(f"\nSample Mati document: {mati_doc}")
else:
    print("\nNo Mati station documents found")
