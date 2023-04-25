print('Normal module loaded')
import sys
import logging

import egoros.node

def init(mod):
    print('Piposaurio (from normal node)')
    return egoros.node.Configuration(
        name = 'test_node',
    )

def tick(mod):
    msg = 'Pipusaurio'
    print(f'Publicando: {msg}')
    mod.publish('messages', msg)
