import socket
import threading
import os
import time
import json
import logging
from datetime import datetime
import uuid
from io import StringIO

# Import database and logging from main module
# In a real implementation, these would be properly imported
# For demonstration purposes, we'll redefine minimal versions
class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        
    def add_connection(self, data):
        print(f"[DB] New FTP connection: {data}")
        
    def add_ftp_command(self, data):
        print(f"[DB] FTP command: {data}")
        
    def start_session(self, session_id, client_ip, protocol, username=None):
        print(f"[DB] Started session {session_id} for {client_ip} using {protocol}")
        
    def end_session(self, session_id):
        print(f"[DB] Ended session {session_id}")

class LogManager:
    def __init__(self):
        self.logger = logging.getLogger('FTPHoneypot')
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
        
    def log_ftp_command(self, client_ip, session_id, command, args, response):
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'session_id': session_id,
            'command': command,
            'args': args,
            'response': response
        }
        self.logger.info(f"FTP Command: {json.dumps(data)}")
        return data

# Load configuration
def load_config(config_file='config.json'):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {
        "ftp": {
            "enabled": True,
            "port": 2121,
            "interface": "0.0.0.0",
            "banner": "220 FTP Server Ready",
            "username": "anonymous",
            "password": ""
        }
    }

# Virtual FTP File System
class FTPFileSystem:
    def __init__(self):
        # Virtual file system structure
        self.files = {
            '/': ['pub', 'incoming', 'private'],
            '/pub': ['readme.txt', 'software', 'documents'],
            '/pub/software': ['install.exe', 'patch.zip', 'update.tar.gz'],
            '/pub/documents': ['manual.pdf', 'changelog.txt'],
            '/incoming': [],
            '/private': ['users.txt', 'config.dat']
        }
        
        # File contents
        self.file_contents = {
            '/pub/readme.txt': "Welcome to our FTP server.\nThis server contains public software and documentation.\n",
            '/pub/documents/changelog.txt': "v2.1.3 - Bug fixes\nv2.1.2 - Added new features\nv2.1.1 - Performance improvements\n",
            '/private/users.txt': "admin:x:0:0:Administrator:/home/admin:/bin/bash\nuser1:x:1000:1000:User One:/home/user1:/bin/bash\nftp:x:14:50:FTP User:/var/ftp:/bin/false\n"
        }
        
    def list_dir(self, path):
        """List directory contents"""
        if path in self.files:
            return self.files[path]
        return []
        
    def get_file(self, path):
        """Get file contents"""
        if path in self.file_contents:
            return self.file_contents[path]
        return None
        
    def file_exists(self, path):
        """Check if file exists"""
        dir_path = os.path.dirname(path)
        filename = os.path.basename(path)
        
        if dir_path in self.files and filename in self.files[dir_path]:
            return True
        if path in self.file_contents:
            return True
        return False
        
    def is_dir(self, path):
        """Check if path is a directory"""
        return path in self.files
        
    def normalize_path(self, current, path):
        """Normalize path"""
        if path.startswith('/'):
            return path
        
        # Handle relative paths
        if not current.endswith('/'):
            current += '/'
            
        # Handle .. in path
        if path == '..':
            return os.path.dirname(current.rstrip('/'))
            
        return current + path

