Solana Real-Time Event Monitoring MCP
License: MIT | Python 3.9+ | Docker Support | Powered by FastMCP
The Story: Bringing Blockchain to Life

Jane was building an AI trading agent that needed to react instantly to on-chain events. Traditional polling solutions were too slow and unreliable. "If only there was a way to stream blockchain data directly to my agent," she thought. The next morning, she discovered Solana Real-Time Event Monitoring MCP. Within minutes, her agent was receiving live account updates, transaction confirmations, and program logs, allowing it to execute trades with unprecedented speed and precision. What used to take seconds or minutes now happened in milliseconds.

Overview
Solana Real-Time Event Monitoring MCP is a powerful WebSocket-based microservice that transforms Solana's real-time blockchain data into structured, consumable streams for AI applications, agents, and monitoring systems. It leverages the FastMCP framework to provide reliable, persistent connections to the Solana blockchain, delivering critical on-chain events directly to your applications as they happen.
This project serves as a bridge between Solana's WebSocket API and modern AI-driven applications, enabling real-time decision making, monitoring, and analysis based on blockchain activity. By wrapping Solana's WebSocket endpoints in a standardized MCP (Microservice Communication Protocol) format, developers can easily integrate live blockchain data into their systems without managing complex WebSocket connections or handling reconnection logic.
Features

Account Monitoring: Subscribe to changes for any Solana account and receive immediate notifications when data changes.
Transaction Tracking: Follow transaction signatures from submission to finalization across different commitment levels.
Program Logs: Stream logs from specific programs or the entire Solana network with customizable filters.
Real-time Data Streams: Receive data via asynchronous generators, perfect for AI agents that need to react to events.
Commitment Level Selection: Choose between processed, confirmed, and finalized commitment levels.
Flexible Data Encoding: Support for various encoding formats including base64, base58, and jsonParsed.
Error Handling: Robust error management with informative error messages.
Multi-client Support: Designed to handle multiple concurrent connections efficiently.

Installation
Prerequisites

Python 3.9 or higher
pip (Python package installer)

Option 1: Local Installation
bash# Clone the repository
git clone https://github.com/yourusername/solana-realtime-monitor-mcp.git
cd solana-realtime-monitor-mcp

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the server
python main.py
Option 2: Docker Installation
bash# Clone the repository
git clone https://github.com/yourusername/solana-realtime-monitor-mcp.git
cd solana-realtime-monitor-mcp

# Build the Docker image
docker build -t solana-realtime-monitor-mcp .

# Run the container
docker run -p 8081:8081 solana-realtime-monitor-mcp
Configuration
Configure the Solana connection to use mainnet:
python# Edit these variables in main.py
SOLANA_WS_URL = "wss://api.mainnet-beta.solana.com/"  # Official Solana mainnet RPC
MCP_HOST = "127.0.0.1"  # The host address to bind the MCP server
MCP_PORT = 8081         # The port to expose the MCP server
For production applications, we strongly recommend using a dedicated RPC provider:
python# Replace with your dedicated RPC provider URL
SOLANA_WS_URL = "wss://YOUR_PROVIDER_URL/..."  # Examples include:
# - QuickNode: "wss://YOUR_QUICKNODE_URL/..."
# - Alchemy: "wss://YOUR_ALCHEMY_URL/..."
# - Ankr: "wss://YOUR_ANKR_URL/..."
# - Triton: "wss://YOUR_TRITON_URL/..."
When using mainnet, consider these additional configuration best practices:

Connection Resilience: Implement automatic reconnection with exponential backoff
Error Handling: Add more robust error handling for production environments
Rate Limiting: Be aware of RPC provider rate limits and implement appropriate throttling
Load Balancing: For high-volume applications, consider implementing RPC endpoint rotation

Usage
Once the server is running, it exposes several tools that can be used to monitor Solana blockchain activity:
Available Tools

subscribe_to_account_updates: Stream real-time account data changes.
subscribe_to_signature_status: Monitor transaction status changes.
subscribe_to_logs: Stream program execution logs.

Example: Monitoring a Token Account with Python
pythonimport asyncio
import json
import httpx
from sse_client.async_client import EventSource

