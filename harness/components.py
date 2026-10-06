"""Load a competition-local implementation by module:class specification."""

from copy import deepcopy
import importlib


def create_component(package: str, spec: str, config: dict, methods: tuple[str, ...]):
    if not isinstance(spec, str) or spec.count(":") != 1:
        raise ValueError("Implementation must be specified as module:class")
    module_name, name = spec.split(":")
    if not all(part.isidentifier() for part in module_name.split(".")) or not name.isidentifier():
        raise ValueError("Use Python module and class names in the implementation setting")
    module = importlib.import_module(f"{package}.{module_name}")
    factory = getattr(module, name, None)
    if not callable(factory):
        raise ValueError(f"Implementation factory not found: {spec}")
    component = factory(deepcopy(config))
    for method in methods:
        if not callable(getattr(component, method, None)):
            raise TypeError(f"{spec} must implement {method}()")
    return component
