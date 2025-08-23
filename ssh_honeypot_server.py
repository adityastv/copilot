# Libraries
import logging
from logging.handlers import RotatingFileHandler
import socket
import paramiko 
import threading
import json
import time
import os
import random
import sqlite3
from datetime import datetime
import ipaddress
import uuid

# Constants
VERSION = "1.0.0"
SSH_BANNER = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1"
DEFAULT_PORT = 2223
CONFIG_FILE = "config.json"
DATABASE_FILE = "nexdis.db"

# Ensure directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Configuration
class Config:
    def __init__(self):
        self.config = {
            "ssh": {
                "enabled": True,
                "port": 2223,
                "interface": "0.0.0.0",
                "banner": SSH_BANNER,
                "key_file": "server.key"
            },
            "logging": {
                "level": "INFO",
                "max_size": 10485760,  # 10MB
                "backup_count": 10
            },
            "emulation": {
                "hostname": "corporate-jumpbox2",
                "username": "corpuser1",
                "filesystem": {
                    "/usr/local": ["jumpbox1.conf", "system.log", "backup.tar.gz"],
                    "/home/corpuser1": [".bashrc", ".profile", "notes.txt"]
                }
            },
            "deception": {
                "sensitivity": "medium",  # low, medium, high
                "interaction_level": "medium"  # low, medium, high
            },
            "credentials": {
                "accepted_credentials": [
                    {"username": "admin", "password": "password123"},
                    {"username": "root", "password": "toor"},
                    {"username": "user", "password": "password"}
                ]
            }
        }
        
        # Load config from file if exists
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    # Merge saved config with default
                    self._deep_merge(self.config, saved_config)
            except Exception as e:
                print(f"Error loading config: {e}")
                
    def _deep_merge(self, target, source):
        """Recursively merge source dict into target dict"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
                
    def save(self):
        """Save current config to file"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def get(self, *keys):
        """Get a config value by path of keys"""
        result = self.config
        for key in keys:
            if key in result:
                result = result[key]
            else:
                return None
        return result

# Initialize config
config = Config()

# Setup logging
class LogManager:
    def __init__(self, config):
        self.config = config
        
        # Main logger
        self.main_logger = self._setup_logger(
            'NexdisMain', 
            os.path.join('logs', 'nexdis.log'),
            config.get('logging', 'level')
        )
        
        # Connection logger
        self.connection_logger = self._setup_logger(
            'ConnectionLog', 
            os.path.join('logs', 'connections.log'),
            config.get('logging', 'level')
        )
        
        # Credentials logger
        self.creds_logger = self._setup_logger(
            'CredsLogger', 
            os.path.join('logs', 'credentials.log'),
            config.get('logging', 'level')
        )
        
        # Command logger
        self.command_logger = self._setup_logger(
            'CommandLogger', 
            os.path.join('logs', 'commands.log'),
            config.get('logging', 'level')
        )
        
        # Threat logger
        self.threat_logger = self._setup_logger(
            'ThreatLogger', 
            os.path.join('logs', 'threats.log'),
            config.get('logging', 'level')
        )
        
    def _setup_logger(self, name, log_file, level):
        """Setup and return a logger instance"""
        logger = logging.getLogger(name)
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        logger.setLevel(level_map.get(level, logging.INFO))
        
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=self.config.get('logging', 'max_size'), 
            backupCount=self.config.get('logging', 'backup_count')
        )
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_connection(self, client_ip, port, protocol, success=False):
        """Log a connection attempt"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'port': port,
            'protocol': protocol,
            'success': success
        }
        self.connection_logger.info(json.dumps(data))
        return data
    
    def log_credentials(self, client_ip, username, password, success=False):
        """Log credential attempt"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'username': username,
            'password': password,
            'success': success
        }
        self.creds_logger.info(json.dumps(data))
        return data
    
    def log_command(self, client_ip, session_id, command, output):
        """Log a command execution"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'session_id': session_id,
            'command': command,
            'output': output
        }
        self.command_logger.info(json.dumps(data))
        return data
    
    def log_threat(self, client_ip, threat_type, confidence, details):
        """Log a detected threat"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'threat_type': threat_type,
            'confidence': confidence,
            'details': details
        }
        self.threat_logger.info(json.dumps(data))
        return data

# Initialize logging
log_manager = LogManager(config)

