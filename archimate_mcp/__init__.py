"""archimate-mcp: ArchiMate model engine + MCP Server + A2A Server."""

import importlib
import inspect
from typing import Any

__version__ = "0.2.0"
__all__: list[str] = []

CORE_MODULES = ["archimate_mcp.api_client"]
OPTIONAL_MODULES = {
    "archimate_mcp.mcp_server": "mcp",
}


def _expose_members(module):
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            globals()[name] = obj
            if name not in __all__:
                __all__.append(name)


for module_name in CORE_MODULES:
    module = importlib.import_module(module_name)
    _expose_members(module)

_loaded_optional_modules: dict[str, Any] = {}


def _import_module_safely(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


#: Sentinel attribute names understood as "is this optional module importable?"
#: queries, mapped to a substring identifying the module they probe.
_AVAILABILITY_FLAGS = {
    "_MCP_AVAILABLE": "mcp_server",
    "_AGENT_AVAILABLE": "agent_server",
}


def _optional_module_available(module_substring: str) -> bool:
    module_key = next((k for k in OPTIONAL_MODULES if module_substring in k), None)
    return _import_module_safely(module_key) is not None if module_key else False


def _ensure_optional_module_loaded(module_name: str):
    if module_name not in _loaded_optional_modules:
        module = _import_module_safely(module_name)
        if module is not None:
            _loaded_optional_modules[module_name] = module
            _expose_members(module)
    return _loaded_optional_modules.get(module_name)


def _resolve_optional_attribute(name: str) -> Any:
    for module_name in OPTIONAL_MODULES:
        module = _ensure_optional_module_loaded(module_name)
        if module is not None and hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str) -> Any:
    if name in _AVAILABILITY_FLAGS:
        return _optional_module_available(_AVAILABILITY_FLAGS[name])
    return _resolve_optional_attribute(name)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
