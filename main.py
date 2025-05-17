import asyncio
import websockets
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

# --- Configuration ---
SOLANA_WS_URL = "wss://api.devnet.solana.com/"
MCP_HOST = "127.0.0.1"
MCP_PORT = 8081
MCP_SERVER_NAME = "solana-realtime-monitor-mcp"

mcp = FastMCP(MCP_SERVER_NAME, host=MCP_HOST, port=MCP_PORT)

@mcp.tool(
    description="Subscribes to account changes for a given Solana account public key and streams updates as JSON strings."
)
async def subscribe_to_account_updates(
    account_pubkey: str,
    commitment: str = "confirmed",
    encoding: str = "base64"
) -> AsyncGenerator[str, None]:
    """
    Streams real-time notifications for account changes on the Solana blockchain.

    Args:
        account_pubkey: The base58 encoded public key of the account to monitor.
        commitment: The commitment level ('processed', 'confirmed', 'finalized').
        encoding: The encoding for account data ('base64', 'base58', 'jsonParsed', 'base64+zstd').

    Example:
        - account_pubkey="So11111111111111111111111111111111111111112" (SOL mint address)
        - account_pubkey="...", commitment="finalized", encoding="jsonParsed"

    Yields:
        JSON string notifications from the Solana WebSocket.
        The first yielded message will contain the Solana subscription ID.
    """
    subscription_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "accountSubscribe",
        "params": [
            account_pubkey,
            {
                "encoding": encoding,
                "commitment": commitment
            }
        ]
    }
    try:
        async with websockets.connect(SOLANA_WS_URL) as websocket:
            await websocket.send(json.dumps(subscription_request))

            # First response is the subscription confirmation with a Solana subscription ID
            initial_response_str = await websocket.recv()
            initial_data = json.loads(initial_response_str)

            if 'result' in initial_data and isinstance(initial_data['result'], int):
                solana_subscription_id = initial_data['result']
                yield json.dumps({
                    "type": "subscription_started",
                    "event": "account_update",
                    "account_pubkey": account_pubkey,
                    "solana_subscription_id": solana_subscription_id,
                    "message": f"Successfully subscribed to account {account_pubkey}."
                })
            else:
                error_message = f"Subscription failed or unexpected response for account {account_pubkey}: {json.dumps(initial_data)}"
                yield json.dumps({"type": "error", "message": error_message})
                return

            # Listen for updates
            while True:
                try:
                    response_str = await websocket.recv()
                    yield response_str
                except websockets.exceptions.ConnectionClosed:
                    yield json.dumps({
                        "type": "subscription_ended",
                        "event": "account_update",
                        "account_pubkey": account_pubkey,
                        "message": "WebSocket connection closed."
                    })
                    break
                except Exception as e:
                    error_message = f"Error receiving update for account {account_pubkey}: {str(e)}"
                    yield json.dumps({"type": "error", "message": error_message})
                    break
    except websockets.exceptions.InvalidURI:
        yield json.dumps({"type": "error", "message": f"Invalid WebSocket URI: {SOLANA_WS_URL}"})
    except websockets.exceptions.WebSocketException as e:
        yield json.dumps({"type": "error", "message": f"WebSocket connection error for account {account_pubkey}: {str(e)}"})
    except Exception as e:
        yield json.dumps({"type": "error", "message": f"An unexpected error occurred in subscribe_to_account_updates for {account_pubkey}: {str(e)}"})

@mcp.tool(
    description="Subscribes to transaction signature status for a given Solana transaction signature and streams updates as JSON strings."
)
async def subscribe_to_signature_status(
    signature: str,
    commitment: str = "confirmed"
) -> AsyncGenerator[str, None]:
    """
    Streams real-time notifications for a specific transaction signature on Solana.
    The stream usually ends after the transaction reaches the specified commitment or fails.

    Args:
        signature: The base58 encoded transaction signature to monitor.
        commitment: The commitment level ('processed', 'confirmed', 'finalized').

    Example:
        - signature="5siggingDPpHBsAgV5yq7nYKEdY68sLkWyNycAbygXGFZ61LpZqWfEGwsUeTNs8XakmS2oSVhFdfMXWMyy9tjd7B"
        - signature="...", commitment="finalized"

    Yields:
        JSON string notifications from the Solana WebSocket.
        The first yielded message will contain the Solana subscription ID.
    """
    subscription_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "signatureSubscribe",
        "params": [
            signature,
            {"commitment": commitment}
        ]
    }
    try:
        async with websockets.connect(SOLANA_WS_URL) as websocket:
            await websocket.send(json.dumps(subscription_request))
            initial_response_str = await websocket.recv()
            initial_data = json.loads(initial_response_str)

            if 'result' in initial_data and isinstance(initial_data['result'], int):
                solana_subscription_id = initial_data['result']
                yield json.dumps({
                    "type": "subscription_started",
                    "event": "signature_update",
                    "signature": signature,
                    "solana_subscription_id": solana_subscription_id,
                    "message": f"Successfully subscribed to signature {signature}."
                })
            else:
                error_message = f"Subscription failed for signature {signature}: {json.dumps(initial_data)}"
                yield json.dumps({"type": "error", "message": error_message})
                return

            while True:
                try:
                    response_str = await websocket.recv()
                    yield response_str
                except websockets.exceptions.ConnectionClosed:
                    yield json.dumps({
                        "type": "subscription_ended",
                        "event": "signature_update",
                        "signature": signature,
                        "message": "WebSocket connection closed (often expected after final signature notification)."
                    })
                    break
                except Exception as e:
                    error_message = f"Error receiving update for signature {signature}: {str(e)}"
                    yield json.dumps({"type": "error", "message": error_message})
                    break
    except websockets.exceptions.InvalidURI:
        yield json.dumps({"type": "error", "message": f"Invalid WebSocket URI: {SOLANA_WS_URL}"})
    except websockets.exceptions.WebSocketException as e:
        yield json.dumps({"type": "error", "message": f"WebSocket connection error for signature {signature}: {str(e)}"})
    except Exception as e:
        yield json.dumps({"type": "error", "message": f"An unexpected error occurred in subscribe_to_signature_status for {signature}: {str(e)}"})

