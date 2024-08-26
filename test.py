import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.config import Configure
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_API_KEY = os.getenv("GOOGLE_APIKEY")

client = weaviate.connect_to_embedded(
    version="1.24.21",
    environment_variables={
        "ENABLE_MODULES": "multi2vec-palm",
    },
    headers={
        "X-PALM-Api-Key": EMBEDDING_API_KEY,
    }
)