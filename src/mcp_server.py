from mcp.server.fastmcp import FastMCP
import time

# Initialize an MCP Server
mcp = FastMCP("OpsSwarm-Tools")

@mcp.tool()
def fetch_service_logs(service_name: str) -> str:
    """Fetches the last 50 lines of logs for a given service."""
    # Simulation of real infrastructure
    if service_name == "payment_gateway":
        return """
        [INFO] 14:00:01 Transaction started
        [INFO] 14:00:02 Processing payment
        [ERROR] 14:00:05 Connection Refused: DB_SHARD_04 unreachable
        [CRITICAL] 14:00:06 Transaction rolled back.
        """
    elif service_name == "auth_service":
        return "[INFO] Health Check: OK"
    else:
        return f"[ERROR] Service '{service_name}' not found."

@mcp.tool()
def check_db_status(shard_id: str) -> str:
    """Checks the health status of a database shard."""
    if shard_id == "DB_SHARD_04":
        return "STATUS: OFFLINE. CPU Load: 100%. Memory: 99%."
    return "STATUS: ONLINE. Load: Normal."

@mcp.tool()
def restart_resource(resource_id: str) -> str:
    """Restarts a specific resource (container/VM/DB)."""
    time.sleep(2) # Simulate work
    return f"SUCCESS: Resource {resource_id} has been restarted."

if __name__ == "__main__":
    # Runs the MCP server on stdio (standard input/output)
    mcp.run()