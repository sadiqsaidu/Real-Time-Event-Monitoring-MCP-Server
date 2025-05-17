# ⚡ Solana Real-Time Event Monitoring MCP

**License**: MIT | **Python** 3.9+ | Powered by **FastMCP**

---

## 🌟 The Story: Bringing Blockchain to Life

Jane was building an AI trading agent that needed to react instantly to on-chain events. Traditional polling solutions were too slow and unreliable.

> "If only there was a way to stream blockchain data directly to my agent," she thought.

The next morning, she discovered **Solana Real-Time Event Monitoring MCP**. Within minutes, her agent was receiving live account updates, transaction confirmations, and program logs—executing trades with unprecedented speed and precision. What used to take seconds or minutes now happened in milliseconds.

---

## 🧠 Overview

**Solana Real-Time Event Monitoring MCP** is a WebSocket-powered microservice that transforms Solana’s real-time blockchain data into structured, AI-friendly streams. Built on the **FastMCP** framework, it bridges Solana’s WebSocket API with modern AI agents and monitoring systems.

No more juggling raw sockets or reconnection logic—just plug in and stream on-chain events in real-time.

---

## 🚀 Features

- 🔄 **Account Monitoring** – Get notified immediately on account changes.
- 🧾 **Transaction Tracking** – Follow transactions from submission to finalization.
- 📦 **Program Logs** – Filter and stream logs from any program or network-wide.
- 📡 **Real-Time Streams** – Seamless integration using async generators.
- 🛠️ **Commitment Levels** – Choose from processed, confirmed, or finalized.
- 🧬 **Flexible Encodings** – base64, base58, and jsonParsed support.
- ⚙️ **Robust Error Handling** – Informative and fail-safe.
- 🧍‍♂️ **Multi-client Support** – Scales effortlessly for concurrent connections.

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)

### Option: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/solana-realtime-monitor-mcp.git
cd solana-realtime-monitor-mcp

# Set up a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

---

## ⚙️ Configuration

Edit the connection variables in `main.py`:

```python
SOLANA_WS_URL = "wss://api.mainnet-beta.solana.com/"
MCP_HOST = "127.0.0.1"
MCP_PORT = 8081
```

### Use a Dedicated RPC Provider for Production

```python
SOLANA_WS_URL = "wss://YOUR_PROVIDER_URL/..."
# e.g.
# QuickNode: "wss://YOUR_QUICKNODE_URL/..."
# Alchemy:   "wss://YOUR_ALCHEMY_URL/..."
# Ankr:      "wss://YOUR_ANKR_URL/..."
# Triton:    "wss://YOUR_TRITON_URL/..."
```

💡 **Tips for Production**:
- 📶 Add reconnection logic with exponential backoff
- 🔐 Harden error handling
- 🚦 Monitor rate limits and throttle requests
- 🧭 Rotate endpoints for load balancing

---

## 🧪 Usage

Once the server is running at `http://localhost:8081`, it exposes real-time Solana monitoring tools:

### 🔧 Available Tools

- `subscribe_to_account_updates` – Monitor account changes
- `subscribe_to_signature_status` – Track transaction status
- `subscribe_to_logs` – Stream logs for specific programs

---

## 🧠 Example: LangChain Integration

```python
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

# Load Solana monitoring tools
tools = load_tools(["solana-realtime-monitor-mcp"], base_url="http://localhost:8081")

# Initialize an agent with the tools
llm = OpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# Run the agent with a Solana-related query
response = agent.run("Monitor the USDC token account on Solana and alert me if the balance changes")
```

---

## 🏗️ Architecture

**Core Components**:

- 🌐 WebSocket Client – Persistent Solana connections
- 🚀 FastMCP Server – Wraps streams via HTTP (SSE)
- 🔁 Async Generators – Streamline WebSocket events
- ❌ Error Handler – Rich, user-friendly messages

### 🔄 Data Flow:

```
Solana Node <---> WebSocket Client <---> FastMCP API <---> AI Agents
```

---

## 🧰 Tool Details

### `subscribe_to_account_updates`

Monitors real-time account changes.

**Parameters**:
- `account_pubkey` (string): Account address (base58)
- `commitment` (optional): processed | confirmed | finalized
- `encoding` (optional): base64 | base58 | jsonParsed | base64+zstd

🔍 **Use Cases**:
- Track token/NFT balance changes
- Detect smart contract state updates

---

### `subscribe_to_signature_status`

Tracks transaction status.

**Parameters**:
- `signature` (string): Transaction signature
- `commitment` (optional): processed | confirmed | finalized

🔍 **Use Cases**:
- Monitor payment status
- Trigger actions post-finalization

---

### `subscribe_to_logs`

Streams logs from programs.

**Parameters**:
- `filter_criteria`: `{"all": true}` or `{"mentions": ["Program1"]}`
- `commitment` (optional): processed | confirmed | finalized

🔍 **Use Cases**:
- Trace smart contract events
- Debug program logic

---

## 🤝 Contributing

Pull requests are welcome! Fork, improve, and PR.

---

## 📄 License

MIT – see the [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- 🧠 **FastMCP** 
- 🛠️ **Solana Labs** 