from typing import List
from . import node
import logging
from . import reloader

log = logging.getLogger('egoros')

class EgoInstance:
    '''

    '''
    def __init__(self, node_filanames: List[str]) -> None:
        # Open nodes
        self.nodes = [node.Node(file) for file in node_filanames]

    def enable_hot_reloading(self) -> None:
        reloader.enable_dynamic_reloads(self.nodes, self)

    def spin(self) -> None:
        running = True

        log.info(f'''
    Finishing EgoROS instance.
    Waiting for all nodes to finish...
        ''')

        try:
            # TODO: Add the joins for the thread handlers
            pass
        except InterruptedError as e:
            log.warning(f'''
    Forcing exit of nodes
            ''')
            # TODO: abort nodes execution


