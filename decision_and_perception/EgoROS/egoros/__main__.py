# First thing to do is configure the global configuration of the parser
from . import utils
utils.configure_logger()

import argparse
from . import node
import logging
from functools import reduce
from . import instance


log = logging.getLogger('egoros')

parser = argparse.ArgumentParser(description='''
    Allows to run a dedicated ego-ros instance
''')

parser.add_argument(
    '-p', '--path',
    action='store',
    help='Specified the folder where the nodes are located (default: "./nodes")',
    default='./nodes',
)

parser.add_argument(
    '-r', '--enable-hot-reload',
    action='store_true',
    help='Enables hot reloading for all of the nodes'
)

args = parser.parse_args()

# Get nodes
try:
    filenames = utils.get_node_filenames_from_path(args.path)
    print(filenames)
    # Crete an egoros instance
    read = reduce(
        lambda prev, filename: prev + '\t' + str(filename) + '\n',
        filenames,
        ''
    )
    log.info(f'''
    Nodes discovered:
{read}
    ''')

    ego = instance.EgoInstance(
        node_filanames=filenames
    )

    if args.enable_hot_reload:
        log.info('Enabling hot reload...')
        ego.enable_hot_reloading()


except FileNotFoundError as e:
    log.critical(f'''
    Could not read path "{args.path}"
    '''
    )
    exit(1)
except Exception as e:
    exit(1)
