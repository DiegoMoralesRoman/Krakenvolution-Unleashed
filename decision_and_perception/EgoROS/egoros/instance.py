import threading
from typing import Any, Dict, List
from . import node
from . import egonode
import logging
from . import reloader
from .pubsub import Topic

log = logging.getLogger('egoros')

class EgoInstance:
    '''

    '''
    def __init__(self, node_filanames: List[str]) -> None:
        # Open nodes
        self.nodes = [node.Node(file) for file in node_filanames]
        self.topics: Dict[str, Topic] = {}
        self.reload_server = None

    def enable_hot_reloading(self) -> None:
        self.reload_server = reloader.enable_dynamic_reloads(self.nodes, self)

    def spin(self) -> None:
        running = True

        # Create EgoNodes
        nodes = [egonode.EgoNode(node, self.topics) for node in self.nodes]

        # Launch all nodes
        joiners = [node.launch() for node in nodes]

        ev = threading.Event()
        # Wait for all nodes to stop
        try:
            print(self.reload_server)
            if (self.reload_server != None):
                self.reload_server.start()
            ev.wait()
        except KeyboardInterrupt:
            msg = f'''
    Egoros interrupted by user, stopping all threads...
            '''
            log.warning(msg)

        [node.stop() for node in nodes]

        log.info(f'''
    Finishing EgoROS instance.
    Waiting for all nodes to finish...
        ''')

        try:
            [joiner() for joiner in joiners]
            pass
        except KeyboardInterrupt as e:
            log.warning(f'''
    Forcing exit of nodes
            ''')
            # TODO: abort nodes execution
            log.error('You dun goofed')
            raise e # FIXME: this is obviously a problem, but I don't want to fix it now

    def publish(self, topic: str, value: Any):
        pass

