from typing import Any, Dict, List
import asyncio
import websockets
import json
import logging
from collections import defaultdict, deque
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Configure logging (should be done early)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("solana-mcp")

# Initialize Solana MCP server
mcp = FastMCP("solana-mcp", host="127.0.0.1", port=8081)

# Constants and shared state
SOLANA_WS_URL = "wss://api.mainnet-beta.solana.com/"
MAX_EVENTS = 10
MAX_SUBSCRIPTIONS = 5
active_subscriptions = {}
subscription_ids = {}
event_storage = defaultdict(lambda: deque(maxlen=MAX_EVENTS))
subscription_lock = asyncio.Lock()

async def ws_listener(key: str, method: str, params: List[Any]):
    """Subscribe to a Solana websocket feed and store incoming events."""
    logger.info(f"Attempting to start subscription for {key} using method {method}")
    try:
        async with websockets.connect(SOLANA_WS_URL) as websocket:
            # Send subscription request
            subscription_request = {
                "jsonrpc": "2.0", "id": 1, "method": method, "params": params
            }
            await websocket.send(json.dumps(subscription_request))
            
            try:
                response_raw = await websocket.recv()
                response = json.loads(response_raw)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response for {key} subscription. Raw: {response_raw}")
                event_storage[key].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "data": {"error": "Failed to decode JSON response from websocket"}
                })
                return
            except Exception as e:
                logger.error(f"Error receiving initial response for {key}: {str(e)}")
                event_storage[key].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "data": {"error": f"Error receiving initial response: {str(e)}"}
                })
                return

            if "error" in response:
                error_details = response.get("error", "Unknown subscription error")
                logger.error(f"Subscription error for {key}: {error_details}")
                event_storage[key].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "data": {"error": str(error_details)} # Ensure error data is consistently structured
                })
                return
            
            sub_id = response.get("result")
            async with subscription_lock:
                subscription_ids[key] = sub_id
            
            logger.info(f"Subscription established for {key} with ID {sub_id}")
            event_storage[key].append({
                "timestamp": datetime.now().isoformat(),
                "type": "subscribed",
                "data": {"subscription_id": sub_id}
            })
            
            while True:
                try:
                    msg_raw = await websocket.recv()
                    msg = json.loads(msg_raw)
                    
                    if "method" in msg and msg["method"] == "subscription":
                        event_data = msg.get("params", {}).get("result", {})
                        logger.debug(f"Received event for {key}: {event_data}")
                        event_storage[key].append({
                            "timestamp": datetime.now().isoformat(),
                            "type": "update",
                            "data": event_data
                        })
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON message for {key}. Raw: {msg_raw}")
                    # Optionally store this error or break, depending on desired behavior
                except Exception as e:
                    logger.error(f"Error processing websocket message for {key}: {str(e)}")
                    event_storage[key].append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "error",
                        "data": {"error": f"Websocket processing error: {str(e)}"}
                    })
                    # Decide if to break or continue listening after an error
                    
    except asyncio.CancelledError:
        logger.info(f"Subscription for {key} was cancelled.")
        if key in subscription_ids:
            current_sub_id = subscription_ids.get(key) # Get ID before attempting to pop
            try:
                async with websockets.connect(SOLANA_WS_URL) as ws:
                    unsubscribe_method = method.replace("Subscribe", "Unsubscribe")
                    await ws.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": unsubscribe_method,
                        "params": [current_sub_id] # Use the stored ID
                    }))
                    logger.info(f"Successfully sent unsubscribe request for {key} with ID {current_sub_id}")
            except Exception as e:
                logger.error(f"Error unsubscribing {key} (ID: {current_sub_id}): {str(e)}")
    except Exception as e:
        logger.error(f"Unhandled websocket error for {key}: {str(e)}")
        event_storage[key].append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "data": {"error": f"Unhandled websocket error: {str(e)}"}
        })

async def validate_and_subscribe(key: str, method: str, params: List[Any]) -> List[Dict[str, Any]]:
    """Start subscription if not already active and return current events."""
    async with subscription_lock:
        if key not in active_subscriptions and len(active_subscriptions) >= MAX_SUBSCRIPTIONS:
            # Sort by the timestamp of the first event (subscription time) if available,
            # otherwise, fall back to the first key encountered.
            # This requires event_storage to have at least one 'subscribed' event.
            # A simpler FIFO based on insertion order into active_subscriptions:
            oldest_key = next(iter(active_subscriptions)) # Relies on dicts preserving insertion order (Python 3.7+)
            
            logger.info(f"Max subscriptions ({MAX_SUBSCRIPTIONS}) reached. Attempting to unsubscribe from oldest: {oldest_key}")
            # await unsubscribe(oldest_key) # Be careful with calling unsubscribe directly here due to lock
            # Safer to just cancel and let the ws_listener handle the actual unsubscribe RPC
            task_to_cancel = active_subscriptions.pop(oldest_key, None)
            subscription_ids.pop(oldest_key, None) # also clear its ID
            if task_to_cancel:
                task_to_cancel.cancel()
                logger.info(f"Cancelled oldest subscription task for {oldest_key} to make space.")
            else:
                logger.warning(f"Tried to remove oldest key {oldest_key} but it was not found in active_subscriptions.")

        if key not in active_subscriptions:
            logger.info(f"Creating new subscription task for {key}")
            active_subscriptions[key] = asyncio.create_task(ws_listener(key, method, params))
        
    return list(event_storage[key])