# FTP Session Handler
class FTPSession:
    def __init__(self, client_socket, client_address, config, db_manager, log_manager):
        self.socket = client_socket
        self.client_ip = client_address[0]
        self.client_port = client_address[1]
        self.config = config
        self.db_manager = db_manager
        self.log_manager = log_manager
        
        self.session_id = str(uuid.uuid4())
        self.authenticated = False
        self.username = None
        self.current_dir = '/'
        self.data_socket = None
        self.passive_server = None
        self.passive_port = None
        self.fs = FTPFileSystem()
        
        # Log connection
        connection_data = self.log_manager.log_connection(
            self.client_ip,
            self.client_port,
            'ftp',
            success=True
        )
        self.db_manager.add_connection(connection_data)
        
        # Start session
        self.db_manager.start_session(self.session_id, self.client_ip, 'ftp')
        
    def start(self):
        """Start the FTP session"""
        try:
            # Send welcome message
            self.send_response(self.config.get('banner', '220 FTP Server Ready'))
            
            # Main command loop
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break
                    
                request = data.decode('utf-8', errors='ignore').strip()
                if not request:
                    continue
                    
                # Extract command and arguments
                parts = request.split(' ', 1)
                command = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ''
                
                # Process command
                self.handle_command(command, args)
        except Exception as e:
            print(f"Error in FTP session: {str(e)}")
        finally:
            self.close()
            
    def close(self):
        """Close the FTP session"""
        try:
            self.socket.close()
        except:
            pass
            
        if self.data_socket:
            try:
                self.data_socket.close()
            except:
                pass
                
        if self.passive_server:
            try:
                self.passive_server.close()
            except:
                pass
                
        # End session
        self.db_manager.end_session(self.session_id)
        
    def send_response(self, message):
        """Send response to client"""
        if not message.endswith('\r\n'):
            message += '\r\n'
        self.socket.sendall(message.encode('utf-8'))
        
    def send_data(self, data):
        """Send data through the data connection"""
        if not self.data_socket:
            self.send_response('425 Use PORT or PASV first')
            return False
            
        try:
            self.data_socket.sendall(data)
            self.data_socket.close()
            self.data_socket = None
            return True
        except Exception as e:
            print(f"Error sending data: {str(e)}")
            self.send_response('426 Connection closed; transfer aborted')
            return False
            
    def handle_command(self, command, args):
        """Handle FTP command"""
        handlers = {
            'USER': self.handle_user,
            'PASS': self.handle_pass,
            'SYST': self.handle_syst,
            'FEAT': self.handle_feat,
            'PWD': self.handle_pwd,
            'CWD': self.handle_cwd,
            'CDUP': self.handle_cdup,
            'TYPE': self.handle_type,
            'PASV': self.handle_pasv,
            'PORT': self.handle_port,
            'LIST': self.handle_list,
            'NLST': self.handle_nlst,
            'RETR': self.handle_retr,
            'STOR': self.handle_stor,
            'DELE': self.handle_dele,
            'RMD': self.handle_rmd,
            'MKD': self.handle_mkd,
            'RNFR': self.handle_rnfr,
            'RNTO': self.handle_rnto,
            'QUIT': self.handle_quit
        }
        
        # Log command
        response = "500 Command not implemented"
        
        # Process command
        if command in handlers:
            response = handlers[command](args)
        else:
            self.send_response(response)
            
        # Log the command and response
        log_data = self.log_manager.log_ftp_command(
            self.client_ip,
            self.session_id,
            command,
            args,
            response
        )
        self.db_manager.add_ftp_command(log_data)
        
        return response
        
    def handle_user(self, username):
        """Handle USER command"""
        self.username = username
        self.authenticated = False
        response = '331 Please specify the password'
        self.send_response(response)
        return response
        
    def handle_pass(self, password):
        """Handle PASS command"""
        if not self.username:
            response = '503 Login with USER first'
        else:
            # For honeypot, we'll accept most credentials
            accepted_username = self.config.get('username', 'anonymous')
            accepted_password = self.config.get('password', '')
            
            if self.username == accepted_username and (not accepted_password or password == accepted_password):
                self.authenticated = True
                response = '230 Login successful'
            else:
                # For deception, randomly accept some invalid credentials
                if password and random.random() < 0.3:
                    self.authenticated = True
                    response = '230 Login successful'
                else:
                    response = '530 Login incorrect'
                    
        self.send_response(response)
        return response
        
    def handle_syst(self, args):
        """Handle SYST command"""
        response = '215 UNIX Type: L8'
        self.send_response(response)
        return response
        
    def handle_feat(self, args):
        """Handle FEAT command"""
        response = '211-Features:\r\n PASV\r\n UTF8\r\n SIZE\r\n211 End'
        self.send_response(response)
        return response
        
    def handle_pwd(self, args):
        """Handle PWD command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            response = f'257 "{self.current_dir}" is the current directory'
            
        self.send_response(response)
        return response
        
    def handle_cwd(self, path):
        """Handle CWD command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            new_path = self.fs.normalize_path(self.current_dir, path)
            
            if self.fs.is_dir(new_path):
                self.current_dir = new_path
                response = f'250 Directory changed to {new_path}'
            else:
                response = f'550 Failed to change directory'
                
        self.send_response(response)
        return response
        
    def handle_cdup(self, args):
        """Handle CDUP command"""
        return self.handle_cwd('..')
        
    def handle_type(self, type_code):
        """Handle TYPE command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            response = '200 Type set to ' + type_code
            
        self.send_response(response)
        return response
        
    def handle_pasv(self, args):
        """Handle PASV command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
            self.send_response(response)
            return response
            
        # Close any existing passive server
        if self.passive_server:
            self.passive_server.close()
            
        # Create a passive server
        self.passive_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.passive_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.passive_server.bind(('0.0.0.0', 0))
        self.passive_server.listen(1)
        
        # Get assigned port
        _, self.passive_port = self.passive_server.getsockname()
        
        # Format response
        server_ip = socket.gethostbyname(socket.gethostname())
        ip_parts = server_ip.split('.')
        port_high = self.passive_port // 256
        port_low = self.passive_port % 256
        
        response = f'227 Entering Passive Mode ({ip_parts[0]},{ip_parts[1]},{ip_parts[2]},{ip_parts[3]},{port_high},{port_low})'
        self.send_response(response)
        
        # Start thread to accept connection
        threading.Thread(target=self.accept_passive_connection, daemon=True).start()
        
        return response
        
    def accept_passive_connection(self):
        """Accept connection on passive socket"""
        try:
            self.passive_server.settimeout(20)  # 20 second timeout
            conn, addr = self.passive_server.accept()
            self.data_socket = conn
        except socket.timeout:
            print("Passive connection timed out")
        except Exception as e:
            print(f"Error accepting passive connection: {str(e)}")
        finally:
            self.passive_server.close()
            self.passive_server = None
            
    def handle_port(self, args):
        """Handle PORT command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
            self.send_response(response)
            return response
            
        # Parse PORT arguments
        parts = args.split(',')
        if len(parts) != 6:
            response = '501 Invalid PORT command'
            self.send_response(response)
            return response
            
        # Extract IP and port
        ip = '.'.join(parts[:4])
        port = (int(parts[4]) << 8) + int(parts[5])
        
        # Close any existing data socket
        if self.data_socket:
            self.data_socket.close()
            
        # Create new data socket
        try:
            self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.data_socket.connect((ip, port))
            response = '200 PORT command successful'
        except Exception as e:
            self.data_socket = None
            response = '425 Failed to establish connection'
            
        self.send_response(response)
        return response
        
    def handle_list(self, args):
        """Handle LIST command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
            self.send_response(response)
            return response
            
        if not self.data_socket and not self.passive_server:
            response = '425 Use PORT or PASV first'
            self.send_response(response)
            return response
            
        # Wait for passive connection if needed
        if self.passive_server and not self.data_socket:
            self.send_response('150 Opening data connection')
            time.sleep(1)
            if not self.data_socket:
                response = '425 Failed to establish connection'
                self.send_response(response)
                return response
                
        # Send directory listing
        path = args.strip() if args.strip() else self.current_dir
        path = self.fs.normalize_path(self.current_dir, path)
        
        if not self.fs.is_dir(path):
            response = '550 No such directory'
            self.send_response(response)
            return response
            
        listing = ""
        for item in self.fs.list_dir(path):
            if self.fs.is_dir(os.path.join(path, item)):
                listing += f"drwxr-xr-x 2 ftp ftp 4096 Aug 23 12:34 {item}\r\n"
            else:
                listing += f"-rw-r--r-- 1 ftp ftp 2048 Aug 23 12:34 {item}\r\n"
                
        self.send_response('150 Opening ASCII mode data connection for file list')
        self.send_data(listing.encode('utf-8'))
        self.send_response('226 Transfer complete')
        return '226 Transfer complete'
        
    def handle_nlst(self, args):
        """Handle NLST command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
            self.send_response(response)
            return response
            
        if not self.data_socket and not self.passive_server:
            response = '425 Use PORT or PASV first'
            self.send_response(response)
            return response
            
        # Wait for passive connection if needed
        if self.passive_server and not self.data_socket:
            self.send_response('150 Opening data connection')
            time.sleep(1)
            if not self.data_socket:
                response = '425 Failed to establish connection'
                self.send_response(response)
                return response
                
        # Send directory listing (names only)
        path = args.strip() if args.strip() else self.current_dir
        path = self.fs.normalize_path(self.current_dir, path)
        
        if not self.fs.is_dir(path):
            response = '550 No such directory'
            self.send_response(response)
            return response
            
        listing = "\r\n".join(self.fs.list_dir(path)) + "\r\n"
                
        self.send_response('150 Opening ASCII mode data connection for file list')
        self.send_data(listing.encode('utf-8'))
        self.send_response('226 Transfer complete')
        return '226 Transfer complete'
        
    def handle_retr(self, path):
        """Handle RETR command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
            self.send_response(response)
            return response
            
        if not self.data_socket and not self.passive_server:
            response = '425 Use PORT or PASV first'
            self.send_response(response)
            return response
            
        # Wait for passive connection if needed
        if self.passive_server and not self.data_socket:
            self.send_response('150 Opening data connection')
            time.sleep(1)
            if not self.data_socket:
                response = '425 Failed to establish connection'
                self.send_response(response)
                return response
                
        # Send file
        full_path = self.fs.normalize_path(self.current_dir, path)
        
        # Check if file exists
        if not self.fs.file_exists(full_path):
            response = '550 No such file'
            self.send_response(response)
            return response
            
        # Get file content
        content = self.fs.get_file(full_path)
        if content is None:
            # File exists in structure but no content defined
            content = f"This is the content of {os.path.basename(full_path)}\n"
            
        self.send_response('150 Opening data connection for file transfer')
        self.send_data(content.encode('utf-8'))
        self.send_response('226 Transfer complete')
        return '226 Transfer complete'
        
    def handle_stor(self, path):
        """Handle STOR command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
            self.send_response(response)
            return response
            
        if not self.data_socket and not self.passive_server:
            response = '425 Use PORT or PASV first'
            self.send_response(response)
            return response
            
        # Wait for passive connection if needed
        if self.passive_server and not self.data_socket:
            self.send_response('150 Opening data connection')
            time.sleep(1)
            if not self.data_socket:
                response = '425 Failed to establish connection'
                self.send_response(response)
                return response
                
        # In a honeypot, we don't actually store files
        self.send_response('150 Opening data connection for file upload')
        
        # Read data but don't store it
        try:
            self.data_socket.settimeout(10)
            data = b''
            while True:
                chunk = self.data_socket.recv(1024)
                if not chunk:
                    break
                data += chunk
            
            self.data_socket.close()
            self.data_socket = None
            
            # Log the upload attempt
            self.log_manager.logger.info(f"File upload attempt: {path}, size: {len(data)} bytes")
            
            self.send_response('226 Transfer complete')
            return '226 Transfer complete'
        except Exception as e:
            if self.data_socket:
                self.data_socket.close()
                self.data_socket = None
            self.send_response('426 Connection closed; transfer aborted')
            return '426 Connection closed; transfer aborted'
            
    def handle_dele(self, path):
        """Handle DELE command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            # In a honeypot, pretend to delete but don't actually do it
            full_path = self.fs.normalize_path(self.current_dir, path)
            if self.fs.file_exists(full_path) and not self.fs.is_dir(full_path):
                response = '250 File deleted'
            else:
                response = '550 No such file'
                
        self.send_response(response)
        return response
        
    def handle_rmd(self, path):
        """Handle RMD command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            # In a honeypot, pretend to delete but don't actually do it
            full_path = self.fs.normalize_path(self.current_dir, path)
            if self.fs.is_dir(full_path):
                response = '250 Directory deleted'
            else:
                response = '550 No such directory'
                
        self.send_response(response)
        return response
        
    def handle_mkd(self, path):
        """Handle MKD command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            # In a honeypot, pretend to create but don't actually do it
            full_path = self.fs.normalize_path(self.current_dir, path)
            response = f'257 "{full_path}" directory created'
                
        self.send_response(response)
        return response
        
    def handle_rnfr(self, path):
        """Handle RNFR command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        else:
            # Store path for RNTO
            self.rename_from = self.fs.normalize_path(self.current_dir, path)
            if self.fs.file_exists(self.rename_from) or self.fs.is_dir(self.rename_from):
                response = '350 Ready for RNTO'
            else:
                response = '550 No such file or directory'
                
        self.send_response(response)
        return response
        
    def handle_rnto(self, path):
        """Handle RNTO command"""
        if not self.authenticated:
            response = '530 Please login with USER and PASS'
        elif not hasattr(self, 'rename_from'):
            response = '503 RNFR required first'
        else:
            # In a honeypot, pretend to rename but don't actually do it
            rename_to = self.fs.normalize_path(self.current_dir, path)
            response = '250 Rename successful'
            delattr(self, 'rename_from')
                
        self.send_response(response)
        return response
        
    def handle_quit(self, args):
        """Handle QUIT command"""
        response = '221 Goodbye'
        self.send_response(response)
        self.close()
        return response

# Main FTP honeypot class
class FTPHoneypot:
    def __init__(self, config=None, db_manager=None, log_manager=None):
        self.config = config or load_config()
        self.db_manager = db_manager or DatabaseManager("nexdis.db")
        self.log_manager = log_manager or LogManager()
        self.server_socket = None
        self.running = False
        
    def start(self):
        """Start FTP honeypot server"""
        ftp_config = self.config.get('ftp', {})
        
        if not ftp_config.get('enabled', True):
            print("FTP honeypot disabled in config")
            return
            
        port = ftp_config.get('port', 2121)
        interface = ftp_config.get('interface', '0.0.0.0')
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((interface, port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"FTP honeypot listening on {interface}:{port}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {str(e)}")
        except Exception as e:
            print(f"Error starting FTP honeypot: {str(e)}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                
    def _handle_client(self, client_socket, client_address):
        """Handle a client connection"""
        session = FTPSession(
            client_socket,
            client_address,
            self.config.get('ftp', {}),
            self.db_manager,
            self.log_manager
        )
        session.start()
        
    def stop(self):
        """Stop FTP honeypot server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("FTP honeypot stopped")

# Run as standalone
if __name__ == "__main__":
    honeypot = FTPHoneypot()
    try:
        honeypot.start()
    except KeyboardInterrupt:
        print("\nShutting down FTP honeypot...")
        honeypot.stop()
        print("Shutdown complete")