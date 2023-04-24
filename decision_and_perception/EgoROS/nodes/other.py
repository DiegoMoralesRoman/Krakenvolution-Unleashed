from egoros.node import Configuration

def init(node):
    print('Other node initialized')
    return Configuration(
        name='Kekos'
    )

def tick(node):
    print('Ticked dingus node')
