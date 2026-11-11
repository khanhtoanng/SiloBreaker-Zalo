"""Compatibility exports; implementation lives in the layered package."""

from .adapters.ollama import (
    NoRedirect as NoRedirect,
)
from .adapters.ollama import (
    OllamaClient as OllamaClient,
)
from .adapters.ollama import (
    OllamaPolicy as OllamaPolicy,
)
from .adapters.ollama import (
    local_url as local_url,
)