# Database manager
class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.init_db()
        
    def get_connection(self):
        """Get a database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        """Initialize the database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create connections table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            port INTEGER NOT NULL,
            protocol TEXT NOT NULL,
            success INTEGER NOT NULL
        )
        ''')
        
        # Create credentials table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            success INTEGER NOT NULL
        )
        ''')
        
        # Create commands table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            session_id TEXT NOT NULL,
            command TEXT NOT NULL,
            output TEXT NOT NULL
        )
        ''')
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            start_time TEXT NOT NULL,
            end_time TEXT,
            client_ip TEXT NOT NULL,
            protocol TEXT NOT NULL,
            username TEXT,
            commands_count INTEGER DEFAULT 0
        )
        ''')
        
        # Create threats table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS threats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            threat_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            details TEXT NOT NULL
        )
        ''')
        
        conn.commit()
    
    def add_connection(self, data):
        """Add connection record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO connections (timestamp, client_ip, port, protocol, success) VALUES (?, ?, ?, ?, ?)",
            (data['timestamp'], data['client_ip'], data['port'], data['protocol'], 1 if data['success'] else 0)
        )
        conn.commit()
        return cursor.lastrowid
    
    def add_credentials(self, data):
        """Add credentials record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO credentials (timestamp, client_ip, username, password, success) VALUES (?, ?, ?, ?, ?)",
            (data['timestamp'], data['client_ip'], data['username'], data['password'], 1 if data['success'] else 0)
        )
        conn.commit()
        return cursor.lastrowid
    
    def add_command(self, data):
        """Add command record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO commands (timestamp, client_ip, session_id, command, output) VALUES (?, ?, ?, ?, ?)",
            (data['timestamp'], data['client_ip'], data['session_id'], data['command'], data['output'])
        )
        cursor.execute(
            "UPDATE sessions SET commands_count = commands_count + 1 WHERE id = ?",
            (data['session_id'],)
        )
        conn.commit()
        return cursor.lastrowid
    
    def start_session(self, session_id, client_ip, protocol, username=None):
        """Record the start of a new session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO sessions (id, start_time, client_ip, protocol, username) VALUES (?, ?, ?, ?, ?)",
            (session_id, now, client_ip, protocol, username)
        )
        conn.commit()
    
    def end_session(self, session_id):
        """Record the end of a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE sessions SET end_time = ? WHERE id = ?",
            (now, session_id)
        )
        conn.commit()
    
    def add_threat(self, data):
        """Add threat record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO threats (timestamp, client_ip, threat_type, confidence, details) VALUES (?, ?, ?, ?, ?)",
            (data['timestamp'], data['client_ip'], data['threat_type'], data['confidence'], json.dumps(data['details']))
        )
        conn.commit()
        return cursor.lastrowid
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

# Initialize database
db_manager = DatabaseManager(DATABASE_FILE)

# File system emulation
class FileSystemEmulator:
    def __init__(self, config):
        self.config = config
        self.filesystem = config.get('emulation', 'filesystem')
        self.current_dir = "/home/" + config.get('emulation', 'username')
        
        # File contents
        self.file_contents = {
            "/usr/local/jumpbox1.conf": "# Configuration for jumpbox1\nUSER=corpuser1\nMASTER_SERVER=192.168.1.100\nBACKUP_SERVER=192.168.1.101\nACCESS_KEY=hj2Kla91nMzpQ7sR\n",
            "/usr/local/system.log": "Aug 20 14:23:12 jumpbox2 sshd[1234]: Accepted password for corpuser1 from 192.168.1.50\nAug 20 14:25:18 jumpbox2 sudo: corpuser1 : TTY=pts/0 ; PWD=/home/corpuser1 ; USER=root ; COMMAND=/usr/bin/apt update\nAug 20 16:12:45 jumpbox2 sshd[1842]: Failed password for invalid user test from 203.0.113.100 port 39654 ssh2\n",
            "/home/corpuser1/notes.txt": "TODO:\n- Update firewall rules for new subnet\n- Check VPN access for remote team\n- Ask admin@example.com for access to database server\n",
        }
    
    def get_full_path(self, path):
        """Convert relative path to absolute path"""
        if path.startswith('/'):
            return path
        elif self.current_dir.endswith('/'):
            return self.current_dir + path
        else:
            return self.current_dir + '/' + path
    
    def list_files(self, directory=None):
        """List files in the given directory"""
        if directory is None:
            directory = self.current_dir
            
        if directory in self.filesystem:
            return self.filesystem[directory]
        return []
    
    def read_file(self, filepath):
        """Read the contents of a file"""
        full_path = self.get_full_path(filepath)
        
        # Check if file exists
        dir_path = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        if dir_path in self.filesystem and filename in self.filesystem[dir_path]:
            return self.file_contents.get(full_path, f"File {filepath} exists but has no content.")
        
        return f"cat: {filepath}: No such file or directory"
    
    def change_directory(self, path):
        """Change current directory"""
        if path == "..":
            # Go up one directory
            self.current_dir = os.path.dirname(self.current_dir)
            if not self.current_dir:
                self.current_dir = "/"
            return True
        
        if path.startswith('/'):
            # Absolute path
            new_path = path
        else:
            # Relative path
            if self.current_dir.endswith('/'):
                new_path = self.current_dir + path
            else:
                new_path = self.current_dir + '/' + path
        
        # Check if directory exists
        if new_path in self.filesystem:
            self.current_dir = new_path
            return True
        
        return False
    
    def get_current_directory(self):
        """Get current directory path"""
        return self.current_dir

# Emulated Shell
class EmulatedShell:
    def __init__(self, channel, client_ip, session_id, config, fs_emulator, log_manager, db_manager):
        self.channel = channel
        self.client_ip = client_ip
        self.session_id = session_id
        self.config = config
        self.fs = fs_emulator
        self.log_manager = log_manager
        self.db_manager = db_manager
        self.hostname = config.get('emulation', 'hostname')
        self.username = config.get('emulation', 'username')
        self.command_history = []
        
    def start(self):
        """Start the emulated shell"""
        # Send initial prompt
        self.send_prompt()
        
        # Main command loop
        command = b""
        while True:
            char = self.channel.recv(1)
            if not char:
                break
            
            # Echo character back to client
            self.channel.send(char)
            
            if char == b'\r':
                # Command completed, process it
                cmd_str = command.decode('utf-8', errors='ignore').strip()
                if cmd_str:
                    self.process_command(cmd_str)
                
                # Reset command buffer
                command = b""
            else:
                # Add character to command buffer
                command += char
                
        # Session ended
        self.db_manager.end_session(self.session_id)
    
    def send_prompt(self):
        """Send the command prompt"""
        prompt = f"{self.username}@{self.hostname}:{self.fs.get_current_directory()}$ "
        self.channel.send(prompt.encode('utf-8'))
    
    def process_command(self, command):
        """Process a shell command"""
        self.channel.send(b"\r\n")
        
        # Split command and arguments
        parts = command.split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        # Process command
        output = ""
        if cmd == "exit" or cmd == "logout":
            output = "Goodbye!"
            self.channel.send(output.encode('utf-8') + b"\r\n")
            self.channel.close()
            return
            
        elif cmd == "pwd":
            output = self.fs.get_current_directory()
            
        elif cmd == "cd":
            if not args:
                # cd without args goes to home directory
                self.fs.change_directory(f"/home/{self.username}")
                output = ""
            else:
                if self.fs.change_directory(args[0]):
                    output = ""
                else:
                    output = f"cd: {args[0]}: No such file or directory"
                    
        elif cmd == "ls":
            # Basic ls implementation
            directory = None
            if args:
                directory = args[0]
            files = self.fs.list_files(directory)
            output = "  ".join(files)
            
        elif cmd == "cat":
            if not args:
                output = "cat: missing operand"
            else:
                output = self.fs.read_file(args[0])
                
        elif cmd == "whoami":
            output = self.username
            
        elif cmd == "hostname":
            output = self.hostname
            
        elif cmd == "uname":
            if "-a" in args:
                output = "Linux jumpbox2 5.15.0-60-generic #66-Ubuntu SMP Fri Jan 20 14:29:49 UTC 2023 x86_64 GNU/Linux"
            else:
                output = "Linux"
                
        elif cmd == "id":
            output = f"uid=1000({self.username}) gid=1000({self.username}) groups=1000({self.username}),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev)"
            
        elif cmd == "date":
            output = datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")
            
        elif cmd == "echo":
            output = " ".join(args)
            
        elif cmd == "ps":
            output = "  PID TTY          TIME CMD\n"
            output += "    1 ?        00:00:04 systemd\n"
            output += "  678 ?        00:00:01 sshd\n"
            output += "  923 pts/0    00:00:00 bash\n"
            output += " 1245 pts/0    00:00:00 ps"
            
        elif cmd == "netstat":
            if "-tuln" in command:
                output = "Active Internet connections (only servers)\n"
                output += "Proto Recv-Q Send-Q Local Address           Foreign Address         State\n"
                output += "tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN\n"
                output += "tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN\n"
                output += "tcp6       0      0 :::22                   :::*                    LISTEN"
            else:
                output = "Use netstat -tuln to show listening ports"
                
        elif cmd == "ifconfig" or cmd == "ip":
            output = "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
            output += "        inet 192.168.1.5  netmask 255.255.255.0  broadcast 192.168.1.255\n"
            output += "        inet6 fe80::216:3eff:fe14:1dc3  prefixlen 64  scopeid 0x20<link>\n"
            output += "        ether 00:16:3e:14:1d:c3  txqueuelen 1000  (Ethernet)"
            
        elif cmd == "wget" or cmd == "curl":
            output = f"Trying to connect to {' '.join(args)}...\nConnection failed: Network unreachable"
            
        elif cmd == "help":
            output = "Available commands: cd, cat, date, echo, exit, hostname, id, ifconfig, ls, netstat, ps, pwd, uname, whoami"
            
        else:
            output = f"Command not found: {cmd}. Try 'help' for available commands."
        
        # Log the command and output
        if output:
            self.channel.send(output.encode('utf-8') + b"\r\n")
            
        # Log command
        log_data = self.log_manager.log_command(
            self.client_ip, 
            self.session_id, 
            command, 
            output
        )
        self.db_manager.add_command(log_data)
        
        # Add to command history
        self.command_history.append(command)
        
        # Check for potential threats based on command
        self.analyze_command(command)
        
        # Send new prompt
        self.send_prompt()
    
    def analyze_command(self, command):
        """Analyze command for potential threats"""
        # Simple threat detection examples - in a real system this would use ML
        threat_indicators = {
            "wget": ("file_download", 0.7, "Attempted to download file"),
            "curl": ("file_download", 0.7, "Attempted to download file"),
            "rm -rf": ("destructive", 0.9, "Attempted destructive command"),
            "chmod 777": ("permission_change", 0.8, "Attempted to change permissions"),
            "|": ("command_chaining", 0.5, "Command chaining detected"),
            "nc": ("network_tool", 0.8, "Netcat command detected"),
            "nmap": ("scanning", 0.9, "Port scanning attempted"),
            ">": ("output_redirect", 0.4, "Output redirection detected"),
            "sudo": ("privilege_escalation", 0.7, "Privilege escalation attempted")
        }
        
        for indicator, (threat_type, confidence, details) in threat_indicators.items():
            if indicator in command:
                threat_data = {
                    'timestamp': datetime.now().isoformat(),
                    'client_ip': self.client_ip,
                    'threat_type': threat_type,
                    'confidence': confidence,
                    'details': {
                        'command': command,
                        'description': details,
                        'session_id': self.session_id
                    }
                }
                self.log_manager.log_threat(
                    self.client_ip,
                    threat_type,
                    confidence,
                    threat_data['details']
                )
                self.db_manager.add_threat(threat_data)

# SSH server implementation
class SSHServer(paramiko.ServerInterface):
    def __init__(self, client_ip, config, log_manager, db_manager):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.config = config
        self.log_manager = log_manager
        self.db_manager = db_manager
        self.session_id = str(uuid.uuid4())
        self.username = None
        self.auth_attempts = 0
        self.max_auth_attempts = 3
        
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
        
    def check_auth_password(self, username, password):
        self.auth_attempts += 1
        self.username = username
        
        # Log the credential attempt
        success = False
        
        # Check against accepted credentials
        accepted_credentials = self.config.get('credentials', 'accepted_credentials')
        for cred in accepted_credentials:
            if username == cred['username'] and password == cred['password']:
                success = True
                break
        
        # Log the attempt
        cred_data = self.log_manager.log_credentials(
            self.client_ip, 
            username, 
            password, 
            success
        )
        self.db_manager.add_credentials(cred_data)
        
        # In honeypot mode, always accept credentials after logging
        # But in a real scenario we would use: return paramiko.AUTH_SUCCESSFUL if success else paramiko.AUTH_FAILED
        
        # For honeypot purposes, we'll accept all credentials
        if self.auth_attempts >= self.max_auth_attempts:
            # After a few attempts, accept any credentials to allow attackers in
            return paramiko.AUTH_SUCCESSFUL
            
        # Randomly accept credentials earlier to increase engagement
        if random.random() < 0.3:
            return paramiko.AUTH_SUCCESSFUL
            
        return paramiko.AUTH_FAILED
    
    def get_allowed_auths(self, username):
        return 'password'
        
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
        
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
        
    def check_channel_exec_request(self, channel, command):
        # Log the exec command
        command_str = command.decode('utf-8', errors='ignore')
        log_data = self.log_manager.log_command(
            self.client_ip, 
            self.session_id, 
            command_str, 
            "Command execution attempted via exec channel"
        )
        self.db_manager.add_command(log_data)
        
        # For honeypot purposes, accept the exec request
        return True

# Handler for client connections
def handle_client(client, addr, config, log_manager, db_manager):
    client_ip = addr[0]
    client_port = addr[1]
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    
    # Log the connection
    connection_data = log_manager.log_connection(
        client_ip, 
        client_port, 
        'ssh', 
        success=True
    )
    db_manager.add_connection(connection_data)
    
    try:
        # Set up SSH transport
        transport = paramiko.Transport(client)
        transport.local_version = config.get('ssh', 'banner')
        
        # Load host key
        host_key_file = config.get('ssh', 'key_file')
        host_key = paramiko.RSAKey(filename=host_key_file)
        transport.add_server_key(host_key)
        
        # Initialize server
        server = SSHServer(client_ip, config, log_manager, db_manager)
        transport.start_server(server=server)
        
        # Record session start
        db_manager.start_session(session_id, client_ip, 'ssh')
        
        # Accept channel
        channel = transport.accept(20)
        if channel is None:
            log_manager.main_logger.info(f"No channel from {client_ip}")
            return
        
        # Wait for auth
        server.event.wait(10)
        if not server.event.is_set():
            log_manager.main_logger.info(f"No auth request from {client_ip}")
            return
            
        # Send welcome banner
        welcome_banner = f"""
Welcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-60-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}

  System load:  0.08               Users logged in:        1
  Usage of /:   39.8% of 30.63GB   IPv4 address for eth0:  192.168.1.5
  Memory usage: 22%                IPv4 address for docker0: 172.17.0.1
  Swap usage:   0%                 IPv4 address for tun0:  10.8.0.1
  Temperature:  38.0 C             Processes:              123

Last login: {(datetime.now() - datetime.timedelta(days=random.randint(0, 5), hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime('%a %b %d %H:%M:%S %Y')} from 192.168.1.50
"""
        channel.send(welcome_banner.encode('utf-8') + b"\r\n")
        
        # Start emulated shell
        fs_emulator = FileSystemEmulator(config)
        shell = EmulatedShell(channel, client_ip, session_id, config, fs_emulator, log_manager, db_manager)
        shell.start()
        
    except Exception as e:
        log_manager.main_logger.error(f"Error handling SSH client {client_ip}: {str(e)}")
    finally:
        try:
            transport.close()
        except:
            pass
        client.close()

# Main honeypot server
def start_ssh_honeypot(config, log_manager, db_manager):
    """Start the SSH honeypot server"""
    host = config.get('ssh', 'interface')
    port = config.get('ssh', 'port')
    
    # Create server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((host, port))
        sock.listen(100)
        log_manager.main_logger.info(f"SSH honeypot listening on {host}:{port}")
        print(f"SSH honeypot listening on {host}:{port}")
        
        while True:
            client, addr = sock.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client, addr, config, log_manager, db_manager),
                daemon=True
            )
            client_thread.start()
            
    except Exception as e:
        log_manager.main_logger.error(f"Error in SSH honeypot: {str(e)}")
    finally:
        sock.close()

# Generate SSH key if needed
def generate_ssh_key(key_file):
    """Generate an SSH key if one doesn't exist"""
    if not os.path.exists(key_file):
        print(f"Generating new SSH host key: {key_file}")
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(key_file)

# Main function
def main():
    """Main entry point"""
    print(f"NEXDIS SSH Honeypot v{VERSION}")
    print("Starting services...")
    
    # Initialize config
    config = Config()
    
    # Generate SSH key if needed
    key_file = config.get('ssh', 'key_file')
    generate_ssh_key(key_file)
    
    # Initialize logging
    log_manager = LogManager(config)
    
    # Initialize database
    db_manager = DatabaseManager(DATABASE_FILE)
    
    # Log startup
    log_manager.main_logger.info(f"NEXDIS SSH Honeypot v{VERSION} starting")
    
    # Start SSH honeypot
    if config.get('ssh', 'enabled'):
        ssh_thread = threading.Thread(
            target=start_ssh_honeypot,
            args=(config, log_manager, db_manager),
            daemon=True
        )
        ssh_thread.start()
        
    try:
        # Keep main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        log_manager.main_logger.info("NEXDIS SSH Honeypot shutting down")
        db_manager.close()
        print("Shutdown complete")

if __name__ == "__main__":
    main()