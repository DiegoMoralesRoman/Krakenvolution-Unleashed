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
    expr: re.Pattern[str]
    loader: Callable[[str], ModuleType]

@dataclass
class Requirement:
    name: str
    condition: Callable

@dataclass
class Configuration:
    name: str
    defered: bool = False

def normal_loader(path: str):
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
    pass

def package_loader(path: str):
    pass

LOADERS = [
    Loader(
        expr=re.compile('^.*\.py$'),
        loader=normal_loader
    ),
    Loader(
        expr=re.compile('^.*\.so$'),
        loader=dynamic_loader
    ),
    Loader(
        expr=re.compile('^(?!.*\..*$).+$'),
        loader=package_loader
    )
]

# TODO: check if the methods have sufficient arguments
REQUIREMENTS = [
    Requirement(
        name='init',
        condition=lambda e: callable(e[1]) and e[0] == 'init' 
    )
]

OPTIONAL_REQUIREMENTS = [
    Requirement(
        name='tick',
        condition=lambda e: callable(e[1]) and e[0] == 'tick'
    )
]

class Node:
    def __init__(self, filename: str) -> None:
        self.state = NodeState.CRASHED
        self.mod = None
        self.filename = filename

        for loader in LOADERS:
            # Check if a defined loaders is able to load the module
            if re.match(loader.expr, filename):
                self.mod = loader.loader(filename)
                break

        if not self.mod:
            raise ImportError(f'''
    Module of type {filename} 
    has no defined loaders
            ''')

        # Optional members

        # Check if module is a valid node
        detected_requirements = {}
        optional_requirements = {}
        for member in inspect.getmembers(self.mod):
            for requirement in REQUIREMENTS:
                if requirement.condition(member):
                    detected_requirements[requirement.name] = member[1]

            for requirement in OPTIONAL_REQUIREMENTS:
                if requirement.condition(member):
                    optional_requirements[requirement.name] = member[1]

        if len(detected_requirements) != len(REQUIREMENTS):
            not_found = ''
            for req in filter(lambda e: e.name not in detected_requirements.keys(), REQUIREMENTS):
                not_found += f'{req.name}\n'

            raise ImportError(f'''
    Could not find all requirements for the module {filename}
    Found {len(detected_requirements)} out of {len(REQUIREMENTS)} required members.
    Requirements not found:
        {not_found}
            ''')
        
        self.detected_requirements = detected_requirements
        self.optional_requirements = optional_requirements

        self.tick_callback = None
        if 'tick' in optional_requirements:
            self.tick_callback = optional_requirements['tick']

        self.state = NodeState.ACTIVE

    def tick(self, arg: Any):
        if self.state == NodeState.ACTIVE and self.tick_callback != None:
            try:
                self.tick_callback(arg)
            except Exception as e:
                self.state = NodeState.CRASHED
                print(f'''
    Node {self.filename} crashed ticking
    If hot reloading is enabled, fix the issue and save the file
    Exception:
        {traceback.format_exc()}
                ''')

    def is_tickable(self):
        return 'tick' in self.optional_requirements

    def init(self, arg):
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
