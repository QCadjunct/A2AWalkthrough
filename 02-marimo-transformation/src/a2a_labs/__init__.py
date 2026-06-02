"""Shared standards layer for the Agent-to-Agent (A2A) Walkthrough labs.

Provides Enums (replacing free-form strings), a Pydantic Version 2 (V2)
``Settings`` object with a Gemini / Vertex Artificial Intelligence (Vertex AI)
toggle, and decorators for professional lab-step structure.
"""

from a2a_labs.config import Settings, get_settings, setup_env
from a2a_labs.decorators import async_lab_step, lab_step, requires
from a2a_labs.cascade import Cascade, CascadeKey
from a2a_labs.registry import MODEL_REGISTRY, MODELS, vendors
from a2a_labs.registry import models_for as registry_models_for
from a2a_labs.messages import ModelMessage
from a2a_labs.paths import DATA_DIR, data_path
from a2a_labs.executor import GovernedExecutor, make_policy_executor
from a2a_labs.enums import (
    AGENT_PORTS,
    AgentPort,
    AgentRole,
    OverrideDefault,
    Provider,
    TransportMode,
)
from a2a_labs.fqsn import (
    FQSN,
    DatabaseAdapter,
    FilesystemAdapter,
    SkillResolver,
    SkillTrifecta,
)
from a2a_labs.tool_menu import (
    Triplet,
    ToolMenu,
    menu_for,
)
from a2a_labs.workspace import (
    MessageDirection,
    ResponseStatus,
    WorkspaceEnvelope,
    WorkspaceResponseObject,
    WorkspaceState,
    pair_hash,
)
from a2a_labs.vendors import (
    VENDOR_MODELS,
    Model,
    Vendor,
    VendorModel,
    VendorModelSelection,
    models_for,
)
from a2a_labs.locking import (
    ReentrantChainState,
    make_pessimistic_chain,
    run_serially_reentrant,
)

__all__ = [
    "AGENT_PORTS",
    "AgentPort",
    "AgentRole",
    "DATA_DIR",
    "GovernedExecutor",
    "MODEL_REGISTRY",
    "MessageDirection",
    "Model",
    "ModelMessage",
    "Provider",
    "ReentrantChainState",
    "ResponseStatus",
    "Settings",
    "TransportMode",
    "VENDOR_MODELS",
    "Vendor",
    "VendorModel",
    "VendorModelSelection",
    "models_for",
    "WorkspaceEnvelope",
    "WorkspaceResponseObject",
    "WorkspaceState",
    "async_lab_step",
    "data_path",
    "make_policy_executor",
    "Cascade",
    "CascadeKey",
    "MODELS",
    "get_settings",
    "lab_step",
    "make_pessimistic_chain",
    "pair_hash",
    "registry_models_for",
    "requires",
    "run_serially_reentrant",
    "setup_env",
    "vendors",
    "OverrideDefault",
    "FQSN",
    "SkillResolver",
    "SkillTrifecta",
    "FilesystemAdapter",
    "DatabaseAdapter",
    "Triplet",
    "ToolMenu",
    "menu_for",
]
__version__ = "0.1.0"
