import sys
import os
import time
import json
import base64
import socket
import hashlib
import struct
import subprocess
import urllib.request
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

OUT_DIR = Path(__file__).resolve().parent / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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
        # Masked client frame
        length = len(payload)
        mask_key = os.urandom(4)
        header = bytearray([0x81]) # FIN + text opcode
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
        # Read WebSocket frame
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

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def capture_all():
    print(f"Launching Browser: {CHROME}")
    user_data = Path(__file__).resolve().parent / "scratch" / "chrome_user_data"
    user_data.mkdir(parents=True, exist_ok=True)
    
    proc = subprocess.Popen([
        CHROME,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--window-size=1600,1050",
        "--hide-scrollbars",
        "--disable-gpu",
        f"--user-data-dir={user_data}",
        "about:blank"
    ])
    
    time.sleep(2.5)
    
    try:
        targets_req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
        targets = json.loads(targets_req.read().decode('utf-8'))
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]
        # Parse ws URL: ws://127.0.0.1:9222/devtools/page/...
        parsed = ws_url.replace("ws://", "").split("/", 1)
        host_port = parsed[0].split(":")
        host = host_port[0]
        port = int(host_port[1])
        path = "/" + parsed[1]
        
        ws = MinimalWebSocket(host, port, path)
        print("Connected to Browser DevTools via WebSocket!")
        
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        
        screenshots_to_take = [
            ("01_login_screen.png", "http://127.0.0.1:8000/", 1.5),
            ("02_digital_twin_studio.png", "http://127.0.0.1:8000/?autologin=cfo&tab=digitaltwin", 3.0),
            ("03_executive_control_center.png", "http://127.0.0.1:8000/?autologin=cfo&tab=dashboard", 2.5),
            ("04_company_decision_map.png", "http://127.0.0.1:8000/?autologin=cfo&tab=decisionmap", 2.0),
            ("05_invoice_intelligence_auditor.png", "http://127.0.0.1:8000/?autologin=cfo&tab=invoices", 2.0),
            ("06_hitl_approvals_queue.png", "http://127.0.0.1:8000/?autologin=cfo&tab=approvals", 2.0),
            ("07_form16_tax_reconciliation.png", "http://127.0.0.1:8000/?autologin=cfo&tab=tax", 2.0),
            ("08_financial_copilot_chat.png", "http://127.0.0.1:8000/?autologin=cfo&tab=copilot", 2.0),
            ("09_merchant_ai_commerce.png", "http://127.0.0.1:8000/?autologin=cfo&tab=commerce", 3.0),
        ]
        
        for filename, url, wait_sec in screenshots_to_take:
            print(f"\nNavigating to: {url} ...")
            ws.call("Page.navigate", {"url": url})
            time.sleep(wait_sec)
            
            print(f"Capturing: {filename} ...")
            res = ws.call("Page.captureScreenshot", {"format": "png", "quality": 95})
            if res and "data" in res:
                img_data = base64.b64decode(res["data"])
                out_path = OUT_DIR / filename
                with open(out_path, "wb") as f:
                    f.write(img_data)
                print(f"[OK SAVED] {out_path} ({len(img_data):,} bytes)")
            else:
                print(f"[FAILED] No screenshot data returned for {filename}")
                
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass

if __name__ == "__main__":
    capture_all()
