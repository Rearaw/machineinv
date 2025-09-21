import  os.path,re,sys,json,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor ,as_completed

BASE_DIR=os.path.abspath(os.path.dirname(__file__))
def file_checksum(  path,
                    algorithm="md5",
                    chunk_size=8192):
    h = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
        return str(path), h.hexdigest()

def list_files(base_dir):    
    return [f for f in base_dir.rglob("*") if f.is_file()]           
def all_file_checks():
    _BASE_DIR=Path(BASE_DIR)
    results={} 
    files=list_files(_BASE_DIR)
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_file={executor.submit(file_checksum,f): f for f in files}
        for future in as_completed(future_to_file):
            path,checksum = future.result()
            results[path] = checksum
    
    print(1)

if __name__ == "__main__":
    all_file_checks()
            

