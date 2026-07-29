"""Work around a CrewAI 1.14.4 bug that makes hyphenated MCP tools unreachable.

During discovery, CrewAI stores each remote tool under a sanitized name
(``resolve-library-id`` becomes ``resolve_library_id``) and then sends that
sanitized name back to the server when calling the tool. Servers that use
hyphens in tool names — Context7 among them — never receive a name they
recognize, so those tools silently fail.

This module replaces ``MCPToolResolver._resolve_external`` with a version
that keeps the server's original tool name for the call while still
exposing the sanitized name to the model. Importing the module applies the
patch as a side effect; import it before any agent is constructed.

Re-verify on every crewai upgrade: if upstream fixes the bug, delete this
file and the import in ``main.py``.
"""

import asyncio
from typing import Any, cast

from crewai.mcp.tool_resolver import (
    MCP_CONNECTION_TIMEOUT,
    MCP_DISCOVERY_TIMEOUT,
    MCPToolResolver,
)
from crewai.tools.base_tool import BaseTool
from crewai.tools.mcp_tool_wrapper import MCPToolWrapper
from crewai.utilities.string_utils import sanitize_tool_name


def _resolve_external(self: MCPToolResolver, mcp_ref: str) -> list[BaseTool]:
    """Resolve an HTTPS MCP server URL into tools, preserving tool names.

    Args:
        self: The resolver instance being patched.
        mcp_ref: Server URL, optionally suffixed with ``#tool_name`` to
            select a single tool.

    Returns:
        The wrapped remote tools, or an empty list if the server is
        unreachable.
    """
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    if "#" in mcp_ref:
        server_url, specific_tool = mcp_ref.split("#", 1)
    else:
        server_url, specific_tool = mcp_ref, None

    server_params = {"url": server_url}
    server_name = self._extract_server_name(server_url)
    sanitized_specific = sanitize_tool_name(specific_tool) if specific_tool else None

    async def _discover() -> list[Any]:
        async with (
            streamablehttp_client(server_url) as (read, write, _),
            ClientSession(read, write) as session,
        ):
            await asyncio.wait_for(session.initialize(), timeout=MCP_CONNECTION_TIMEOUT)
            listed = await asyncio.wait_for(
                session.list_tools(),
                timeout=MCP_DISCOVERY_TIMEOUT - MCP_CONNECTION_TIMEOUT,
            )
            return list(listed.tools)

    async def _list_mcp_tools() -> list[Any]:
        # Discovery runs in the foreground of a crew run, so it keeps the same
        # bounds as the method being replaced; without them a stalled server
        # hangs the crew with no output.
        return await asyncio.wait_for(_discover(), timeout=MCP_DISCOVERY_TIMEOUT)

    try:
        mcp_tools = asyncio.run(_list_mcp_tools())
    except Exception as exc:  # noqa: BLE001 — any transport or protocol failure degrades to no tools
        self._logger.log("warning", f"Failed to connect to MCP server {server_url}: {exc}")
        return []

    tools: list[BaseTool] = []
    for mcp_tool in mcp_tools:
        sanitized = sanitize_tool_name(mcp_tool.name)
        if sanitized_specific and sanitized != sanitized_specific:
            continue
        args_schema = None
        if getattr(mcp_tool, "inputSchema", None):
            args_schema = self._json_schema_to_pydantic(sanitized, mcp_tool.inputSchema)
        schema = {
            "description": getattr(mcp_tool, "description", ""),
            "args_schema": args_schema,
        }
        try:
            wrapper = MCPToolWrapper(
                mcp_server_params=server_params,
                tool_name=sanitized,
                tool_schema=schema,
                server_name=server_name,
            )
            # Restore the server-side name so call_tool reaches the real tool.
            wrapper._original_tool_name = mcp_tool.name
            tools.append(wrapper)
        except Exception as exc:  # noqa: BLE001 — skip a malformed tool, keep the rest
            self._logger.log("warning", f"Failed to wrap MCP tool {sanitized}: {exc}")

    return cast(list[BaseTool], tools)


MCPToolResolver._resolve_external = _resolve_external
