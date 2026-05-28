# import os 
# import asyncio
# from loguru import logger
# from langchain_core.tools import BaseTool
# from langchain_mcp_adapters.client import MultiServerMCPClient

# MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")  
# MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001") 
# MCP_SERVER_PATH = os.getenv("MCP_SERVER_PATH","mcp_server/server.py") 


# def get_mcp_server_config() -> dict:
#     if MCP_TRANSPORT == "sse":
#         return {
#             "medical-tools": {
#                 "transport": "sse",
#                 "url": f"{MCP_SERVER_URL}/sse",
#             }
#         }
#     else:
#         return {
#             "medical-tools": {
#                 "transport": "stdio",
#                 "command": "python",
#                 "args": [MCP_SERVER_PATH],
#                 "env": None,
#             }
#         }

# async def get_mcp_tools_async() -> list[BaseTool]:
#     """
#     Récupère les tools depuis le serveur MCP (version async).

#     Retourne une liste de BaseTool LangChain prêts à être utilisés
#     dans llm.bind_tools() ou ToolNode.

#     Utilisation dans un agent async :
#         tools = await get_mcp_tools_async()
#         llm_with_tools = llm.bind_tools(tools)
#     """
#     config=get_mcp_server_config()
#     logger.info(f"[MCPClient] Connexion au serveur MCP via {MCP_TRANSPORT} : {config}")
#     async with MultiServerMCPClient(config) as client:
#          tools=client.get_tools()
#          tool_names=[t.name for t in tools]
#          logger.info(f"[MCPClient] {len(tools)} tools récupérés : {tool_names}")
#          return tools
    


# # def get_mcp_tools_sync() -> list[BaseTool]:
# #     """
# #     Version synchrone — utilisée dans les nodes LangGraph synchrones.
# #     Crée une nouvelle boucle event loop si nécessaire.
# #     """
# #     try:
# #         loop = asyncio.get_event_loop()
# #         if loop.is_running():
# #             # Dans FastAPI async, on ne peut pas appeler run_until_complete
# #             # → utiliser asyncio.run_coroutine_threadsafe ou un executor
# #             import concurrent.futures
# #             with concurrent.futures.ThreadPoolExecutor() as pool:
# #                 future = pool.submit(asyncio.run, get_mcp_tools_async())
# #                 return future.result(timeout=30)
# #         else:
# #             return loop.run_until_complete(get_mcp_tools_async())
# #     except Exception as e:
# #         logger.error(f"[MCPClient] Erreur récupération tools MCP : {e}")
# #         logger.warning("[MCPClient] Fallback sur les tools locaux...")
# #         # Fallback : utiliser les tools locaux si le serveur MCP est indisponible
# #         # from backend.app.tools.patient_tools import patient_tools
# #         # from backend.app.tools.care_tools import care_tools
# #         # return patient_tools + care_tools
# def get_mcp_tools_sync() -> list[BaseTool]:
#     """
#     Version synchrone — utilisée dans les nodes LangGraph synchrones.
 
#     Problème réel (visible dans vos logs) :
#       LangGraph exécute les nodes dans un thread worker 'asyncio_0'.
#       Dans ce thread, asyncio.get_event_loop() lève RuntimeError
#       "There is no current event loop in thread 'asyncio_0'"
#       car Python 3.10+ ne crée plus de boucle implicite dans les threads secondaires.
 
#     Solution : toujours créer un thread propre avec asyncio.run().
#       asyncio.run() crée SA PROPRE boucle event loop, l'exécute, puis la détruit.
#       Ça fonctionne dans n'importe quel thread, qu'il ait une boucle ou non.
#     """
#     import concurrent.futures
 
#     def _run_in_clean_thread():
#         # asyncio.run() crée une nouvelle boucle isolée — pas de conflit
#         return asyncio.run(get_mcp_tools_async())
 
#     try:
#         # Toujours passer par un thread propre pour éviter les conflits de boucle.
#         # ThreadPoolExecutor crée un thread vierge sans event loop préexistante.
#         with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
#             future = pool.submit(_run_in_clean_thread)
#             tools = future.result(timeout=30)
#             logger.info(f"[MCPClient] {len(tools)} tools MCP chargés depuis le serveur ✓")
#             return tools
 
#     except Exception as e:
#         logger.error(f"[MCPClient] Erreur connexion serveur MCP : {e}")
#         logger.error("[MCPClient] Vérifiez que 'python mcp_server/server.py' tourne sur le port 8001")
#         # Sans fallback : on lève l'erreur pour forcer la correction
#         # (commentez le raise et décommentez le fallback si vous voulez tolérer l'absence du serveur)
#         raise RuntimeError(
#             f"Impossible de contacter le serveur MCP ({MCP_SERVER_URL}). "
#             f"Lancez : python mcp_server/server.py\nErreur originale : {e}"
#         )
 
# # ── Cache des tools (évite de se reconnecter à chaque appel) ──────────────────
# _tools_cache: list[BaseTool] | None = None


# def get_cached_mcp_tools() -> list[BaseTool]:
#     """
#     Retourne les tools en cache ou les récupère si nécessaire.
#     Le cache est invalidé au redémarrage du process (acceptable pour dev).
#     Pour prod : ajouter une logique de TTL ou de refresh.
#     """
#     global _tools_cache
#     if _tools_cache is None:
#         logger.info("[MCPClient] Initialisation du cache des tools MCP...")
#         _tools_cache = get_mcp_tools_sync()
#     return _tools_cache


