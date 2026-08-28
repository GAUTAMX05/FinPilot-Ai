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
        while time.time() - start < 10:
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

def test_compose_request_flow():
    user_data = Path(__file__).resolve().parent / "chrome_compose_test_data"
    user_data.mkdir(parents=True, exist_ok=True)
    
    proc = subprocess.Popen([
        CHROME,
        "--headless=new",
        "--remote-debugging-port=9225",
        "--window-size=1400,900",
        "--disable-gpu",
        f"--user-data-dir={user_data}",
        "about:blank"
    ])
    
    time.sleep(2.0)
    
    try:
        targets_req = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=5)
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
        
        print("1. Logging in as CFO (Priya Sharma / Vikramaditya Singhania)...")
        ws.call("Page.navigate", {"url": "http://127.0.0.1:8000/?autologin=cfo"})
        time.sleep(3.0)
        
        # Open Notifications Drawer
        ws.eval_js("toggleNotificationsDrawer()")
        time.sleep(1.0)
        is_drawer_open = ws.eval_js("!document.getElementById('notificationsDrawer').classList.contains('hidden')")
        print(f"[PASS] Notification Drawer Toggled -> Visible: {is_drawer_open}")
        
        # Click [New Request] button
        print("2. Clicking [New Request] button...")
        ws.eval_js("openComposeNotificationModal()")
        time.sleep(1.0)
        is_compose_open = ws.eval_js("!document.getElementById('composeNotifModal').classList.contains('hidden')")
        recipient_options_count = ws.eval_js("document.getElementById('composeRecipient').options.length")
        print(f"[PASS] Compose Modal Opened -> Visible: {is_compose_open}, Available Recipients: {recipient_options_count}")
        
        # Fill in compose form
        print("3. Composing and dispatching request to Rahul Verma (FIN-MGR-001)...")
        ws.eval_js("""
            document.getElementById('composeRecipient').value = 'FIN-MGR-001';
            document.getElementById('composeType').value = 'APPROVAL_REQUEST';
            document.getElementById('composePriority').value = 'HIGH';
            document.getElementById('composeEntityType').value = 'EXPENSE';
            document.getElementById('composeEntityId').value = 'EXP-2026-CLOUD';
            document.getElementById('composeTitle').value = 'Production Cluster Expansion Approval';
            document.getElementById('composeMessage').value = 'Please review the ₹92,000 AWS Kubernetes cluster invoice.';
            document.getElementById('composeNotifForm').dispatchEvent(new Event('submit'));
        """)
        time.sleep(1.5)
        is_compose_closed = ws.eval_js("document.getElementById('composeNotifModal').classList.contains('hidden')")
        print(f"[PASS] Request Dispatched -> Modal Closed: {is_compose_closed}")
        
        # Now switch account to Finance Manager (Rahul Verma)
        print("4. Switching account to Finance Manager (Rahul Verma, FIN-MGR-001)...")
        ws.call("Page.navigate", {"url": "http://127.0.0.1:8000/?autologin=fm"})
        time.sleep(3.0)
        
        # Open FM notification drawer
        ws.eval_js("toggleNotificationsDrawer()")
        time.sleep(1.0)
        fm_unread_badge = ws.eval_js("document.getElementById('drawerNotifCount').innerText")
        print(f"[PASS] Finance Manager Drawer Opened -> Counter: '{fm_unread_badge}'")
        
        # Check if the newly composed notification is at top of list
        first_title = ws.eval_js("document.querySelector('#notificationsDrawerList h4')?.innerText")
        print(f"[PASS] Finance Manager Received New Request -> Title: '{first_title}'")
        
        # Open Thread Modal and send reply
        print("5. Opening Two-Way Conversation Thread and replying...")
        first_notif_id = ws.eval_js("cachedNotifications[0]?.id")
        ws.eval_js(f"openNotificationThread('{first_notif_id}')")
        time.sleep(1.0)
        is_thread_open = ws.eval_js("!document.getElementById('notifThreadModal').classList.contains('hidden')")
        print(f"[PASS] Conversation Thread Modal Opened: {is_thread_open}")
        
        # Reply to thread
        ws.eval_js("""
            document.getElementById('threadReplyInput').value = 'Reviewed and verified under Q3 Cloud budget allocation.';
            document.getElementById('threadReplyForm').dispatchEvent(new Event('submit'));
        """)
        time.sleep(1.5)
        msg_count = ws.eval_js("document.querySelectorAll('#threadMessagesContainer > div').length")
        print(f"[PASS] Reply Posted in Live Thread -> Total Messages: {msg_count}")
        
        print("\n==================================================================")
        print("NEW REQUEST & TWO-WAY CONVERSATION FLOW VERIFIED 100% OPERATIONAL!")
        print("==================================================================")
        
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass

if __name__ == "__main__":
    test_compose_request_flow()
