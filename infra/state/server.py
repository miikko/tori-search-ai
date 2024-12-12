from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path
import base64

# Configure state storage directory
STATES_DIR = Path("states")
STATES_DIR.mkdir(exist_ok=True)

try:
    with open(".env", "r") as f:
        credentials = f.readlines()
        if len(credentials) < 2:
            raise ValueError("Missing credentials in .env file. Expected USERNAME and PASSWORD")
        USERNAME = credentials[0].split("=")[1].strip()
        PASSWORD = credentials[1].split("=")[1].strip()
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading credentials: {e}")
    exit(1)

class TerraformStateHandler(BaseHTTPRequestHandler):
    
    def authenticate(self) -> bool:
        """Verify basic auth credentials"""
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            return False
        try:
            auth_type, auth_string = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                return False
            credentials = base64.b64decode(auth_string).decode()
            username, password = credentials.split(":", 1)
            return username == USERNAME and password == PASSWORD
        except Exception:
            return False
    
    def require_auth(self):
        """Send authentication required response"""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Terraform State"')
        self.end_headers()
    
    def handle_request(self, handler):
        """Wrapper to enforce authentication before handling requests"""
        if not self.authenticate():
            self.require_auth()
            return
        handler()
    
    def get_state_path(self, state_name: str) -> Path:
        """Get the full path for a state file"""
        return STATES_DIR / f"{state_name}.tfstate"
    
    def parse_state_name(self) -> str:
        """Extract state name from path, ignoring query parameters"""
        path = self.path.split('?')[0].strip('/')
        if not path:
            return ""
        return path.split('/')[-1]
    
    def do_GET(self):
        """Handle GET requests for state retrieval"""
        self.handle_request(self._handle_get)
    
    def _handle_get(self):
        state_name = self.parse_state_name()
        state_path = self.get_state_path(state_name)
        if not state_path.exists():
            self.send_response(404)
            self.end_headers()
            return
        with open(state_path, "rb") as f:
            state_data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(state_data)
    
    def do_POST(self):
        """Handle POST requests for state updates"""
        self.handle_request(self._handle_post)
    
    def _handle_post(self):
        state_name = self.parse_state_name()
        state_path = self.get_state_path(state_name)
        lock_path = self.get_state_path(f"{state_name}.lock")
        if lock_path.exists():
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?')[1]
                query_params = dict(param.split('=') for param in query_string.split('&'))
            with open(lock_path, 'r') as f:
                lock_info = json.load(f)
            if 'ID' not in query_params or query_params['ID'] != lock_info['ID']:
                self.send_response(423)  # Locked
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(lock_info).encode())
                return
        content_length = int(self.headers.get("Content-Length", 0))
        state_data = self.rfile.read(content_length)
        with open(state_path, "wb") as f:
            f.write(state_data)
        self.send_response(200)
        self.end_headers()
    
    def do_LOCK(self):
        """Handle LOCK requests"""
        self.handle_request(self._handle_lock)
    
    def _handle_lock(self):
        state_name = self.parse_state_name()
        lock_path = self.get_state_path(f"{state_name}.lock")
        if lock_path.exists():
            with open(lock_path, "r") as f:
                lock_info = json.load(f)
            self.send_response(423)  # Locked status code
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(lock_info).encode())
            return
        content_length = int(self.headers.get("Content-Length", 0))
        lock_info = json.loads(self.rfile.read(content_length))
        with open(lock_path, "w") as f:
            json.dump(lock_info, f)
        self.send_response(200)
        self.end_headers()
    
    def do_UNLOCK(self):
        """Handle UNLOCK requests"""
        self.handle_request(self._handle_unlock)
    
    def _handle_unlock(self):
        state_name = self.parse_state_name()
        lock_path = self.get_state_path(f"{state_name}.lock")
        if lock_path.exists():
            lock_path.unlink()
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    port = 8000
    server = HTTPServer(("0.0.0.0", port), TerraformStateHandler)
    print(f"Starting Terraform state server on port {port}")
    server.serve_forever()
