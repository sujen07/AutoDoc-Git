import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.config import Configure
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



if(client.collections.exists("GitFiles")):
    client.collections.delete("GitFiles")
    
client.collections.create(
    name="GitFiles",
    vectorizer_config=Configure.Vectorizer.multi2vec_clip(
        image_fields=["image"], 
        text_fields=['text'],      
    )
)

