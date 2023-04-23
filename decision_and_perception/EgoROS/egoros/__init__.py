from typing import List
import os

def get_folder_nodes(path: str):
    paths: List[str] = []
    
    def recursion(path: str):
        # Read contents
        for entry in os.scandir(path):
            # Check if it's a file (.py or .so nodes)
            if entry.is_file():
                # Get file extension
                if os.path.splitext(entry.path)[1] in ['.so', '.py']:
                    paths.append(entry.path)
            elif entry.is_dir():
                # Check if folder contains a __init__.py file (it's a python package)
                if os.path.exists(os.path.join(entry.path, '__init__.py')):
                    paths.append(entry.path)
                else:
                    # Recurse into folder
                    recursion(entry.path)

    recursion(path)

    # Convert paths into absolute path
    paths = [os.path.abspath(e) for e in paths]
    return paths
