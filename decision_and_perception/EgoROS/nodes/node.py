print('Normal module loaded')
import sys
import logging

import egoros.node

def test(msg, ctx):
    print(msg, ctx)

def init(mod):
    print('Piposaurio (from normal node)')
    mod.subscribe('kekos', test)
    return egoros.node.Configuration(
        name = 'test_node',
        tick_rate = 1
    )

def tick(mod):
    pass
