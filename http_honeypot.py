import socket
import threading
import ssl
import json
import time
import os
import random
import logging
from datetime import datetime
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import database and logging from main module
# In a real implementation, these would be properly imported
# For demonstration purposes, we'll redefine minimal versions
class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        
    def add_connection(self, data):
        print(f"[DB] New HTTP connection: {data}")
        
    def add_http_request(self, data):
        print(f"[DB] New HTTP request: {data}")
        
    def start_session(self, session_id, client_ip, protocol, username=None):
        print(f"[DB] Started session {session_id} for {client_ip} using {protocol}")
        
    def end_session(self, session_id):
        print(f"[DB] Ended session {session_id}")

class LogManager:
    def __init__(self):
        self.logger = logging.getLogger('HTTPHoneypot')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
    def log_connection(self, client_ip, port, protocol, success=False):
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'port': port,
            'protocol': protocol,
            'success': success
        }
        self.logger.info(f"Connection: {json.dumps(data)}")
        return data
        
    def log_http_request(self, client_ip, session_id, method, path, headers, response_code):
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'session_id': session_id,
            'method': method,
            'path': path,
            'headers': headers,
            'response_code': response_code
        }
        self.logger.info(f"HTTP Request: {json.dumps(data)}")
        return data

# Load configuration
def load_config(config_file='config.json'):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {
        "http": {
            "enabled": True,
            "http_port": 8080,
            "https_port": 8443,
            "interface": "0.0.0.0",
            "cert_file": "server.crt",
            "key_file": "server.key",
            "server_name": "Apache/2.4.41 (Ubuntu)",
            "templates_dir": "templates"
        }
    }

