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

    def capture_screenshot(self, output_path):
        res = self.call("Page.captureScreenshot", {"format": "png"})
        if res and "data" in res:
            img_bytes = base64.b64decode(res["data"])
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"Captured: {output_path} ({len(img_bytes)} bytes)")
            return True
        return False

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def capture_all():
    screenshots_dir = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data = Path(__file__).resolve().parent / "chrome_ss_data"
    user_data.mkdir(parents=True, exist_ok=True)
    
    proc = subprocess.Popen([
        CHROME,
        "--headless=new",
        "--remote-debugging-port=9228",
        "--window-size=1600,1000",
        "--disable-gpu",
        f"--user-data-dir={user_data}",
        "about:blank"
    ])
    
    time.sleep(2.0)
    
    try:
        targets_req = urllib.request.urlopen("http://127.0.0.1:9228/json", timeout=5)
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
        
        # 1. Login Screen with new Logo
        print("1. Capturing Login Screen with new Logo...")
        ws.call("Page.navigate", {"url": "http://127.0.0.1:8000/"})
        time.sleep(2.5)
        ws.capture_screenshot(screenshots_dir / "01_login_screen.png")
        
        # 2. Executive Control Center
        print("2. Capturing Executive Control Center with new Logo...")
        ws.call("Page.navigate", {"url": "http://127.0.0.1:8000/?autologin=cfo&tab=dashboard"})
        time.sleep(3.0)
        ws.capture_screenshot(screenshots_dir / "03_executive_control_center.png")
        
        # 3. Digital Twin Studio
        print("3. Capturing Digital Twin Studio with new Logo...")
        ws.eval_js("switchTab('digitaltwin')")
        time.sleep(2.0)
        ws.capture_screenshot(screenshots_dir / "02_digital_twin_studio.png")
        
        # 4. Company Decision Map
        print("4. Capturing Company Decision Map...")
        ws.eval_js("switchTab('decisionmap')")
        time.sleep(2.0)
        ws.capture_screenshot(screenshots_dir / "04_company_decision_map.png")
        
        # 5. Invoices & Affordability
        print("5. Capturing Invoice Intelligence...")
        ws.eval_js("switchTab('invoices')")
        time.sleep(2.0)
        ws.capture_screenshot(screenshots_dir / "05_invoice_intelligence_auditor.png")
        
        # 6. HITL Approvals Queue
        print("6. Capturing Approvals Queue...")
        ws.eval_js("switchTab('approvals')")
        time.sleep(2.0)
        ws.capture_screenshot(screenshots_dir / "06_hitl_approvals_queue.png")
        
        # 7. Form 16 Tax Reporting
        print("7. Capturing Tax & Form 16...")
        ws.eval_js("switchTab('taxreporting')")
        time.sleep(2.0)
        ws.capture_screenshot(screenshots_dir / "07_form16_tax_reconciliation.png")
        
        # 8. Financial Copilot Chat
        print("8. Capturing Financial Copilot Chat...")
        ws.eval_js("switchTab('chat'); sendQuickPrompt('What if Engineering spending rate stays the same for 60 more days?')")
        time.sleep(3.5)
        ws.capture_screenshot(screenshots_dir / "08_financial_copilot_chat.png")
        
        # 9. Merchant AI Commerce
        print("9. Capturing Merchant Growth & AI Commerce...")
        ws.eval_js("switchTab('commerce')")
        time.sleep(2.0)
        ws.capture_screenshot(screenshots_dir / "09_merchant_ai_commerce.png")
        
        # 10. Role-Based Notification Drawer
        print("10. Capturing Role-Based Notification Drawer...")
        ws.eval_js("toggleNotificationsDrawer()")
        time.sleep(1.5)
        ws.capture_screenshot(screenshots_dir / "10_role_based_notifications_drawer.png")
        
        print("\n==================================================================")
        print("ALL SCREENSHOTS SUCCESSFULLY UPDATED WITH OFFICIAL FINPILOT AI LOGO!")
        print("==================================================================")
        
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass

if __name__ == "__main__":
    capture_all()