# def invalidate_tools_cache():
#     """Force le re-chargement des tools depuis le serveur MCP."""
#     global _tools_cache
#     _tools_cache = None
#     logger.info("[MCPClient] Cache des tools MCP invalidé.")
  

import os
import asyncio
import concurrent.futures
from loguru import logger
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient


# ── Configuration ─────────────────────────────────────────────────────────────
MCP_TRANSPORT  = os.getenv("MCP_TRANSPORT",  "sse")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
MCP_SERVER_PATH = os.getenv("MCP_SERVER_PATH", "mcp_server/server.py")


def get_mcp_server_config() -> dict:
    """Construit la config selon le transport choisi (sse ou stdio)."""
    if MCP_TRANSPORT == "sse":
        return {
            "medical-tools": {
                "transport": "sse",
                "url": f"{MCP_SERVER_URL}/sse",
            }
        }
    else:
        return {
            "medical-tools": {
                "transport": "stdio",
                "command": "python",
                "args": [MCP_SERVER_PATH],
                "env": None,
            }
        }


# async def get_mcp_tools_async() -> list[BaseTool]:
    # """
    # Récupère les tools depuis le serveur MCP — version async.
    # Retourne des BaseTool LangChain utilisables dans llm.bind_tools().
    # """
    # config = get_mcp_server_config()
    # logger.info(f"[MCPClient] Connexion MCP via {MCP_TRANSPORT} → {MCP_SERVER_URL}")

    # async with MultiServerMCPClient(config) as client:
    #     tools = client.get_tools()
    #     logger.info(f"[MCPClient] {len(tools)} tools récupérés : {[t.name for t in tools]}")
    #     return tools
async def get_mcp_tools_async() -> list[BaseTool]:
    """
    Récupère les tools depuis le serveur MCP — version async.
    Compatible langchain-mcp-adapters >= 0.1.0
    """
    config = get_mcp_server_config()
    logger.info(f"[MCPClient] Connexion MCP via {MCP_TRANSPORT} → {MCP_SERVER_URL}")

    # ✅ Nouvelle API : plus de context manager
    client = MultiServerMCPClient(config)
    tools = await client.get_tools()

    logger.info(f"[MCPClient] {len(tools)} tools récupérés : {[t.name for t in tools]}")
    return tools

def get_mcp_tools_sync() -> list[BaseTool]:
    """
    Version synchrone — appelée depuis les nodes LangGraph.

    Pourquoi ThreadPoolExecutor + asyncio.run() ?
    ─────────────────────────────────────────────
    LangGraph exécute ses nodes dans un thread worker ('asyncio_0').
    Dans ce thread, il n'y a PAS de boucle event loop.
    Depuis Python 3.10, asyncio.get_event_loop() dans un thread sans boucle
    lève RuntimeError au lieu de créer une boucle silencieusement.

    Solution : soumettre la coroutine dans un thread PROPRE via ThreadPoolExecutor.
    asyncio.run() crée sa propre boucle, l'exécute, puis la détruit.
    Ça fonctionne dans n'importe quel thread, avec ou sans boucle existante.
    """
    def _run_in_clean_thread():
        return asyncio.run(get_mcp_tools_async())

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_in_clean_thread)
            tools = future.result(timeout=30)
            logger.info(f"[MCPClient] {len(tools)} tools MCP chargés ✓")
            return tools

    except Exception as e:
        logger.error(f"[MCPClient] Impossible de contacter le serveur MCP : {e}")
        logger.error("[MCPClient] → Vérifiez que 'python mcp_server/server.py' tourne sur le port 8001")
        raise RuntimeError(
            f"Serveur MCP non disponible ({MCP_SERVER_URL}). "
            f"Lancez : python mcp_server/server.py\n"
            f"Erreur : {e}"
        )


# ── Cache des tools ────────────────────────────────────────────────────────────
# Initialisé au premier appel, réutilisé ensuite.
# Invalidé uniquement au redémarrage du process.
_tools_cache: list[BaseTool] | None = None


def get_cached_mcp_tools() -> list[BaseTool]:
    """
    Retourne les tools en cache ou les récupère depuis le serveur MCP.
    Un seul appel réseau par démarrage de process.
    """
    global _tools_cache
    if _tools_cache is None:
        logger.info("[MCPClient] Initialisation du cache des tools MCP...")
        _tools_cache = get_mcp_tools_sync()
    return _tools_cache


def invalidate_tools_cache():
    """Force le rechargement des tools au prochain appel."""
    global _tools_cache
    _tools_cache = None
    logger.info("[MCPClient] Cache invalidé — reconnexion au prochain appel.")




def invoke_tool_sync(tool_name: str, inputs: dict):
    """
    Invoque un tool MCP de façon synchrone.
    Même pattern que get_mcp_tools_sync() — thread propre avec asyncio.run().
    """
    tools = get_cached_mcp_tools()
    tool = next((t for t in tools if t.name == tool_name), None)
    if tool is None:
        raise ValueError(f"Tool '{tool_name}' introuvable dans le serveur MCP")

    def _run_in_clean_thread():
        return asyncio.run(tool.ainvoke(inputs))  # ✅ ainvoke dans thread propre

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run_in_clean_thread)
        return future.result(timeout=30)    