from flask import Flask, render_template, request, jsonify
import json
import requests
import urllib3
import time
from datetime import datetime

urllib3.disable_warnings()
API_ENDPOINT = "https://192.168.0.115/jsonrpc"

app = Flask(__name__)

# Store conversation history in memory (use database for production)
conversations = {}

def get_bgp_status():
    """Retrieves BGP status from FortiManager"""
    request_data = {
        "id": 1,
        "method": "exec",
        "params": [
            {
                "data": {
                    "passwd": "admin",
                    "user": "admin"
                },
                "url": "/sys/login/user"
            }
        ]
    }
    
    response = requests.post(url=API_ENDPOINT, data=json.dumps(request_data), verify=False)
    parsed = json.loads(response.text)
    session_id = parsed["session"]
    
    script_run_request = {
        "method": "exec",
        "params": [
            {
                "data": {
                    "adom": ["adom62"],
                    "scope": [
                        {
                            "name": "VF-1401-HQ-FGT-01",
                            "vdom": "root"
                        }
                    ],
                    "script": "bgp summary"
                },
                "url": "/dvmdb/adom/adom62/script/execute"
            }
        ],
        "session": session_id,
        "id": 1
    }
    
    script_run_response = requests.post(url=API_ENDPOINT, data=json.dumps(script_run_request), verify=False)
    time.sleep(10)
    
    script_output_request = {
        "method": "get",
        "params": [
            {
                "url": "/dvmdb/adom/adom62/script/log/latest/device/VF-1401-HQ-FGT-01"
            }
        ],
        "session": session_id,
        "id": 1
    }
    
    script_output_response = requests.post(url=API_ENDPOINT, data=json.dumps(script_output_request), verify=False)
    parsed_output = json.loads(script_output_response.text)
    output = parsed_output["result"][0]["data"]["content"]
    
    return output


# Tool definition
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_bgp_status",
            "description": "Retrieves the BGP routing summary from FortiManager for device VF-1401-HQ-FGT-01. Use this when user asks about BGP status, routing, or network connectivity.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

SYSTEM_INSTRUCTIONS = """You are a network monitoring assistant specialized in FortiGate devices.

Your responsibilities:
- Monitor and analyze BGP routing status
- Provide clear, concise summaries of network status
- Alert users to any issues or anomalies
- Use technical terminology accurately but explain it when needed

When analyzing BGP output:
- Highlight the number of BGP neighbors
- Identify neighbor states (Established, Idle, Active, etc.)
- Note any neighbors that are down
- Summarize routing table information

Keep responses professional but friendly. Always prioritize accuracy."""


def chat_with_llama(user_message, conversation_history):
    """Chat with Llama 3.2 with BGP tool integration"""
    
    # Add system prompt if this is the first message
    if len(conversation_history) == 0:
        conversation_history.append({
            "role": "system",
            "content": SYSTEM_INSTRUCTIONS
        })
    
    # Add user message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    try:
        # Call Ollama with tools
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2",
                "messages": conversation_history,
                "tools": tools,
                "stream": False
            },
            timeout=30
        )
        
        response_data = response.json()
        assistant_message = response_data["message"]
        
        # Add assistant response to history
        conversation_history.append(assistant_message)
        
        # Check if tool was called
        if assistant_message.get("tool_calls"):
            for tool_call in assistant_message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                
                if function_name == "get_bgp_status":
                    # Execute function
                    function_response = get_bgp_status()
                    
                    # Add tool response to conversation
                    conversation_history.append({
                        "role": "tool",
                        "content": function_response
                    })
                    
                    # Get final response with tool output
                    final_response = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "llama3.2",
                            "messages": conversation_history,
                            "stream": False
                        },
                        timeout=30
                    )
                    
                    final_message = final_response.json()["message"]
                    conversation_history.append(final_message)
                    
                    return final_message["content"], conversation_history
        
        return assistant_message.get("content", ""), conversation_history
        
    except Exception as e:
        return f"Error: {str(e)}", conversation_history


@app.route('/')
def index():
    """Render the chat interface"""
    return render_template('chat.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    # Get or create conversation history
    if session_id not in conversations:
        conversations[session_id] = []
    
    # Get response from LLM
    response, conversations[session_id] = chat_with_llama(
        user_message, 
        conversations[session_id]
    )
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })


@app.route('/reset', methods=['POST'])
def reset():
    """Reset conversation history"""
    data = request.json
    session_id = data.get('session_id', 'default')
    
    if session_id in conversations:
        conversations[session_id] = []
    
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Flask Chat Server")
    print("=" * 60)
    print("\n📊 Open your browser and go to: http://localhost:5000")
    print("\n⚡ Press CTRL+C to stop the server\n")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
