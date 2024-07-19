import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

client = weaviate.connect_to_local(
    port=8080,
    grpc_port=50051,
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=60, insert=120)  # Values in seconds
    )
)


"""
# Just checking if you ever need to re run it
if(client.collections.exists("Animals")):
    client.collections.delete("Animals")
    
client.collections.create(
    name="Animals",
    vectorizer_config=Configure.Vectorizer.multi2vec_clip(
        image_fields=["image"],
        video_fields=["video"],
        project_id="semi-random-dev",
        location="us-central1",
        model_id="multimodalembedding@001",
        dimensions=1408,        
    )
)

"""