async def monitor_token_account(account_pubkey):
    # Initialize the streaming connection
    url = f"http://localhost:8081/tools/subscribe_to_account_updates"
    params = {
        "account_pubkey": account_pubkey,
        "commitment": "confirmed",
        "encoding": "jsonParsed"
    }
    
    async with httpx.AsyncClient() as client:
        # Create a streaming connection
        async with client.stream("POST", url, json=params, timeout=None) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        print(f"Update received: {json.dumps(data, indent=2)}")
                        
                        # Process the data (example)
                        if "params" in data and "result" in data["params"]:
                            account_data = data["params"]["result"]["value"]
                            print(f"Balance: {account_data.get('lamports', 0)}")
                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {line}")

# Example: Monitor the SOL token mint account
asyncio.run(monitor_token_account("So11111111111111111111111111111111111111112"))
Example: Using with LangChain
pythonfrom langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

# Load Solana monitoring tools
tools = load_tools(["solana-realtime-monitor-mcp"], base_url="http://localhost:8081")

# Initialize an agent with the tools
llm = OpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# Run the agent with a Solana-related query
response = agent.run("Monitor the USDC token account on Solana and alert me if the balance changes")
Example: Monitoring Program Logs
pythonimport asyncio
import json
import httpx

async def monitor_token_program_logs():
    # SPL Token Program ID
    token_program_id = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    
    url = f"http://localhost:8081/tools/subscribe_to_logs"
    params = {
        "filter_criteria": {"mentions": [token_program_id]},
        "commitment": "confirmed"
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=params, timeout=None) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        
                        # Check for token transfer logs
                        if "params" in data and "result" in data["params"]:
                            logs = data["params"]["result"]["value"]["logs"]
                            if any("Transfer" in log for log in logs):
                                print("Token transfer detected!")
                                print(f"Logs: {logs}")
                    except json.JSONDecodeError:
                        pass

# Monitor all SPL token transfers
asyncio.run(monitor_token_program_logs())
Architecture
Solana Real-Time Event Monitoring MCP is built using a modular architecture that abstracts the complexities of WebSocket connections:
Core Components

WebSocket Client: Manages persistent connections to Solana's WebSocket API with automatic reconnection.
FastMCP Server: Exposes the WebSocket streams as standardized tools via HTTP with Server-Sent Events.
Async Generators: Transforms WebSocket events into asynchronous generators for easy consumption.
Error Handling: Comprehensive error handling with informative error messages.

Data Flow
  Solana Node      WebSocket Client      FastMCP API        Client Apps   
  (WebSocket) <---> (Subscription) <---> (SSE Stream) <---> & AI Agents

The FastMCP server receives a tool request from a client app or AI agent.
It establishes a WebSocket connection to the specified Solana node.
The subscription is created and a WebSocket connection is maintained.
Real-time updates are streamed from Solana to the client via Server-Sent Events.
The connection persists until the client disconnects or an error occurs.

Tool Details
subscribe_to_account_updates
Monitors changes to a Solana account in real-time.
Parameters:

account_pubkey (string): The account public key to monitor (base58 encoded)
commitment (string, optional): Commitment level - "processed", "confirmed", or "finalized"
encoding (string, optional): Data encoding - "base64", "base58", "jsonParsed", or "base64+zstd"

Example Use Cases:

Track token account balance changes
Monitor NFT metadata updates
Detect smart contract state changes

subscribe_to_signature_status
Tracks a transaction from submission to confirmation.
Parameters:

signature (string): The transaction signature to monitor (base58 encoded)
commitment (string, optional): Commitment level - "processed", "confirmed", or "finalized"

Example Use Cases:

Verify payment completion
Monitor transaction finality
Trigger actions after transaction confirmation

subscribe_to_logs
Streams program execution logs in real-time.
Parameters:

filter_criteria (object): Either {"all": true} or {"mentions": ["Program1", "Program2"]}
commitment (string, optional): Commitment level - "processed", "confirmed", or "finalized"

Example Use Cases:

Monitor smart contract events
Debug program executions
Track cross-program interactions

Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

FastMCP Framework for providing the MCP server implementation
Solana Labs for their WebSocket API documentation
