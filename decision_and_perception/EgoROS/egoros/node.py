from dataclasses import dataclass
import importlib.abc
import re
from types import ModuleType
from typing import Callable, cast
import importlib.util
import os.path
import inspect

@dataclass
class Loader:
    expr: re.Pattern[str]
    loader: Callable[[str], ModuleType]

@dataclass
class Requirement:
    name: str
    condition: Callable

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

REQUIREMENTS = [
    Requirement(
        name='init',
        condition=lambda e: callable(e[1]) and e[0] == 'init' 
    )
]

class Node:
    def __init__(self, filename: str) -> None:
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

        # Check if module is a valid node
        detected_requirements = {}
        for member in inspect.getmembers(self.mod):
            for requirement in REQUIREMENTS:
                if requirement.condition(member):
                    detected_requirements[requirement.name] = member[1]

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

    def init(self, arg):
        self.detected_requirements['init'](arg)
