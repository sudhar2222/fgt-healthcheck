import json
import requests
import urllib3
import time

urllib3.disable_warnings()

API_ENDPOINT = "https://192.168.0.115/jsonrpc"

def get_bgp_status(user="admin", passwd="admin", device="VF-1401-HQ-FGT-01", adom="adom62", vdom="root"):
    """
    Runs the 'bgp summary' script on a FortiGate device via JSON-RPC and returns the script output.

    Args:
        user (str): FortiGate username
        passwd (str): FortiGate password
        device (str): Device name
        adom (str): ADOM name
        vdom (str): VDOM name

    Returns:
        str: Output of the BGP summary script
    """
    # 1️⃣ Generate session key
    login_request = {
        "id": 1,
        "method": "exec",
        "params": [
            {
                "data": {"user": user, "passwd": passwd},
                "url": "/sys/login/user"
            }
        ]
    }

    response = requests.post(url=API_ENDPOINT, data=json.dumps(login_request), verify=False)
    parsed = response.json()
    session_id = parsed.get("session")
    if not session_id:
        raise Exception("Failed to generate session key")

    # 2️⃣ Run the script
    script_run_request = {
        "method": "exec",
        "params": [
            {
                "data": {
                    "adom": [adom],
                    "scope": [{"name": device, "vdom": vdom}],
                    "script": "bgp summary"
                },
                "url": f"/dvmdb/adom/{adom}/script/execute"
            }
        ],
        "session": session_id,
        "id": 1
    }

    requests.post(url=API_ENDPOINT, data=json.dumps(script_run_request), verify=False)

    # 3️⃣ Wait for the script to execute
    time.sleep(10)  # adjust if needed

    # 4️⃣ Get the script output
    script_output_request = {
        "method": "get",
        "params": [{"url": f"/dvmdb/adom/{adom}/script/log/latest/device/{device}"}],
        "session": session_id,
        "id": 1
    }

    output_response = requests.post(url=API_ENDPOINT, data=json.dumps(script_output_request), verify=False)
    parsed_output = output_response.json()

    try:
        content = parsed_output["result"][0]["data"]["content"].strip()
        return content
    except (KeyError, IndexError):
        return ""

# Example usage
if __name__ == "__main__":
    bgp_output = get_bgp_status()
    print("Script Output:\n", bgp_output)



def call_phi3(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi3",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    return response.json()["response"]

# --- Simple Tool Use Flow ---
user_query = "Check BGP status for router 192.168.0.115"

# Step 1: Ask LLM to decide what to do
prompt = f"""
You are a network assistant. If user asks for BGP info, say TOOL_CALL:get_bgp_status and include router IP.
Otherwise, respond normally.

User: {user_query}
"""
response = call_phi3(prompt)

print("LLM Response:", response)

# Step 2: Detect Tool Call
if "TOOL_CALL:get_bgp_status" in response:
    # Extract IP if present
    import re
    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', user_query)
    ip = match.group(1) if match else "192.168.0.1"

    # Run tool
    tool_result = get_bgp_status(ip)
    print("Tool Result:", tool_result)

    # Step 3: Send tool output back to LLM for final reply
    followup_prompt = f"""
    The tool get_bgp_status returned this data:
    {json.dumps(tool_result)}
    Give a final explanation to the user.
    """
    final_response = call_phi3(followup_prompt)
    print("Final Response:", final_response)
else:
    print("Final Response:", response)