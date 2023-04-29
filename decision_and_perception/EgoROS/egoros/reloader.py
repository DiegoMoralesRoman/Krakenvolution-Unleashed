from typing import Any, Callable, List
from . import node  # Import the Node class from the local module
from watchdog.observers import Observer  # Import the Observer class from the watchdog library
from watchdog.events import FileSystemEventHandler  # Import the FileSystemEventHandler class from the watchdog library

class FileModifiedHandler(FileSystemEventHandler):
    """
    Custom event handler that triggers a callback when a file is modified
    """
    def __init__(self, callback: Callable[[], None]) -> None:
        """
        Constructor for the FileModifiedHandler class
        @param callback: The callback function to trigger when a file is modified
        """
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        """
        Overrides the on_modified method of the FileSystemEventHandler class
        @param event: The event that triggered the callback
        """
        print(f'Event: {event}')
        if not event.is_directory:
            self.callback()

handlers = []  # List to store the event handlers
observer = Observer()  # Create an instance of the Observer class

def callback(node: node.Node, init_arg: Any) -> None:
    """
    Callback function that reloads a node module when the corresponding file is modified
    @param node: The node module to reload
    @param init_arg: The initialization argument to pass to the node module's init function
    """
    print(f'Reloading node {node.filename}')
    node.__init__(node.filename) # Reload module
    node.init(init_arg)

def enable_dynamic_reloads(nodes: List[node.Node], init_arg: Any) -> Observer:
    """
    Enables dynamic reloading of node modules when their corresponding files are modified
    @param nodes: The list of Node instances to watch for file modifications
    @param init_arg: The initialization argument to pass to the node module's init function
    @return: An instance of the Observer class used to watch for file modifications
    """
    for node in nodes:
        handler = FileModifiedHandler(lambda: callback(node, init_arg))  # Create a new event handler for the node
        observer.schedule(handler, node.filename, recursive=False)  # Schedule the event handler to watch for file modifications
        handlers.append(handler)  # Add the event handler to the list of handlers

    return observer  # Return the observer instance so that it can be started later
