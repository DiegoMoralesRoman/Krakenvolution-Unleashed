import egoros
import egoros.node

nodes = egoros.get_folder_nodes('./nodes')

instance = egoros.EgoInstance(nodes)
instance.enable_dynamic_reloads()

instance.spin(delta_t = 1)

