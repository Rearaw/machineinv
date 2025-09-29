# file_checksum_manager.py
import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileChecksumManager:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.abspath(os.path.dirname(__file__))
        self.snapshot_file = "checksums.json"

    def file_checksum(self, path, algorithm="md5", chunk_size=8192):
        """Calculate checksum for a single file"""
        try:
            h = hashlib.new(algorithm)
            with open(path, "rb") as f:
                while chunk := f.read(chunk_size):
                    h.update(chunk)
            return str(path), h.hexdigest()
        except Exception as e:
            print(f"Error calculating checksum for {path}: {e}")
            return str(path), "error"

    def list_files(self, base_dir=None):
        """List all files in directory recursively"""
        search_dir = Path(base_dir or self.base_dir)
        return [f for f in search_dir.rglob("*") if f.is_file()]

    def all_file_checks(self, base_dir=None):
        """Calculate checksums for all files using threading"""
        results = {}
        search_dir = Path(base_dir or self.base_dir)
        files = self.list_files(search_dir)

        print(f"Calculating checksums for {len(files)} files...")

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_file = {executor.submit(self.file_checksum, f): f for f in files}
            for future in as_completed(future_to_file):
                path, checksum = future.result()
                # Store relative path for better sharing between devices
                relative_path = str(Path(path).relative_to(search_dir))
                results[relative_path] = {
                    "checksum": checksum,
                    "size": Path(path).stat().st_size,
                    "modified": datetime.fromtimestamp(
                        Path(path).stat().st_mtime
                    ).isoformat(),
                }
        return results

    def save_snapshot(self, results, filename=None):
        """Save checksum snapshot to file"""
        snapshot_file = filename or self.snapshot_file
        snapshot = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "device_id": self.get_device_id(),
            "total_files": len(results),
            "checksums": results,
        }
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
        return snapshot

    def load_snapshot(self, filename=None):
        """Load checksum snapshot from file"""
        snapshot_file = filename or self.snapshot_file
        if not Path(snapshot_file).exists():
            return {}, None
        with open(snapshot_file, "r", encoding="utf-8") as f:
            snapshot = json.load(f)
        return snapshot.get("checksums", {}), snapshot.get("timestamp")

    def get_current_file_data(self):
        """Get current file checksum data for sharing"""
        checksums = self.all_file_checks()
        snapshot = self.save_snapshot(checksums)
        return snapshot

    def compare_snapshots(self, snapshot1, snapshot2):
        """Compare two snapshots and return differences"""
        results1 = snapshot1.get("checksums", {})
        results2 = snapshot2.get("checksums", {})

        differences = {"added": [], "removed": [], "modified": [], "unchanged": []}

        all_files = set(results1.keys()) | set(results2.keys())

        for file_path in sorted(all_files):
            file1 = results1.get(file_path)
            file2 = results2.get(file_path)

            if file1 and not file2:
                differences["removed"].append({"file": file_path, "info": file1})
            elif file2 and not file1:
                differences["added"].append({"file": file_path, "info": file2})
            elif file1 and file2:
                if file1["checksum"] != file2["checksum"]:
                    differences["modified"].append(
                        {"file": file_path, "old_info": file1, "new_info": file2}
                    )
                else:
                    differences["unchanged"].append(file_path)

        return differences

    def get_device_id(self):
        """Get a unique identifier for this device"""
        try:
            import socket

            hostname = socket.gethostname()
            return f"{hostname}-{hashlib.md5(hostname.encode()).hexdigest()[:8]}"
        except:
            return "unknown-device"
