from typing import Any, Dict, List, Any, Callable
from .node import Any, Node, Configuration
from . import reloader
import os
from dataclasses import dataclass, field
import threading
from .pubsub import MessageContext, MessageHub

def get_folder_nodes(path: str):
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

@dataclass 
class EgoNode:
    """
    Class containing information about a running node
    @param config Launch and basic configuration of the node
    @param the node itself
    """
    config: Configuration
    node: Node
    subscriptions: List[str] = field(default_factory=lambda: [])

# Main instance
class EgoInstance:
    """
    EgoROS server instance.
    """
    def __init__(self, node_paths: List[str]) -> None:
        """
        Constructor
        @param node_paths List of node paths that the server will keep track of
        """

        self.msg_hub = MessageHub()
        self.msg_hub.pause()

        nodes  = [Node(e) for e in node_paths]
        self.nodes: Dict[str, EgoNode] = {}
        # Initialize nodes
        for node in nodes:
            node_config = node.init(self)
            self.nodes[node_config.name] = EgoNode(
                config=node_config,
                node=node
            )

        self.msg_hub.resume()
        # Initialize inner attributes
        self.observer_started = False
        self.running = True

    def publish(self, topic: str, value: Any):
        self.msg_hub.publish(topic, value)

    def subscribe(self, topic: str, callback: Callable[[Any, MessageContext], None]):
        self.msg_hub.subscribe(topic, callback)

    def enable_dynamic_reloads(self):
        """
        Enables dynamic reload for all loaded modules
        @details
        Dynamic reload is the capability of hot reloading the egoros modules. 
        If the server detects a change on any file it will re-import it, keeping the states
        of the other nodes
        """
        # Enables hot reloading for every node
        self.dyn_reload_observer = reloader.enable_dynamic_reloads([e.node for e in self.nodes.values()], self)
        # Starts the observer thread (if it wasn't started before)
        if not self.observer_started:
            self.dyn_reload_observer.start()
            self.observer_started = True

    def spin(self, delta_t: float = 1.0):
        """
        Starts the EgoROS server
        @details Starts the ticking of the nodes using the provided configuration.
        The server will be stoped if the self.stop() method is called
        """
        # ==================================================
        # Subscription threads
        # ==================================================

        def subscription_thread(node: EgoNode):
            while self.running:
                pass

        subscription_thread_handlers: List[threading.Thread] = []
        for node in self.nodes.values():
            subscription_thread_handlers.append(threading.Thread(
                target=lambda node=node: subscription_thread(node)
            ))

        # ==================================================
        # Node ticking
        # ==================================================

        # Condition mutex that allows the synchronization of the nodes ticking
        tick_condition = threading.Condition()

        # Check configuration
        undefered_nodes: List[EgoNode] = []
        defered_nodes: List[EgoNode] = []
        for name, node in self.nodes.items():
            # Adds nodes if they are tickable (have the tick function defined)
            if node.config.defered and node.node.is_tickable():
                defered_nodes.append(node)
            elif node.node.is_tickable():
                undefered_nodes.append(node)

        def defered_thread_tick(node: EgoNode):
            """
            Function that every defered node runs. Allows the execution of defered nodes in
            different threads
            """
            while self.running:
                # Wait until the next tick is available
                tick_condition.acquire()
                tick_condition.wait()
                tick_condition.release()
                # Ticks the node
                node.node.tick(self)

        self.running = True
        # Starts defered nodes threads
        defered_tick_thread_handlers: List[threading.Thread] = []
        for defered in filter(lambda e: e.node.is_tickable(), defered_nodes):
            handler = threading.Thread(target=lambda: defered_thread_tick(defered))
            handler.start()
            defered_tick_thread_handlers.append(handler)

        def undefered_thread_tick():
            while self.running:
                tick_condition.acquire()
                tick_condition.wait()
                tick_condition.release()
                # Ticks all the undefered nodes
                for node in undefered_nodes:
                    node.node.tick(self)

        undefered_tick_thread_handler = threading.Thread(target=undefered_thread_tick)
        undefered_tick_thread_handler.start()

        import datetime
        from time import sleep

        # Initialized next_tick and converts delta to milliseconds
        # Using current times to avoid accumulating error on the tick activation time
        delta_t = datetime.timedelta(microseconds=(delta_t * 1000000))
        next_tick = datetime.datetime.now()
        # Main loop
        # Activates the tick condition and ticks every node
        try:
            while self.running:
                tick_condition.acquire()
                tick_condition.notify_all()
                tick_condition.release()
                
                # Waits for next tick and updates it's value for the next iteration
                current_time = datetime.datetime.now()
                sleep_time = (next_tick - current_time).total_seconds()
                next_tick += delta_t 
                if sleep_time > 0:
                    sleep(sleep_time)
        except KeyboardInterrupt as interrupt:
            self.running = False
            tick_condition.acquire()
            tick_condition.notify_all()
            tick_condition.release()
            print(f'''
    EgoROS main loop was interrupted by the user, closing all nodes...
            ''')
            
        # Wait until all threads have stopped
        undefered_tick_thread_handler.join()
        for handler in defered_tick_thread_handlers:
            handler.join()

        for handler in subscription_thread_handlers:
            handler.join()


    def stop(self):
        """
        Stops the server if self.spin() was called
        """
        self.running = False