@mcp.tool(
    description="Subscribes to logs emitted by Solana programs and streams them as JSON strings. Filter by 'all' or specific 'mentions' (program IDs)."
)
async def subscribe_to_logs(
    filter_criteria: Dict[str, Any],  # Example: {"mentions": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]}, or {"all": True}
    commitment: str = "confirmed"
) -> AsyncGenerator[str, None]:
    """
    Streams real-time log notifications from the Solana blockchain.

    Args:
        filter_criteria: A dictionary specifying the filter.
                         For all logs: `{"all": True}` (or just ` "all" ` as per RPC docs for first param)
                         To filter by program ID(s) or other mentioned accounts: `{"mentions": ["PublicKey1", "PublicKey2"]}`
        commitment: The commitment level ('processed', 'confirmed', 'finalized').

    Example:
        - filter_criteria={"mentions": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]} (SPL Token Program)
        - filter_criteria={"all": True}, commitment="finalized"
          (Note: Solana RPC expects first param of logsSubscribe to be the filter object or "all")

    Yields:
        JSON string log notifications from the Solana WebSocket.
        The first yielded message will contain the Solana subscription ID.
    """
    params_list: List[Any]
    filter_description_for_log: str

    if "all" in filter_criteria and filter_criteria["all"] is True:
        params_list = ["all"]
        filter_description_for_log = "all logs"
    elif "mentions" in filter_criteria and isinstance(filter_criteria["mentions"], list):
        params_list = [{"mentions": filter_criteria["mentions"]}]
        filter_description_for_log = f"logs mentioning: {', '.join(filter_criteria['mentions'])}"
    else:
        yield json.dumps({
            "type": "error",
            "message": "Invalid filter_criteria. Use {'all': True} or {'mentions': ['PK1', ...]}"
        })
        return

    subscription_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": params_list + [{"commitment": commitment}]
    }

    try:
        async with websockets.connect(SOLANA_WS_URL) as websocket:
            await websocket.send(json.dumps(subscription_request))
            initial_response_str = await websocket.recv()
            initial_data = json.loads(initial_response_str)

            if 'result' in initial_data and isinstance(initial_data['result'], int):
                solana_subscription_id = initial_data['result']
                yield json.dumps({
                    "type": "subscription_started",
                    "event": "logs_update",
                    "filter": filter_criteria,
                    "solana_subscription_id": solana_subscription_id,
                    "message": f"Successfully subscribed to {filter_description_for_log}."
                })
            else:
                error_message = f"Log subscription failed for {filter_description_for_log}: {json.dumps(initial_data)}"
                yield json.dumps({"type": "error", "message": error_message})
                return

            while True:
                try:
                    response_str = await websocket.recv()
                    yield response_str
                except websockets.exceptions.ConnectionClosed:
                    yield json.dumps({
                        "type": "subscription_ended",
                        "event": "logs_update",
                        "filter": filter_criteria,
                        "message": "WebSocket connection closed for logs subscription."
                    })
                    break
                except Exception as e:
                    error_message = f"Error receiving log update for {filter_description_for_log}: {str(e)}"
                    yield json.dumps({"type": "error", "message": error_message})
                    break
    except websockets.exceptions.InvalidURI:
        yield json.dumps({"type": "error", "message": f"Invalid WebSocket URI: {SOLANA_WS_URL}"})
    except websockets.exceptions.WebSocketException as e:
        yield json.dumps({"type": "error", "message": f"WebSocket connection error for logs ({filter_description_for_log}): {str(e)}"})
    except Exception as e:
        yield json.dumps({"type": "error", "message": f"An unexpected error in subscribe_to_logs for ({filter_description_for_log}): {str(e)}"})

if __name__ == "__main__":
    print(f"Solana Real-Time Event Monitoring MCP Server.")
    mcp.run()