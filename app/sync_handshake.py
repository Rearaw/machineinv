# sync_handshake.py
# sync_handshake.py
import time
import threading
import requests
import json
from flask import jsonify
import uuid

class SyncHandshake:
    def __init__(self):
        self.connection_status = {"status": "disconnected", "server_ip": "", "peer_ip": ""}
        self.peer_data = {}  # Store data received from peer
        self.local_data = {}  # Store local data to share
        self.session_id = str(uuid.uuid4())[:8]  # Unique session ID
    
    def update_connection(self, server_ip):
        """Update connection status and initiate connection process"""
        self.connection_status["server_ip"] = server_ip
        self.connection_status["peer_ip"] = server_ip
        self.connection_status["status"] = "connecting"
        
        # Start connection process in background
        def connect_to_peer():
            try:
                # First, verify the peer is reachable
                response = requests.get(f"http://{server_ip}/get_status", timeout=5)
                if response.status_code == 200:
                    # Peer is reachable, now send our connection request
                    connection_data = {
                        "peer_ip": self.get_my_ip(),
                        "session_id": self.session_id,
                        "action": "connect"
                    }
                    
                    response = requests.post(
                        f"http://{server_ip}/peer_connect", 
                        json=connection_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        self.connection_status["status"] = "connected"
                        # Automatically exchange data after connection
                        self.exchange_data_with_peer()
                    else:
                        self.connection_status["status"] = "failed"
                else:
                    self.connection_status["status"] = "failed"
                    
            except requests.exceptions.RequestException as e:
                print(f"Connection failed: {e}")
                self.connection_status["status"] = "failed"
        
        threading.Thread(target=connect_to_peer).start()
        
        return {"status": "processing", "message": "Connecting to peer..."}
    
    def handle_incoming_connection(self, peer_data):
        """Handle connection request from another device"""
        try:
            self.connection_status["peer_ip"] = peer_data.get("peer_ip")
            self.connection_status["status"] = "connected"
            
            # Store peer session info
            self.session_id = peer_data.get("session_id", self.session_id)
            
            # Exchange data with the peer
            self.exchange_data_with_peer()
            
            return {"status": "success", "message": "Connection established"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def exchange_data_with_peer(self):
        """Exchange JSON data with connected peer"""
        def exchange():
            try:
                # Prepare local data to share
                self.prepare_local_data()
                
                # Send our data to peer
                peer_ip = self.connection_status["peer_ip"]
                response = requests.post(
                    f"http://{peer_ip}/receive_data",
                    json={
                        "sender_ip": self.get_my_ip(),
                        "session_id": self.session_id,
                        "data": self.local_data
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("Data sent successfully to peer")
                else:
                    print("Failed to send data to peer")
                    
            except Exception as e:
                print(f"Data exchange failed: {e}")
        
        threading.Thread(target=exchange).start()
    
    def receive_data_from_peer(self, data_package):
        """Receive and store data from peer"""
        try:
            self.peer_data = data_package.get("data", {})
            self.peer_data["received_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.peer_data["sender_ip"] = data_package.get("sender_ip", "unknown")
            return {"status": "success", "message": "Data received"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def prepare_local_data(self):
        """Prepare local data to share with peer"""
        # This is where you prepare your device's data
        # You can customize this based on what you want to share
        self.local_data = {
            "device_id": self.get_my_ip(),
            "device_name": f"Device-{self.session_id}",
            "connected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "online",
            "sample_data": {
                "message": f"Hello from {self.get_my_ip()}!",
                "random_number": int(time.time()) % 1000,
                "services_count": 5,  # Example data
                "users_count": 3      # Example data
            }
        }
    
    def get_my_ip(self):
        """Get the current device's IP address"""
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"{local_ip}:5000"
        except:
            return "unknown:5000"
    
    def get_status(self):
        """Get current connection status"""
        return {
            **self.connection_status,
            "session_id": self.session_id,
            "peer_data": self.peer_data,
            "local_data": self.local_data
        }
    
    def reset_connection(self):
        """Reset connection to initial state"""
        self.connection_status = {"status": "disconnected", "server_ip": "", "peer_ip": ""}
        self.peer_data = {}
        self.session_id = str(uuid.uuid4())[:8]
        return {"status": "reset"}

# Create a singleton instance
sync_handler = SyncHandshake()