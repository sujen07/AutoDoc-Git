import os
import requests
import base64
import ast
from dotenv import load_dotenv
import google.generativeai as genai
from weaviate_init import client
import tempfile

load_dotenv()

# Configure Google LLM
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 32,
    "max_output_tokens": 1024,
    "response_mime_type": "text/plain",
}

text_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)




def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

chat_session = text_model.start_chat(history=[])

git_files_collection = client.collections.get('GitFiles')

def toBase64(content):
    return base64.b64encode(content).decode('utf-8')

def extract_comments(content):
    """Extract comments from the code."""
    comments = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                comments.append(node.value.s)
    except SyntaxError:
        pass
    return str(comments)


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
    
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        # Handling image files
        git_files_collection.data.insert(
            {
                "name": filename,
                "image": toBase64(content),
                "mediaType": "image",
                "fileSize": len(content),
            }
        )
    else:
        # Handling text files
        content_text = content.decode('utf-8')
        # Split the content into chunks (example: 1000 characters per chunk)
        chunk_size = 1000
        chunks = [content_text[i:i+chunk_size] for i in range(0, len(content_text), chunk_size)]
        for chunk in chunks:
            git_files_collection.data.insert(
                {
                    "name": filename,
                    "text": toBase64(chunk.encode('utf-8')),
                    "mediaType": "text",
                    "fileSize": len(chunk.encode('utf-8')),
                }
            )

# Example usage
owner = 'sujen07'
repo = 'test-repo'
structure = process_github_repo(owner, repo, process_function=add_to_embedding_collection)
print(structure)
client.close()