# HTTP Request Handler
class HoneypotHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop('config', {})
        self.db_manager = kwargs.pop('db_manager', None)
        self.log_manager = kwargs.pop('log_manager', None)
        self.session_id = str(uuid.uuid4())
        super().__init__(*args, **kwargs)
        
    def setup(self):
        super().setup()
        self.request.settimeout(30)  # Set timeout to prevent hanging connections
        
    def version_string(self):
        return self.config.get('server_name', 'Apache/2.4.41 (Ubuntu)')
        
    def log_request(self, code='-', size='-'):
        # Override to use our custom logging
        pass
        
    def get_client_ip(self):
        return self.client_address[0]
        
    def do_GET(self):
        self._handle_request('GET')
        
    def do_POST(self):
        self._handle_request('POST')
        
    def do_HEAD(self):
        self._handle_request('HEAD')
        
    def _handle_request(self, method):
        client_ip = self.get_client_ip()
        headers = {k: v for k, v in self.headers.items()}
        
        # Log the request
        if self.log_manager:
            log_data = self.log_manager.log_http_request(
                client_ip, 
                self.session_id,
                method,
                self.path,
                headers,
                200  # Default response code
            )
            
            if self.db_manager:
                self.db_manager.add_http_request(log_data)
                
        # Generate appropriate response based on path
        if self.path == '/' or self.path == '/index.html':
            self._serve_index_page()
        elif self.path == '/login' or self.path == '/login.php':
            self._serve_login_page()
        elif self.path.startswith('/admin'):
            self._serve_admin_page()
        elif self.path.endswith('.css') or self.path.endswith('.js'):
            self._serve_static_file()
        else:
            self._serve_not_found()
            
    def _serve_index_page(self):
        content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Corporate Intranet Portal</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                header { background-color: #003366; color: white; padding: 10px 20px; }
                nav { background-color: #f2f2f2; padding: 10px; }
                nav a { margin-right: 15px; text-decoration: none; color: #003366; }
                .content { padding: 20px; }
                footer { background-color: #f2f2f2; padding: 10px; text-align: center; font-size: 0.8em; }
            </style>
        </head>
        <body>
            <header>
                <h1>Corporate Intranet Portal</h1>
            </header>
            <nav>
                <a href="/">Home</a>
                <a href="/services">Services</a>
                <a href="/directory">Directory</a>
                <a href="/admin">Admin</a>
                <a href="/login">Login</a>
            </nav>
            <div class="content">
                <h2>Welcome to the Corporate Intranet</h2>
                <p>This portal provides access to corporate resources and services.</p>
                <p>Please <a href="/login">login</a> to access restricted content.</p>
                
                <h3>Recent Announcements</h3>
                <ul>
                    <li>System maintenance scheduled for Saturday, August 24th</li>
                    <li>New VPN access procedures now in effect</li>
                    <li>Q3 business review documents now available</li>
                </ul>
            </div>
            <footer>
                &copy; 2025 Corporation. All rights reserved. | Last updated: August 20, 2025
            </footer>
        </body>
        </html>
        """
        self._send_response(200, content)
        
    def _serve_login_page(self):
        content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Corporate Portal</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                header { background-color: #003366; color: white; padding: 10px 20px; }
                .login-container { max-width: 400px; margin: 50px auto; padding: 20px; border: 1px solid #ddd; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
                button { background-color: #003366; color: white; padding: 10px 15px; border: none; cursor: pointer; }
                .error { color: red; margin-bottom: 15px; }
            </style>
        </head>
        <body>
            <header>
                <h1>Corporate Portal Login</h1>
            </header>
            <div class="login-container">
                <form action="/login" method="post">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        """
        self._send_response(200, content)
        
    def _serve_admin_page(self):
        content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin - Access Denied</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                header { background-color: #990000; color: white; padding: 10px 20px; }
                .content { padding: 20px; }
            </style>
        </head>
        <body>
            <header>
                <h1>Access Denied</h1>
            </header>
            <div class="content">
                <h2>Authentication Required</h2>
                <p>You must be logged in with administrator privileges to access this section.</p>
                <p><a href="/login">Login</a> to continue.</p>
            </div>
        </body>
        </html>
        """
        self._send_response(403, content)
        
    def _serve_static_file(self):
        content = "/* Static file content would be served here */"
        self._send_response(200, content)
        
    def _serve_not_found(self):
        content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Not Found</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                header { background-color: #990000; color: white; padding: 10px 20px; }
                .content { padding: 20px; }
            </style>
        </head>
        <body>
            <header>
                <h1>404 - Page Not Found</h1>
            </header>
            <div class="content">
                <p>The page you requested could not be found on this server.</p>
                <p>Please check the URL or <a href="/">return to the homepage</a>.</p>
            </div>
        </body>
        </html>
        """
        self._send_response(404, content)
        
    def _send_response(self, status_code, content):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html' if content.startswith('<!DOCTYPE') else 'text/plain')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Server', self.version_string())
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

# HTTP Server factory
def create_http_server(host, port, config, db_manager, log_manager, use_ssl=False):
    """Create and return an HTTP or HTTPS server instance"""
    def handler(*args, **kwargs):
        return HoneypotHTTPRequestHandler(*args, config=config, db_manager=db_manager, log_manager=log_manager, **kwargs)
    
    server = HTTPServer((host, port), handler)
    
    if use_ssl:
        # Configure SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        cert_file = config.get('cert_file', 'server.crt')
        key_file = config.get('key_file', 'server.key')
        
        # Generate self-signed cert if not exists
        if not (os.path.exists(cert_file) and os.path.exists(key_file)):
            generate_self_signed_cert(cert_file, key_file)
            
        context.load_cert_chain(cert_file, key_file)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    
    return server

# Generate self-signed certificate
def generate_self_signed_cert(cert_file, key_file):
    """Generate a self-signed certificate for HTTPS"""
    from OpenSSL import crypto
    
    # Create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Organization"
    cert.get_subject().OU = "Organizational Unit"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Write cert and key to files
    with open(cert_file, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(key_file, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

# Main HTTP honeypot class
class HTTPHoneypot:
    def __init__(self, config=None, db_manager=None, log_manager=None):
        self.config = config or load_config()
        self.db_manager = db_manager or DatabaseManager("nexdis.db")
        self.log_manager = log_manager or LogManager()
        self.http_server = None
        self.https_server = None
        self.http_thread = None
        self.https_thread = None
        
    def start(self):
        """Start HTTP and HTTPS honeypot servers"""
        http_config = self.config.get('http', {})
        
        # Start HTTP server
        if http_config.get('enabled', True):
            http_port = http_config.get('http_port', 8080)
            interface = http_config.get('interface', '0.0.0.0')
            
            self.http_server = create_http_server(
                interface, 
                http_port, 
                http_config,
                self.db_manager,
                self.log_manager
            )
            
            self.http_thread = threading.Thread(
                target=self.http_server.serve_forever,
                daemon=True
            )
            self.http_thread.start()
            print(f"HTTP honeypot listening on {interface}:{http_port}")
            
        # Start HTTPS server
        if http_config.get('enabled', True):
            https_port = http_config.get('https_port', 8443)
            interface = http_config.get('interface', '0.0.0.0')
            
            self.https_server = create_http_server(
                interface, 
                https_port, 
                http_config,
                self.db_manager,
                self.log_manager,
                use_ssl=True
            )
            
            self.https_thread = threading.Thread(
                target=self.https_server.serve_forever,
                daemon=True
            )
            self.https_thread.start()
            print(f"HTTPS honeypot listening on {interface}:{https_port}")
            
    def stop(self):
        """Stop HTTP and HTTPS honeypot servers"""
        if self.http_server:
            self.http_server.shutdown()
            print("HTTP honeypot stopped")
            
        if self.https_server:
            self.https_server.shutdown()
            print("HTTPS honeypot stopped")

# Run as standalone
if __name__ == "__main__":
    honeypot = HTTPHoneypot()
    honeypot.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down HTTP honeypot...")
        honeypot.stop()
        print("Shutdown complete")