from typing import Dict, List
from .node import Node, Configuration
from . import reloader
import os
from dataclasses import dataclass
import threading

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

@dataclass 
class EgoNode:
    config: Configuration
    node: Node

# Main instance
class EgoInstance:
    def __init__(self, node_paths: List[str]) -> None:
        nodes  = [Node(e) for e in node_paths]
        self.nodes: Dict[str, EgoNode] = {}
        # Initialize nodes
        for node in nodes:
            node_config = node.init(self)
            self.nodes[node_config.name] = EgoNode(
                config=node_config,
                node=node
            )

        self.observer_started = False
        self.running = True


    def enable_dynamic_reloads(self):
        self.dyn_reload_observer = reloader.enable_dynamic_reloads([e.node for e in self.nodes.values()], self)
        if not self.observer_started:
            self.dyn_reload_observer.start()
            self.observer_started = True

    def spin(self):
        tick_condition = threading.Condition()

        # Check configuration
        undefered_nodes: List[EgoNode] = []
        defered_nodes: List[EgoNode] = []
        for name, node in self.nodes.items():
            if node.config.defered and node.node.is_tickable():
                defered_nodes.append(node)
            elif node.node.is_tickable():
                undefered_nodes.append(node)

        def defered_thread_tick(node):
            while self.running:
                tick_condition.acquire()
                tick_condition.wait()
                tick_condition.release()
                node.node.tick(self)

        # Add defered threads
        defered_tick_thread_handlers = []
        for defered in filter(lambda e: e.node.is_tickable(), defered_nodes):
            handler = threading.Thread(target=lambda: defered_thread_tick(defered))
            handler.start()
            defered_tick_thread_handlers.append(handler)
            

        from time import sleep
        while self.running:
            tick_condition.acquire()
            tick_condition.notify_all()
            tick_condition.release()
            # Tick all undefered nodes
            for node in undefered_nodes:
                node.node.tick(self)
            sleep(1)


    def stop(self):
        self.running = False
