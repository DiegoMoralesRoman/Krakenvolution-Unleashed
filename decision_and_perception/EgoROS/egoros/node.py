from dataclasses import dataclass
import importlib.abc
import re
from types import ModuleType
from typing import Any, Callable, cast
import importlib.util
import os.path
import inspect
from enum import Enum
import traceback

class NodeState(Enum):
    ACTIVE = 0
    CRASHED = 1

@dataclass
class Loader:
    """
    Loader helper class that stores the available loaders
    @param expr Reges expression that has to match to try to load the module
    @param loader Loader method that tries to import the specified path
    """
    expr: re.Pattern[str]
    loader: Callable[[str], ModuleType]

@dataclass
class Requirement:
    """
    Helper class for node requirements
    @param name Name of the requirement member (for example init or tick)
    @param condition Condition that a member has to fulfill for the requirement to be checked
    """
    name: str
    condition: Callable

@dataclass
class Configuration:
    """
    Node configuration
    @name Public name of the node. This name will allow accessible features for every other node
    @param defered If True, runs the node in another thread
    """
    name: str
    defered: bool = False

def normal_loader(path: str):
    """
    Loads a .py file module
    @param Path where the file is located
    """
    node_name = os.path.splitext(path)[0]
    spec = importlib.util.spec_from_file_location(node_name, path)

    if not spec:
        raise ImportError(f'''
    Failed to generate spec for file {path}
        ''')

    # Load and run module
    mod = importlib.util.module_from_spec(spec)
    cast(importlib.abc.Loader, spec.loader).exec_module(mod)

    return mod

def dynamic_loader(path: str):
    """
    Loads a .so file module 
    @param path Path where the file is located
    @details
    These types of nodes are compiled from C++ or Rust source code (for example with the boost::python lib)
    """
    pass

def package_loader(path: str):
    """
    Loads a python package as a module
    @param path Path where the file is located
    @details This method will try to load the __init__.py file inside the package
    """
    package_main_path = os.path.join(path, '__init__.py')
    return normal_loader(package_main_path)

LOADERS = [
    Loader(
        expr=re.compile('^.*\.py$'), # All files with the .py extension
        loader=normal_loader
    ),
    Loader(
        expr=re.compile('^.*\.so$'), # All files with the .so extension
        loader=dynamic_loader
    ),
    Loader(
        expr=re.compile('^(?!.*\..*$).+$'), # All paths without extension (usually folders)
        loader=package_loader
    )
]

# TODO: check if the methods have sufficient arguments
REQUIREMENTS = [
    Requirement(
        name='init', # Init method
        condition=lambda e: callable(e[1]) and e[0] == 'init' 
    )
]

OPTIONAL_REQUIREMENTS = [
    Requirement(
        name='tick', # Tick method
        condition=lambda e: callable(e[1]) and e[0] == 'tick'
    )
]

class Node:
    """
    Basic EgoROS node
    @details
    This class will load and check if the node is valid for EgoROS
    All the conditions and optional requirements are defined in the variables
    REQUIREMENTS and OPTIONAL_REQUIREMENTS
    """
    def __init__(self, filename: str) -> None:
        """
        Constructor
        @param filename Filename of the underlying python module
        """
        # Initialize attributes
        self.state = NodeState.CRASHED
        self.mod = None
        self.filename = filename

        # Try to load the underlying module
        for loader in LOADERS:
            # Check if a defined loaders is able to load the module
            if re.match(loader.expr, filename):
                self.mod = loader.loader(filename)
                break

        # In case that the node could not be loaded throw an exception
        if not self.mod:
            raise ImportError(f'''
    Module of type {filename} 
    has no defined loaders
            ''')

        # Check if module is a valid node
        detected_requirements = {}
        optional_requirements = {}
        for member in inspect.getmembers(self.mod):
            # Check mandatory requirements
            for requirement in REQUIREMENTS:
                if requirement.condition(member):
                    detected_requirements[requirement.name] = member[1]

            # Check optional requirements
            for requirement in OPTIONAL_REQUIREMENTS:
                if requirement.condition(member):
                    optional_requirements[requirement.name] = member[1]

        # Check if all mandatory requirements were met
        if len(detected_requirements) != len(REQUIREMENTS):
            not_found = ''
            # Add the requirements that were not found to the error message
            for req in filter(lambda e: e.name not in detected_requirements.keys(), REQUIREMENTS):
                not_found += f'{req.name}\n'

            raise ImportError(f'''
    Could not find all requirements for the module {filename}
    Found {len(detected_requirements)} out of {len(REQUIREMENTS)} required members.
    Requirements not found:
        {not_found}
            ''')
        
        # Update internal attributes
        self.detected_requirements = detected_requirements
        self.optional_requirements = optional_requirements

        self.tick_callback = None
        if 'tick' in optional_requirements: # Add this function as a callback to avoid map search when ticking
            self.tick_callback = optional_requirements['tick']

        self.state = NodeState.ACTIVE

    def tick(self, arg: Any):
        """
        Ticks the node
        @param arg Argument that will be passed to the node's tick method
        @return True if the node was ticked, False it the node produced an exception
        """
        if self.state == NodeState.ACTIVE and self.tick_callback != None:
            try:
                self.tick_callback(arg)
                return True
            except Exception as e:
                self.state = NodeState.CRASHED
                print(f'''
    Node {self.filename} crashed ticking
    If hot reloading is enabled, fix the issue and save the file
    Exception:
        {traceback.format_exc()}
                ''')
                return False

    def is_tickable(self):
        """
        Checks if the node can be ticked
        @details
        A node is tickable if it defines the tick method
        """
        return 'tick' in self.optional_requirements

    def init(self, arg):
        """
        Initializes the node (returning it's configuration)
        @param arg Argument that will be passed to the node init method
        @return Configuration of the node (if the node crashed returns default configuration with name=crashed)
        """
        try:
            node_config = self.detected_requirements['init'](arg)
            if not isinstance(node_config, Configuration):
                raise RuntimeError(f'''
        Configuration returned from node {self.filename} is not valid
        Returned value {node_config} of type {type(node_config)} instead of egoros.node.Configuration
                ''')

            return node_config
        except Exception as e:
            self.state = NodeState.CRASHED
            print(f'''
    Node {self.filename} crashed while initializing
    If hot reloading is enabled, fix the issue and save the file
    Exception:
        {traceback.format_exc()}
            ''')

        return Configuration('crashed')
