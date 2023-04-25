from egoros.node import Configuration

def callback(arg: str):
    print(f'Received message: {arg}')

def init(node):
    print('Other node initialized')
    node.subscribe('messages', callback)
    return Configuration(
        name='Kekos'
    )

