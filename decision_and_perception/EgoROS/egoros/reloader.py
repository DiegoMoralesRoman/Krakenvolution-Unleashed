from typing import Any, Callable
from . import List, node
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileModifiedHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable) -> None:
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        print(f'Event: {event}')
        if not event.is_directory:
            self.callback()

handlers = []
observer = Observer()

def callback(node: node.Node, init_arg: Any):
    print(f'Reloading node {node.filename}')
    node.__init__(node.filename) # Reload module
    node.init(init_arg)

def enable_dynamic_reloads(nodes: List[node.Node], init_arg: Any):
    for node in nodes:
        handler = FileModifiedHandler(lambda: callback(node, init_arg))
        observer.schedule(handler, node.filename, recursive=False)

    return observer
