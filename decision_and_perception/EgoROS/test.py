import egoros
import egoros.node
import egoros.reloader

nodes = egoros.get_folder_nodes('./nodes')

loaded_nodes = [egoros.node.Node(e) for e in nodes]

observer = egoros.reloader.enable_dynamic_reloads(loaded_nodes, 'Kekos')
observer.start()

from time import sleep

while True:
    try:
        sleep(1)
    except Exception as e:
        raise e
