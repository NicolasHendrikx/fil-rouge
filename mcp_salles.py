"""Serveur MCP « salles » : expose l'état des salles de l'API Salles comme outil pour un agent."""

import os

import httpx
from mcp.server import MCPServer

API_URL = os.environ.get("SALLES_API_URL", "http://127.0.0.1:8000")

mcp = MCPServer("salles")


@mcp.tool()
def room_status(room_id: int, at: str) -> dict:
    """État d'une salle à un instant donné : libre ou occupée, par qui et jusqu'à quand.

    at : instant local sans fuseau, au format AAAA-MM-JJTHH:MM:SS.
    """
    response = httpx.get(f"{API_URL}/rooms/{room_id}/status", params={"at": at}, timeout=5)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run()
