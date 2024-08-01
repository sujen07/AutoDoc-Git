import requests
import pdb
import base64

from weaviate_init import client

git_files_collection = client.collections.get('GitFiles')

def toBase64(content):
    return base64.b64encode(content).decode('utf-8')

def process_github_repo(owner, repo, path='', process_function=None):
    api_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    
    response = requests.get(api_url)
    
    if response.status_code == 200:
        contents = response.json()
        
        for item in contents:
            if item['type'] == 'file':
                # Download file content
                file_content = requests.get(item['download_url']).content
                
                # Process the file content
                if process_function:
                    process_function(item['name'], file_content)
                
                print(f"Processed: {item['path']}")
            
            elif item['type'] == 'dir':
                # Recursively process directory contents
                process_github_repo(owner, repo, item['path'], process_function)
    else:
        print(f"Failed to retrieve repository contents. Status code: {response.status_code}")

# Example processing function
def add_to_embedding_collection(filename, content):
    # This is a placeholder function. Replace it with your actual processing logic.
    print(f"Processing file: {filename}")
    print(f"File size: {len(content)} bytes")
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        git_files_collection.data.insert(
            {
                "name": filename,
                "image": toBase64(content),
                "mediaType": "image",
            }
        )
    else:
        git_files_collection.data.insert(
            {
                "name": filename,
                "text": toBase64(content),
                "mediaType": "text",
            }
        )

    # Add your processing logic here
    # For example, you could parse the content, extract information, or perform any other operation

# Example usage
owner = 'sujen07'
repo = 'test-repo'
process_github_repo(owner, repo, process_function=add_to_embedding_collection)
client.close()