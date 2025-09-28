
import time
import threading
from flask import jsonify

class SyncHandshake:
    def __init__(self):
        self.connection_status = {"status": "disconnected", "server_ip": ""}
    
    def update_connection(self, server_ip):
        """Update connection status and simulate connection process"""
        self.connection_status["server_ip"] = server_ip
        self.connection_status["status"] = "connecting"
        
        # Simulate connection process
        def simulate_connection():
            time.sleep(2)  # Simulate connection time
            self.connection_status["status"] = "connected"
        
        threading.Thread(target=simulate_connection).start()
        
        return {"status": "processing", "message": "Connection initiated"}
    
    def get_status(self):
        """Get current connection status"""
        return self.connection_status
    
    def reset_connection(self):
        """Reset connection to initial state"""
        self.connection_status["status"] = "disconnected"
        self.connection_status["server_ip"] = ""
        return {"status": "reset"}

# Create a singleton instance
sync_handler = SyncHandshake()