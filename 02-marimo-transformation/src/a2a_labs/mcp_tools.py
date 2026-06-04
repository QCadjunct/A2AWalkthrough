"""Model Context Protocol (MCP) tools and servers for the A2A Walkthrough.

Standing rule (mirrors enums.py): free-form strings are replaced by Enums
wherever a value is drawn from a fixed, known set. In the upstream provider
agent the MCP tool name ``"find_healthcare_providers"`` is a free-form string
repeated three times (the connection key, the advertised skill id, and inside
the system prompt) while the MCP server itself registers the tool as
``list_doctors`` — a mismatch held together only by convention. This module
removes that: an MCP tool is a closed Enum member whose value IS the server's
real tool name, and which owns its server, transport, and launch command.

A prompt is input, not hardcoding, so prompts are not modelled here. The TOOL
NAME, however, is drawn from a fixed known set — so it is an Enum.

KISS here means "Keep It Simple and Standard": standard-library ``enum.StrEnum``
with ``@unique``, and — Single Responsibility Principle (SRP) — each member owns
the facts derived from it via ``@property`` and small composing methods, the way
``AgentRole`` owns its port and ``Provider`` owns its prefix in enums.py.

Every acronym is spelled out on first use:
* MCP   - Model Context Protocol
* A2A   - Agent-to-Agent (protocol)
* SRP   - Single Responsibility Principle
"""

from __future__ import annotations

from enum import StrEnum, unique

from a2a_labs.enums import TransportMode


@unique
class McpServer(StrEnum):
    """An MCP server process the labs can launch.

    Each member owns its launch facts: the script that runs it, the transport
    it speaks, and the composed command to spawn it. Callers ask the member;
    they do not rebuild the command — the server builds it, the way Provider
    builds its own model prefix in enums.py.
    """

    DOCTOR = "doctorserver"  # matches FastMCP("doctorserver") in mcpserver.py

    @property
    def script(self) -> str:
        """The script that runs this server — owned here, not re-typed."""
        return {McpServer.DOCTOR: "mcpserver.py"}[self]

    @property
    def transport(self) -> TransportMode:
        """The transport this server speaks — an Enum, not a literal."""
        return {McpServer.DOCTOR: TransportMode.STDIO}[self]

    def stdio_command(self) -> list[str]:
        """Compose the argv to spawn this server. The server owns the format."""
        return ["uv", "run", self.script]


@unique
class McpTool(StrEnum):
    """A callable MCP tool. Its value IS the wire tool name — one source.

    The member owns which server provides it and its connection key. Because the
    key is the value, the advertised name and the server's real tool name cannot
    drift — the failure the upstream literal invited is structurally impossible.
    """

    LIST_DOCTORS = "list_doctors"  # the actual @mcp.tool name in mcpserver.py

    @property
    def server(self) -> McpServer:
        """Which MCP server provides this tool — owned by the tool."""
        return {McpTool.LIST_DOCTORS: McpServer.DOCTOR}[self]

    @property
    def connection_key(self) -> str:
        """The MultiServerMCPClient key — the tool's own name, so it cannot drift."""
        return self.value


# Derived from the tools themselves — no separately maintained mapping to drift.
SERVER_TOOLS: dict[McpServer, tuple[McpTool, ...]] = {
    server: tuple(t for t in McpTool if t.server is server) for server in McpServer
}
