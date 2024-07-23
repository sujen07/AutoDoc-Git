import requests
import pdb

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
def example_process_function(filename, content):
    # This is a placeholder function. Replace it with your actual processing logic.
    print(f"Processing file: {filename}")
    print(f"File size: {len(content)} bytes")
    pdb.set_trace()
    # Add your processing logic here
    # For example, you could parse the content, extract information, or perform any other operation

# Example usage
owner = 'kashish-ag'
repo = 'Detection-of-Plant-Disease'
process_github_repo(owner, repo, process_function=example_process_function)