@mcp.tool(
    description="Subscribe to and retrieve updates for a Solana account."
)
async def getAccountUpdates(address: str) -> List[Dict[str, Any]]:
    """Subscribe to updates for a Solana account address."""
    # It's highly recommended to add back base58 validation for the address
    # try:
    #     base58.b58decode(address)
    # except Exception:
    #     logger.error(f"Invalid Solana address format: {address}")
    #     return [{"timestamp": datetime.now().isoformat(), 
    #              "type": "error", 
    #              "data": {"error": "Invalid Solana address format"}}]
    try:
        params = [address, {"encoding": "base64", "commitment": "finalized"}]
        # Consider re-adding format_account_response if you had it
        events = await validate_and_subscribe(address, "accountSubscribe", params)
        # return format_account_response(events) 
        return events
    except Exception as e:
        logger.error(f"Error in getAccountUpdates for {address}: {str(e)}")
        return [{"timestamp": datetime.now().isoformat(), 
                 "type": "error", 
                 "data": {"error": str(e)}}]

@mcp.tool(
    description="Subscribe to status updates of a Solana transaction."
)
async def getTransactionStatus(signature: str) -> List[Dict[str, Any]]:
    """Subscribe to status updates for a transaction signature."""
    # Add back signature validation (length, base58)
    try:
        params = [signature, {"commitment": "finalized"}]
        return await validate_and_subscribe(signature, "signatureSubscribe", params)
    except Exception as e:
        logger.error(f"Error in getTransactionStatus for {signature}: {str(e)}")
        return [{"timestamp": datetime.now().isoformat(), 
                 "type": "error", 
                 "data": {"error": str(e)}}]

@mcp.tool(
    description="Subscribe to program account updates."
)
async def getProgramUpdates(programId: str) -> List[Dict[str, Any]]:
    """Subscribe to updates for accounts owned by a program."""
    # Add back programId validation (base58)
    try:
        key = f"program_{programId}"
        params = [programId, {"encoding": "base64", "commitment": "finalized"}]
        return await validate_and_subscribe(key, "programSubscribe", params)
    except Exception as e:
        logger.error(f"Error in getProgramUpdates for {programId}: {str(e)}")
        return [{"timestamp": datetime.now().isoformat(), 
                 "type": "error", 
                 "data": {"error": str(e)}}]

@mcp.tool(
    description="Unsubscribe from updates for a specific key."
)
async def unsubscribe(key: str) -> Dict[str, Any]:
    """Unsubscribe from updates for a specific key."""
    async with subscription_lock:
        task = active_subscriptions.pop(key, None)
        sub_id = subscription_ids.pop(key, None) # Retrieve associated subscription ID
        
        if task:
            task.cancel()
            try:
                await task # Allow cleanup within ws_listener
            except asyncio.CancelledError:
                logger.info(f"Task for {key} (ID: {sub_id}) successfully cancelled during unsubscribe.")
            except Exception as e:
                logger.error(f"Error during task cleanup for {key} (ID: {sub_id}): {str(e)}")
            
            logger.info(f"Unsubscribe process initiated for {key} (original sub_id: {sub_id})")
            # The actual websocket unsubscribe happens in ws_listener's CancelledError block
            return {"status": "success", "message": f"Unsubscription process initiated for {key}", "subscription_id": sub_id}
        
        logger.warning(f"No active subscription found for key {key} during unsubscribe call.")
        return {"status": "error", "message": f"No active subscription found for {key}"}

@mcp.tool(
    description="List all active subscriptions."
)
async def listSubscriptions() -> Dict[str, Any]:
    """List all currently active subscriptions with details."""
    async with subscription_lock:
        subs_details = []
        for key, task in active_subscriptions.items():
            detail = {
                "key": key,
                "subscription_id": subscription_ids.get(key),
                "event_count": len(event_storage.get(key, [])),
                "task_status": "running" if not task.done() else "done" 
            }
            # You can add more sophisticated type detection here if needed
            # e.g., based on key prefix or pattern, similar to your original version
            if key.startswith("program_"):
                detail["type"] = "program"
                detail["program_id"] = key.split("_", 1)[1] if "_" in key else key
            elif key.startswith("block_"): # If you re-add block updates
                detail["type"] = "block"
                detail["commitment"] = key.split("_", 1)[1] if "_" in key else key
            # Add more heuristics for transaction vs account if needed
            # For example, Solana addresses are typically 32-44 chars, signatures ~88
            elif len(key) > 60 and len(key) < 90: # Heuristic for signatures
                 detail["type"] = "transaction_signature"
            else: # Default to account
                 detail["type"] = "account"

            subs_details.append(detail)
            
        return {
            "active_count": len(active_subscriptions),
            "max_subscriptions": MAX_SUBSCRIPTIONS,
            "subscriptions": subs_details
        }

if __name__ == "__main__":
    # Ensure MCP server is started after logging is configured
    logger.info("Starting Solana MCP Server...")
    mcp.run(transport='sse')