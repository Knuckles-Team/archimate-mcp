"""Client factory for the ArchiMate model engine.

Archi has no remote server, so there is nothing to authenticate against.
``get_client`` simply points an :class:`~archimate_mcp.api_client.Api` (the
ArchiMate model engine) at the model file named by ``ARCHI_MODEL_PATH``,
loading it if it already exists.
"""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting

from archimate_mcp.api_client import Api

logger = get_logger(__name__)


def get_client() -> Api:
    """Return an :class:`Api` bound to ``ARCHI_MODEL_PATH``.

    The model file is auto-loaded when present; otherwise an empty in-memory
    model is created. Honors ``ARCHI_MODEL_PATH`` (default
    ``./model.archimate``).
    """
    model_path = setting("ARCHI_MODEL_PATH", "./model.archimate")
    return Api(model_path=model_path)
