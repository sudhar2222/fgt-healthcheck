import json
import requests
import urllib3
import time
import subprocess
import pandas as pd

fmg_ip = input("Enter FortiManager IP address: ")
fmg_admin = input("Enter FortiManager admin username: ")
fmg_pass = input("Enter FortiManager admin password: ")
urllib3.disable_warnings()
API_ENDPOINT = f"https://{fmg_ip}/jsonrpc"

#generate session key

request = {
        "id": 1,
        "method": "exec",
        "params": [
            {
                "data": {
                    "passwd": fmg_admin,
                    "user": fmg_pass
                },
                "url": "/sys/login/user"
            }
        ]
    }
    
response = requests.post(url=API_ENDPOINT,data=json.dumps(request),verify=False )
parsed = json.loads(response.text)
session_id = parsed["session"]
#print(session_id)

def get_bgp_status():    

    fw_name = input("Enter the FortiGate device name : ")
    adom_name = input("Enter the ADOM name : ")
    script_run_request = {
        "method": "exec",
        "params": [
            {
                "data": {
                    "adom": [adom_name],
                    "scope": [
                        {
                            "name": fw_name,
                            "vdom": "root"
                        }
                    ],
                    "script": "bgp summary"
                },
                "url": f"/dvmdb/adom/{adom_name}/script/execute"
            }
        ],
        "session": session_id,
        "id": 1
    }
    
    script_run_response = requests.post(url=API_ENDPOINT, data=json.dumps(script_run_request), verify=False)
    time.sleep(7)
    
    script_output_request = {
        "method": "get",
        "params": [
            {
                "url": f"/dvmdb/adom/{adom_name}/script/log/latest/device/{fw_name}"
            }
        ],
        "session": session_id,
        "id": 1
    }
    
    script_output_response = requests.post(url=API_ENDPOINT, data=json.dumps(script_output_request), verify=False)
    parsed_output = json.loads(script_output_response.text)
    output = parsed_output["result"][0]["data"]["content"]

    return output

    

def ping(host):
    try:
        # For Linux/macOS
        output = subprocess.check_output(
            ["ping", "-c", "4", host],
            stderr=subprocess.STDOUT,       # Capture stderr too
            universal_newlines=True
        )
        return output

    except subprocess.CalledProcessError as e:
        print("Ping failed!")
        # e.output contains the error message from ping
        return e.output

def underlay_check():
    ip = input("Enter WAN gateway IP address: ")
    ping_response = ping(ip)
    return ping_response

def analyze_with_llm(bgp_output, underlay_output):
    """Send BGP output to Llama and get user-friendly analysis"""
    
    prompt = f"""SYSTEM:
You are a Network Engineer Assistant specializing in BGP and WAN diagnostics. You analyze raw CLI outputs and produce structured summaries.

USER:

Analyze the following outputs and summarize strictly as instructed.

INSTRUCTIONS:
1. From the BGP output:
   - Count and report the total number of BGP neighbors.
   - For each neighbor, mention its IP if the status is Established or DOWN  if the status is Idle, Active, or Connect.
   - Explicitly mention if any neighbor is UP or DOWN.

2. From the Ping output:
   - If ping replies are successful (e.g., `0% packet loss`, or lines containing `bytes from`, or `icmp_seq`), state:
      “Ping successful — WAN is healthy.”
   - If ping fails (e.g., `100% packet loss`, `Request timed out`, or `Destination Host Unreachable`), state:
      “Ping failed — WAN is down and not healthy.”

3. Output format must be exactly:

BGP Neighbors:

Total Neighbors: <number>

Neighbor <IP>: <state> (UP/DOWN)

Neighbor <IP>: <state> (UP/DOWN)

WAN Status:
<Ping result and WAN health>

INPUTS:
BGP Output:
{bgp_output}

PING Output:
{underlay_output}

"""

    # Call Ollama API
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3:latest",
            "prompt": prompt,
            "stream": False
        }
    )
    
    result = response.json()
    return result["response"]


if __name__ == "__main__":

    
    #  underlay check
    underlay_output = underlay_check()
    
    # THEN get BGP status
    bgp_output = get_bgp_status()

    # Analyze with LLM
    analysis = analyze_with_llm(bgp_output, underlay_output)
    
    print()
    print("=" * 70)
    print("LLM ANALYSIS")
    print("=" * 70)
    print()
    print(analysis)
    print()
    
    print("=" * 70)
    print("RAW BGP OUTPUT")
    print("=" * 70)
    print()
    print(bgp_output)
    print()
    print("=" * 70)


    print("RAW PING OUTPUT")
    print("=" * 70)
    print()
    print(underlay_output)
    print()
    print("=" * 70)

