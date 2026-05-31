from prometheus_client import Counter, Gauge, Histogram

# Base namespace for our application metrics
NAMESPACE = "virtual_trader"

# HTTP Metrics
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    ["method", "endpoint", "status"],
    namespace=NAMESPACE,
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0, float("inf"))
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status"],
    namespace=NAMESPACE
)

WS_CONNECTIONS_ACTIVE = Gauge(
    "ws_connections_active",
    "Number of active websocket connections",
    ["endpoint"],
    namespace=NAMESPACE
)

# MCP Data Crawler Metrics
MCP_TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Duration of MCP tool calls in seconds",
    ["tool_name", "status"],
    namespace=NAMESPACE,
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0, float("inf"))
)

MCP_TOOL_CALLS_TOTAL = Counter(
    "mcp_tool_calls_total",
    "Total count of MCP tool calls",
    ["tool_name", "status"],
    namespace=NAMESPACE
)

MCP_CRAWLED_BYTES = Counter(
    "mcp_crawled_bytes_total",
    "Total size of data crawled in bytes",
    ["tool_name"],
    namespace=NAMESPACE
)

MCP_CRAWLED_ITEMS = Counter(
    "mcp_crawled_items_total",
    "Total number of items crawled",
    ["tool_name"],
    namespace=NAMESPACE
)

# Swarm Engine Metrics
SWARM_AGENT_AWAKENINGS = Counter(
    "swarm_agent_awakenings_total",
    "Total count of subagent awakenings/actions",
    ["agent_name", "model"],
    namespace=NAMESPACE
)

SWARM_TOKEN_USAGE = Counter(
    "swarm_token_usage_total",
    "Total number of tokens consumed by Swarm Agents",
    ["agent_name", "model", "token_type"],  # token_type: prompt, completion, total
    namespace=NAMESPACE
)

SWARM_CACHE_LOOKUPS = Counter(
    "swarm_cache_lookups_total",
    "Total count of Swarm prediction cache lookups",
    ["status"],  # status: hit, miss
    namespace=NAMESPACE
)

SWARM_DEBATE_DURATION = Histogram(
    "swarm_debate_duration_seconds",
    "Duration of Swarm debate sessions in seconds",
    ["status"],  # status: success, error
    namespace=NAMESPACE,
    buckets=(1.0, 2.5, 5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 90.0, 120.0, float("inf"))
)
