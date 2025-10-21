from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

# Directory where this file lives
BASE_DIR = os.path.dirname(__file__)

# Go one level up
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

# Load .env from the parent directory
load_dotenv(dotenv_path=os.path.join(PARENT_DIR, ".env"))

STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")

blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
container_client = blob_service.get_container_client("visualizations")

# List blobs
for blob in container_client.list_blobs():
    print("Found blob:", blob.name)

# Download the PNG
blob_client = container_client.get_blob_client("traffic_hotspots.png")
with open("traffic_hotspots.png", "wb") as f:
    f.write(blob_client.download_blob().readall())

print("Downloaded traffic_hotspots.png")
