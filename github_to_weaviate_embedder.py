import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import weaviate_init
import numpy as np

load_dotenv()

client = weaviate_init.start_client()
weaviate_init.add_collection(client)

# Configure Google LLM
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 32,
    "max_output_tokens": 1024,
    "response_schema": content.Schema(
        type=content.Type.OBJECT,
        description="Return a list of near text queries for GitHub repo analysis",
        properties={
            "queries": content.Schema(
                type=content.Type.ARRAY,
                items=content.Schema(
                    type=content.Type.STRING,
                    description="A query that can help filter the embeddings collection."
                )
            )
        }
    ),
    "response_mime_type": "application/json",
}

text_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)


GET_QUERY_PROMPT = "I have chunks of code and text from a github repo stored \
    in a embeddings collection, come up with near text queries that would fillter the collection \
    for any information that would allow an LLM to figure out how to use the github repo, \
    make sure to use queries that would filter a vector database with these text chunks, \
    and keep in mind the frameworks used based on file extensions, here is the structure of it: "

chat_session = text_model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                "Generate a list of near text queries that would filter the collection for information allowing an LLM to figure out how to use a GitHub repo. Output as JSON."
            ],
        },
        {
            "role": "model",
            "parts": [
                "{\n\"queries\": [\n\"Dependencies and installation\",\n\"import python\",\n\"npm install\", \n\"docker\"\n]\n}"
            ],
        },
    ]
)

git_files_collection = client.collections.get('GitFiles')

def toBase64(content):
    return content.decode('ascii', errors='ignore')

def is_readable_text(content, sample_size=1024):
    if not content:  # Empty content
        return False
    
    # Sample a random portion of the content
    content_length = len(content)
    if content_length > sample_size:
        start = np.random.randint(0, content_length - sample_size)
        sample = content[start:start + sample_size]
    else:
        sample = content
    
    # Check if the majority of the sample is printable text
    return all(32 <= byte <= 126 or byte in (9, 10, 13) for byte in sample)


def process_github_repo(owner, repo, path='', process_function=None):
    structure = {}

    def recursive_process(path):
        api_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        response = requests.get(api_url)
        
        if response.status_code == 200:
            contents = response.json()
            current_structure = []
            
            for item in contents:
                if item['type'] == 'file':
                    current_structure.append(item['name'])
                    
                    # Download file content (optional)
                    file_content = requests.get(item['download_url']).content
                    
                    # Process the file content (if process_function is provided)
                    if process_function:
                        process_function(item['name'], file_content, item['download_url'])
                
                elif item['type'] == 'dir':
                    current_structure.append({
                        item['name']: recursive_process(item['path'])
                    })
                    
            return current_structure
        else:
            print(f"Failed to retrieve repository contents. Status code: {response.status_code}")
            return None
    
    structure = recursive_process(path)
    return structure

# Example processing function
def add_to_embedding_collection(filename, content, filepath):
    # Adding files to collection
    print(f"Processing file: {filename}")
    print(f"File size: {len(content)} bytes")
    
    if is_readable_text(content):
        # Handling text files
        #pdb.set_trace()
        content_text = toBase64(content)
        # Split the content into chunks (example: 1000 characters per chunk)
        chunk_size = 1000
        chunks = [content_text[i:i+chunk_size] for i in range(0, len(content_text), chunk_size)]
        for i,chunk in enumerate(chunks):
            git_files_collection.data.insert(
                {
                    "name": filename + f'_chunk{i}',
                    "text": chunk,
                    "mediaType": "text",
                    "fileSize": len(chunk.encode('utf-8')),
                }
            )


def get_queries(text_model, structure):
    response = chat_session.send_message(GET_QUERY_PROMPT + str(structure))
    return response

# Example usage
owner = 'sujen07'
repo = 'image-super-resolution'
structure = process_github_repo(owner, repo, process_function=add_to_embedding_collection)
print(structure)

response = git_files_collection.query.near_text(
    query="PyTorch training model",
    return_properties=['name', 'text'],
    limit=3
)

for obj in response.objects:
    print('name: ' + obj.properties['name'])
    test = obj.properties['text']
    print('String: ',  test)

response = get_queries(text_model, structure)


client.close()