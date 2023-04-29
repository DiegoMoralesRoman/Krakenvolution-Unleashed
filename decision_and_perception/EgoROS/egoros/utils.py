import os
from typing import List
import logging

def get_node_filenames_from_path(path: str):
    """
    Gets the defined nodes inside a folder
    @param path Path of the folder to search the nodes
    @details
    The nodes are the files/folders that follow any of the next rules:
    - Files ending in .py (that are not inside a package)
    - Files ending in .so (compiled modules, for example C++ or Rust)
    - Folders containing a __init__.py file (python packages)
    
    A folder can also contain more nodes (the search is recursive). A folder will be checked
    if there is no __init__.py file inside it.
    @return List[str] containing all the file/folder paths that are valid EgoROS nodes
    """
    paths: List[str] = []
    
    def recursion(path: str):
        """
        Recursion method helper 
        @param path Path to search the nodes
        """
        # Read contents
        for entry in os.scandir(path):
            # Check if it's a file (.py or .so nodes)
            if entry.is_file():
                # Get file extension
                if os.path.splitext(entry.path)[1] in ['.so', '.py']:
                    # If it's any of the supported file types add it to the list
                    paths.append(entry.path)
            elif entry.is_dir():
                # Check if folder contains a __init__.py file (it's a python package)
                if os.path.exists(os.path.join(entry.path, '__init__.py')):
                    paths.append(entry.path)
                else:
                    # Search into non-package folder
                    recursion(entry.path)

    recursion(path) # Recursion entry point

    # Convert paths into absolute path
    paths = [os.path.abspath(e) for e in paths] 
    return paths

def configure_logger(
        path: str = 'egoros.log',
        level: int = logging.INFO
    ):
    logger = logging.getLogger('egoros')
    logger.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    terminal_formatter = logging.Formatter('%(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(terminal_formatter)

    file_handler = logging.FileHandler(path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
