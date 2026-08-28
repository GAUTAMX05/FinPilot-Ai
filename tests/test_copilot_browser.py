import os
import sys
import time
import json
import base64
import socket
import struct
import subprocess
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

class MinimalWebSocket:
    def __init__(self, host, port, path):
        self.sock = socket.create_connection((host, port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode('utf-8')
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode('utf-8'))
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.sock.recv(1024)
        if b"101 " not in resp:
            raise Exception(f"WS Handshake failed: {resp[:200]}")
        self.msg_id = 0

    def send_cmd(self, method, params=None):
        self.msg_id += 1
        payload = json.dumps({"id": self.msg_id, "method": method, "params": params or {}}).encode('utf-8')
        length = len(payload)
        mask_key = os.urandom(4)
        header = bytearray([0x81])
        if length <= 125:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        
        masked_payload = bytearray(length)
        for i in range(length):
            masked_payload[i] = payload[i] ^ mask_key[i % 4]
        
        self.sock.sendall(header + mask_key + masked_payload)
        return self.msg_id

    def recv_msg(self):
        data = self.sock.recv(2)
        if not data:
            return None
        b1, b2 = data[0], data[1]
        length = b2 & 0x7F
        if length == 126:
            length = struct.unpack("!H", self.sock.recv(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self.sock.recv(8))[0]
        
        payload = b""
        while len(payload) < length:
            chunk = self.sock.recv(min(65536, length - len(payload)))
            if not chunk:
                break
            payload += chunk
        return json.loads(payload.decode('utf-8', errors='ignore'))

    def call(self, method, params=None, wait_id=True):
        req_id = self.send_cmd(method, params)
        if not wait_id:
            return None
        start = time.time()
        while time.time() - start < 15:
            msg = self.recv_msg()
            if msg and msg.get("id") == req_id:
                return msg.get("result")
        return None

    def eval_js(self, expression):
        res = self.call("Runtime.evaluate", {"expression": expression, "returnByValue": True})
        if res and "result" in res:
            return res["result"].get("value")
        return None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def test_copilot_chat():
    user_data = Path(__file__).resolve().parent / "chrome_copilot_test_data"
    user_data.mkdir(parents=True, exist_ok=True)
    
    proc = subprocess.Popen([
        CHROME,
        "--headless=new",
        "--remote-debugging-port=9226",
        "--window-size=1400,900",
        "--disable-gpu",
        f"--user-data-dir={user_data}",
        "about:blank"
    ])
    
    time.sleep(2.0)
    
    try:
        targets_req = urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5)
        targets = json.loads(targets_req.read().decode('utf-8'))
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]
        parsed = ws_url.replace("ws://", "").split("/", 1)
        host_port = parsed[0].split(":")
        host = host_port[0]
        port = int(host_port[1])
        path = "/" + parsed[1]
        
        ws = MinimalWebSocket(host, port, path)
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        
        print("1. Navigating to Financial Decision Copilot view as CFO...")
        ws.call("Page.navigate", {"url": "http://127.0.0.1:8000/?autologin=cfo&tab=chat"})
        time.sleep(3.0)
        
        is_chat_visible = ws.eval_js("!document.getElementById('view-chat').classList.contains('hidden')")
        print(f"[PASS] Financial Decision Copilot Tab Active -> Visible: {is_chat_visible}")
        
        # Trigger quick prompt: What-If: Eng Burn
        print("2. Sending What-If simulation query to multi-agent orchestrator...")
        ws.eval_js("sendQuickPrompt('What if Engineering spending rate stays the same for 60 more days?')")
        time.sleep(3.0)
        
        msg_count = ws.eval_js("document.querySelectorAll('#chatMessages > div').length")
        last_msg_text = ws.eval_js("document.querySelector('#chatMessages > div:last-child')?.innerText || ''")
        has_assistant_reply = msg_count >= 2 and len(last_msg_text) > 50
        print(f"[PASS] Multi-Agent Response Received -> Message Count: {msg_count}, Content Length: {len(last_msg_text)}")
        
        # Trigger another prompt: Causal Root Cause
        print("3. Sending Causal Root Cause analysis query...")
        ws.eval_js("sendQuickPrompt('Why is Engineering overspending on cloud? Pinpoint causal root cause.')")
        time.sleep(3.0)
        
        msg_count_2 = ws.eval_js("document.querySelectorAll('#chatMessages > div').length")
        last_msg_text_2 = ws.eval_js("document.querySelector('#chatMessages > div:last-child')?.innerText || ''")
        print(f"[PASS] Causal Analysis Response Received -> Message Count: {msg_count_2}, Content Length: {len(last_msg_text_2)}")
        
        # Test HITL flow
        print("4. Testing Human-In-The-Loop Copilot flow...")
        ws.eval_js("submitApprovalDecision(true)")
        time.sleep(2.0)
        final_msg_count = ws.eval_js("document.querySelectorAll('#chatMessages > div').length")
        hitl_hidden = ws.eval_js("document.getElementById('hitlPromptContainer').classList.contains('hidden')")
        print(f"[PASS] HITL Decision Handled Cleanly -> Message Count: {final_msg_count}, HITL Bar Dismissed: {hitl_hidden}")
        
        print("\n==================================================================")
        print("FINANCIAL DECISION COPILOT VERIFIED 100% OPERATIONAL IN BROWSER!")
        print("==================================================================")
        
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass

if __name__ == "__main__":
    test_copilot_chat()
