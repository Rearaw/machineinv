
import time
import threading
import requests
import json
from flask import jsonify
import uuid
from app.file_checksum_manager import FileChecksumManager

class SyncHandshake:
    def __init__(self):
        self.connection_status = {"status": "disconnected", "server_ip": "", "peer_ip": ""}
        self.peer_data = {}  # Store data received from peer
        self.local_data = {}  # Store local data to share
        self.session_id = str(uuid.uuid4())[:8]
        self.file_manager = FileChecksumManager()  # File checksum manager
    
    def update_connection(self, serverIpAddresses):
        """Update connection status and initiate connection process"""
        peer_ip=serverIpAddresses.get("peer_server_ip")
        self.connection_status["server_ip"] = serverIpAddresses.get("server_ip")
        self.connection_status["peer_ip"] = peer_ip
        self.connection_status["status"] = "connecting"
        
        def connect_to_peer():
            try:
                # First, verify the peer is reachable
                response = requests.get(f"http://{peer_ip}/get_status", timeout=5)
                if response.status_code == 200:
                    # Peer is reachable, now send our connection request
                    connection_data = {
                        "server_ip": self.get_my_ip(),
                        "session_id": self.session_id,
                        "action": "connect"
                    }
                    
                    response = requests.post(
                        f"http://{peer_ip}/peer_connect", 
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
                # Prepare local data (including file checksums)
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
                    timeout=30  # Increased timeout for file data
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
            
            # Compare with local data if we have both
            if self.local_data and self.peer_data:
                self.compare_file_data()
                
            return {"status": "success", "message": "Data received"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def prepare_local_data(self):
        """Prepare local data including file checksums"""
        try:
            # Get file checksum data
            file_data = self.file_manager.get_current_file_data()
            
            # Prepare the complete local data package
            self.local_data = {
                "device_info": {
                    "device_id": self.file_manager.get_device_id(),
                    "ip_address": self.get_my_ip(),
                    "connected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "online"
                },
                "file_snapshot": file_data,
                "system_info": {
                    "total_files": file_data.get("total_files", 0),
                    "snapshot_time": file_data.get("timestamp"),
                    "session_id": self.session_id
                }
            }
            
        except Exception as e:
            print(f"Error preparing local data: {e}")
            # Fallback data if file scanning fails
            self.local_data = {
                "device_info": {
                    "device_id": self.file_manager.get_device_id(),
                    "ip_address": self.get_my_ip(),
                    "connected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "online"
                },
                "file_snapshot": {
                    "error": f"Failed to scan files: {str(e)}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_files": 0,
                    "checksums": {}
                },
                "system_info": {
                    "total_files": 0,
                    "snapshot_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id": self.session_id
                }
            }
    
    def compare_file_data(self):
        """Compare local and peer file data"""
        try:
            local_snapshot = self.local_data.get("file_snapshot", {})
            peer_snapshot = self.peer_data.get("file_snapshot", {})
            
            differences = self.file_manager.compare_snapshots(local_snapshot, peer_snapshot)
            
            # Store comparison results
            self.comparison_results = {
                "compared_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "differences": differences,
                "summary": {
                    "added": len(differences["added"]),
                    "removed": len(differences["removed"]),
                    "modified": len(differences["modified"]),
                    "unchanged": len(differences["unchanged"])
                }
            }
            
            print(f"File comparison completed: {self.comparison_results['summary']}")
            
        except Exception as e:
            print(f"Error comparing file data: {e}")
            self.comparison_results = {
                "error": str(e),
                "compared_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    # def get_my_ip(self):
    #     """Get the current device's IP address"""
    #     try:
            
    #         hostname = socket.gethostname()
    #         local_ip = socket.gethostbyname(hostname)
    #         return f"{local_ip}:5000"
    #     except:
    #         return "unknown:5000"




    def get_my_ip(self,fallback="127.0.0.1"):
        try:
            import socket
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM ) as s:
                s.connect(('8.8.8.8',80))
                return f"{s.getsockname()[0]}"
        except Exception:
            return fallback
    
    def get_status(self):
        """Get current connection status"""
        status_data = {
            **self.connection_status,
            "session_id": self.session_id,
            "peer_data": self.peer_data,
            "local_data": self.local_data
        }
        
        # Add comparison results if available
        if hasattr(self, 'comparison_results'):
            status_data["comparison_results"] = self.comparison_results
            
        return status_data
    
    def reset_connection(self):
        """Reset connection to initial state"""
        self.connection_status = {"status": "disconnected", "server_ip": "", "peer_ip": ""}
        self.peer_data = {}
        self.local_data = {}
        self.session_id = str(uuid.uuid4())[:8]
        if hasattr(self, 'comparison_results'):
            del self.comparison_results
        return {"status": "reset"}

# Create a singleton instance
sync_handler = SyncHandshake()