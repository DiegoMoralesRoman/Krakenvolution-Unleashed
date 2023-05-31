from egoros.node import Configuration

def callback(arg: str, context):
    print(f'Received message: {arg}. Context: {context}')

def init(node):
    print('Other node initialized')
    # node.subscribe('messages', callback)
    return Configuration(
        name='Kekos'
    )

