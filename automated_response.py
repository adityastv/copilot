import os
import json
import logging
import threading
import time
import uuid
import random
import subprocess
import ipaddress
import socket
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import requests
from collections import defaultdict
import queue

# Ensure required directories exist
os.makedirs("logs/incidents", exist_ok=True)
os.makedirs("data/responses", exist_ok=True)
os.makedirs("data/quarantine", exist_ok=True)

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/incidents/automated_response.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutomatedResponse")

class ResponseAction:
    """Base class for response actions"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any]):
        self.session_id = session_id
        self.client_ip = client_ip
        self.threat_data = threat_data
        self.action_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.successful = False
        self.notes = []
        
    def execute(self) -> bool:
        """Execute the response action"""
        raise NotImplementedError("Subclasses must implement execute()")
        
    def add_note(self, note: str) -> None:
        """Add a note to the action"""
        timestamp = datetime.now().isoformat()
        self.notes.append({"timestamp": timestamp, "note": note})
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        return {
            "action_id": self.action_id,
            "action_type": self.__class__.__name__,
            "session_id": self.session_id,
            "client_ip": self.client_ip,
            "timestamp": self.timestamp.isoformat(),
            "successful": self.successful,
            "notes": self.notes
        }


class ContainmentAction(ResponseAction):
    """Action to contain a threat"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any], 
                 containment_type: str = "session_isolation"):
        super().__init__(session_id, client_ip, threat_data)
        self.containment_type = containment_type
        
    def execute(self) -> bool:
        """Execute the containment action"""
        if self.containment_type == "session_isolation":
            # Isolate the session to prevent lateral movement
            success = self._isolate_session()
        elif self.containment_type == "network_isolation":
            # Isolate the IP at the network level
            success = self._isolate_network()
        elif self.containment_type == "ip_block":
            # Block the IP address
            success = self._block_ip()
        elif self.containment_type == "service_isolation":
            # Isolate a specific service
            success = self._isolate_service()
        else:
            self.add_note(f"Unknown containment type: {self.containment_type}")
            return False
            
        self.successful = success
        return success
        
    def _isolate_session(self) -> bool:
        """Isolate a session"""
        try:
            # In a real environment, this would modify firewall rules or container isolation
            # For the honeypot, we'll just log the action
            self.add_note(f"Session {self.session_id} isolated")
            
            # Save session data for forensic analysis
            isolation_file = f"data/quarantine/session_{self.session_id}.json"
            with open(isolation_file, 'w') as f:
                json.dump({
                    "session_id": self.session_id,
                    "client_ip": self.client_ip,
                    "threat_data": self.threat_data,
                    "isolation_time": datetime.now().isoformat(),
                    "isolation_type": "session"
                }, f, indent=2)
                
            logger.info(f"Session {self.session_id} isolated due to {self.threat_data.get('threat_severity', 'unknown')} severity threat")
            return True
        except Exception as e:
            self.add_note(f"Error isolating session: {str(e)}")
            logger.error(f"Error isolating session {self.session_id}: {str(e)}")
            return False
            
    def _isolate_network(self) -> bool:
        """Isolate at network level"""
        try:
            # In a real environment, this would configure network isolation
            # For the honeypot, we'll just log the action
            self.add_note(f"Network isolated for IP {self.client_ip}")
            
            # Save network isolation data
            isolation_file = f"data/quarantine/network_{self.client_ip.replace('.', '_')}.json"
            with open(isolation_file, 'w') as f:
                json.dump({
                    "client_ip": self.client_ip,
                    "session_id": self.session_id,
                    "threat_data": self.threat_data,
                    "isolation_time": datetime.now().isoformat(),
                    "isolation_type": "network"
                }, f, indent=2)
                
            logger.info(f"Network isolated for IP {self.client_ip} due to {self.threat_data.get('threat_severity', 'unknown')} severity threat")
            return True
        except Exception as e:
            self.add_note(f"Error isolating network: {str(e)}")
            logger.error(f"Error isolating network for IP {self.client_ip}: {str(e)}")
            return False
            
    def _block_ip(self) -> bool:
        """Block an IP address"""
        try:
            # In a real environment, this would add firewall rules
            # For the honeypot, we'll just log the action
            self.add_note(f"IP {self.client_ip} blocked")
            
            # Save IP block data
            block_file = f"data/quarantine/ip_block_{self.client_ip.replace('.', '_')}.json"
            with open(block_file, 'w') as f:
                json.dump({
                    "client_ip": self.client_ip,
                    "session_id": self.session_id,
                    "threat_data": self.threat_data,
                    "block_time": datetime.now().isoformat()
                }, f, indent=2)
                
            logger.info(f"IP {self.client_ip} blocked due to {self.threat_data.get('threat_severity', 'unknown')} severity threat")
            return True
        except Exception as e:
            self.add_note(f"Error blocking IP: {str(e)}")
            logger.error(f"Error blocking IP {self.client_ip}: {str(e)}")
            return False
            
    def _isolate_service(self) -> bool:
        """Isolate a specific service"""
        try:
            service = self.threat_data.get("service", "unknown")
            self.add_note(f"Service {service} isolated for IP {self.client_ip}")
            
            # Save service isolation data
            isolation_file = f"data/quarantine/service_{service}_{self.client_ip.replace('.', '_')}.json"
            with open(isolation_file, 'w') as f:
                json.dump({
                    "client_ip": self.client_ip,
                    "session_id": self.session_id,
                    "service": service,
                    "threat_data": self.threat_data,
                    "isolation_time": datetime.now().isoformat(),
                    "isolation_type": "service"
                }, f, indent=2)
                
            logger.info(f"Service {service} isolated for IP {self.client_ip} due to {self.threat_data.get('threat_severity', 'unknown')} severity threat")
            return True
        except Exception as e:
            self.add_note(f"Error isolating service: {str(e)}")
            logger.error(f"Error isolating service for IP {self.client_ip}: {str(e)}")
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        data = super().to_dict()
        data["containment_type"] = self.containment_type
        return data


class DeceptionAction(ResponseAction):
    """Action to deploy deception tactics"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any], 
                 deception_type: str = "fake_vulnerability"):
        super().__init__(session_id, client_ip, threat_data)
        self.deception_type = deception_type
        self.decoy_data = {}
        
    def execute(self) -> bool:
        """Execute the deception action"""
        if self.deception_type == "fake_vulnerability":
            # Deploy fake vulnerability
            success = self._deploy_fake_vulnerability()
        elif self.deception_type == "decoy_files":
            # Deploy decoy files
            success = self._deploy_decoy_files()
        elif self.deception_type == "connection_throttling":
            # Throttle connection to simulate issues
            success = self._throttle_connection()
        elif self.deception_type == "fake_service":
            # Deploy fake service
            success = self._deploy_fake_service()
        else:
            self.add_note(f"Unknown deception type: {self.deception_type}")
            return False
            
        self.successful = success
        return success
        
    def _deploy_fake_vulnerability(self) -> bool:
        """Deploy a fake vulnerability for the attacker to discover"""
        try:
            # Generate fake vulnerability
            vuln_types = [
                "command_injection", "sql_injection", "file_inclusion", 
                "buffer_overflow", "default_credentials"
            ]
            
            vuln_type = random.choice(vuln_types)
            
            # Generate fake vulnerability details
            if vuln_type == "command_injection":
                vuln_details = {
                    "type": "command_injection",
                    "location": f"/var/www/html/admin/{random.choice(['process.php', 'upload.php', 'settings.php'])}",
                    "parameter": random.choice(["cmd", "exec", "command", "run"]),
                    "example": f"?{random.choice(['cmd', 'exec', 'command', 'run'])}=id"
                }
            elif vuln_type == "sql_injection":
                vuln_details = {
                    "type": "sql_injection",
                    "location": f"/var/www/html/{random.choice(['login.php', 'search.php', 'user.php'])}",
                    "parameter": random.choice(["id", "user", "item", "query"]),
                    "example": f"?{random.choice(['id', 'user', 'item', 'query'])}=1' OR '1'='1"
                }
            elif vuln_type == "file_inclusion":
                vuln_details = {
                    "type": "file_inclusion",
                    "location": f"/var/www/html/{random.choice(['page.php', 'view.php', 'include.php'])}",
                    "parameter": random.choice(["file", "page", "include", "template"]),
                    "example": f"?{random.choice(['file', 'page', 'include', 'template'])}=../../../etc/passwd"
                }
            elif vuln_type == "buffer_overflow":
                vuln_details = {
                    "type": "buffer_overflow",
                    "location": f"/usr/local/bin/{random.choice(['service', 'daemon', 'app'])}",
                    "parameter": "input buffer",
                    "example": "Long string of 'A's"
                }
            elif vuln_type == "default_credentials":
                users = ["admin", "administrator", "root", "user", "system"]
                passwords = ["password", "admin123", "root123", "123456", "default"]
                vuln_details = {
                    "type": "default_credentials",
                    "location": f"/var/www/html/{random.choice(['admin', 'cp', 'dashboard'])}/",
                    "username": random.choice(users),
                    "password": random.choice(passwords)
                }
            
            self.decoy_data = vuln_details
            self.add_note(f"Deployed fake {vuln_type} vulnerability")
            
            # In a real system, you would actually create the vulnerable endpoint
            logger.info(f"Deployed fake {vuln_type} vulnerability for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error deploying fake vulnerability: {str(e)}")
            logger.error(f"Error deploying fake vulnerability for session {self.session_id}: {str(e)}")
            return False
            
    def _deploy_decoy_files(self) -> bool:
        """Deploy decoy files for the attacker to find"""
        try:
            # Generate decoy files
            decoy_types = [
                "credentials", "config", "keys", "database", "source_code"
            ]
            
            # Choose 1-3 decoy types
            selected_types = random.sample(decoy_types, random.randint(1, 3))
            decoy_files = []
            
            for decoy_type in selected_types:
                if decoy_type == "credentials":
                    users = ["admin", "root", "user", "service", "backup", "deploy"]
                    hosts = ["db-server", "web-server", "app-server", "mail-server"]
                    file_name = random.choice(["credentials.txt", "passwords.txt", ".credentials", "logins.dat"])
                    file_path = f"/home/{random.choice(['user', 'admin'])}/{file_name}"
                    file_content = "\n".join([
                        f"{random.choice(users)}:{self._generate_fake_password()}:{random.choice(hosts)}"
                        for _ in range(random.randint(3, 8))
                    ])
                    decoy_files.append({
                        "type": "credentials",
                        "path": file_path,
                        "content": file_content
                    })
                elif decoy_type == "config":
                    file_name = random.choice(["config.ini", "settings.conf", "app.cfg", ".env"])
                    file_path = f"/etc/{random.choice(['app', 'web', 'service'])}/{file_name}"
                    file_content = "\n".join([
                        "# Configuration file",
                        f"DB_HOST={random.choice(['localhost', '127.0.0.1', 'db-server'])}",
                        f"DB_USER={random.choice(['dbuser', 'admin', 'root', 'app'])}",
                        f"DB_PASS={self._generate_fake_password()}",
                        f"API_KEY={self._generate_api_key()}",
                        f"DEBUG={random.choice(['true', 'false'])}"
                    ])
                    decoy_files.append({
                        "type": "config",
                        "path": file_path,
                        "content": file_content
                    })
                elif decoy_type == "keys":
                    key_types = ["ssh", "ssl", "pgp", "api"]
                    key_type = random.choice(key_types)
                    file_name = f"{key_type}_{'private' if random.random() < 0.7 else 'public'}.key"
                    file_path = f"/home/{random.choice(['user', 'admin'])}/.keys/{file_name}"
                    
                    if key_type == "ssh":
                        file_content = "-----BEGIN RSA PRIVATE KEY-----\n"
                        file_content += "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/", k=350))
                        file_content += "\n-----END RSA PRIVATE KEY-----"
                    else:
                        file_content = f"-----BEGIN {key_type.upper()} KEY-----\n"
                        file_content += "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/", k=200))
                        file_content += f"\n-----END {key_type.upper()} KEY-----"
                        
                    decoy_files.append({
                        "type": "keys",
                        "path": file_path,
                        "content": file_content
                    })
                elif decoy_type == "database":
                    file_name = random.choice(["backup.sql", "dump.sql", "data.db", "users.sqlite"])
                    file_path = f"/var/backups/{file_name}"
                    
                    # Generate fake SQL or database content
                    if file_name.endswith(".sql"):
                        tables = ["users", "customers", "orders", "products", "accounts"]
                        table = random.choice(tables)
                        file_content = f"-- Database dump\nCREATE TABLE {table} (\n"
                        file_content += "  id INT PRIMARY KEY,\n"
                        file_content += "  username VARCHAR(50),\n"
                        file_content += "  password VARCHAR(100),\n"
                        file_content += "  email VARCHAR(100)\n"
                        file_content += ");\n\n"
                        
                        # Add some fake data
                        for i in range(1, random.randint(5, 10)):
                            file_content += f"INSERT INTO {table} VALUES ({i}, 'user{i}', '{self._generate_fake_password()}', 'user{i}@example.com');\n"
                    else:
                        file_content = f"SQLite format 3\x00{os.urandom(20).hex()}"
                        
                    decoy_files.append({
                        "type": "database",
                        "path": file_path,
                        "content": file_content
                    })
                elif decoy_type == "source_code":
                    languages = ["php", "python", "javascript", "java"]
                    language = random.choice(languages)
                    
                    if language == "php":
                        file_name = random.choice(["auth.php", "admin.php", "config.php", "database.php"])
                        file_path = f"/var/www/html/includes/{file_name}"
                        file_content = "<?php\n"
                        file_content += "// Authentication module\n"
                        file_content += f"$db_host = '{random.choice(['localhost', '127.0.0.1', 'db-server'])}';\n"
                        file_content += f"$db_user = '{random.choice(['dbuser', 'admin', 'root', 'app'])}';\n"
                        file_content += f"$db_pass = '{self._generate_fake_password()}';\n"
                        file_content += "function authenticate($username, $password) {\n"
                        file_content += "  global $db_host, $db_user, $db_pass;\n"
                        file_content += "  $conn = mysqli_connect($db_host, $db_user, $db_pass);\n"
                        file_content += "  $query = \"SELECT * FROM users WHERE username='$username' AND password='$password'\";\n"
                        file_content += "  $result = mysqli_query($conn, $query);\n"
                        file_content += "  return mysqli_num_rows($result) > 0;\n"
                        file_content += "}\n?>"
                    elif language == "python":
                        file_name = random.choice(["auth.py", "config.py", "api.py", "database.py"])
                        file_path = f"/opt/app/{file_name}"
                        file_content = "# Authentication module\n"
                        file_content += "import sqlite3\n\n"
                        file_content += f"DB_HOST = '{random.choice(['localhost', '127.0.0.1', 'db-server'])}'\n"
                        file_content += f"DB_USER = '{random.choice(['dbuser', 'admin', 'root', 'app'])}'\n"
                        file_content += f"DB_PASS = '{self._generate_fake_password()}'\n"
                        file_content += f"API_KEY = '{self._generate_api_key()}'\n\n"
                        file_content += "def authenticate(username, password):\n"
                        file_content += "    conn = sqlite3.connect('users.db')\n"
                        file_content += "    cursor = conn.cursor()\n"
                        file_content += "    cursor.execute(f\"SELECT * FROM users WHERE username='{username}' AND password='{password}'\")\n"
                        file_content += "    return len(cursor.fetchall()) > 0\n"
                    else:
                        file_name = f"Auth.{language}"
                        file_path = f"/opt/app/src/{file_name}"
                        file_content = f"// Authentication module\n// TODO: Implement secure authentication"
                        
                    decoy_files.append({
                        "type": "source_code",
                        "path": file_path,
                        "content": file_content
                    })
            
            self.decoy_data = {"files": decoy_files}
            self.add_note(f"Deployed {len(decoy_files)} decoy files")
            
            # In a real system, you would actually create these files
            logger.info(f"Deployed {len(decoy_files)} decoy files for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error deploying decoy files: {str(e)}")
            logger.error(f"Error deploying decoy files for session {self.session_id}: {str(e)}")
            return False
            
    def _throttle_connection(self) -> bool:
        """Throttle the connection to simulate issues"""
        try:
            # Set throttling parameters
            delay_ms = random.randint(100, 500)
            packet_loss = random.randint(5, 15)
            
            self.decoy_data = {
                "delay_ms": delay_ms,
                "packet_loss_percent": packet_loss
            }
            
            self.add_note(f"Connection throttled with {delay_ms}ms delay and {packet_loss}% packet loss")
            
            # In a real system, you would configure traffic control for this IP
            logger.info(f"Throttled connection for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error throttling connection: {str(e)}")
            logger.error(f"Error throttling connection for session {self.session_id}: {str(e)}")
            return False
            
    def _deploy_fake_service(self) -> bool:
        """Deploy a fake service for the attacker to discover"""
        try:
            # Generate fake service
            service_types = [
                "ftp", "smb", "web_admin", "database", "api"
            ]
            
            service_type = random.choice(service_types)
            port = random.randint(10000, 60000)
            
            # Generate fake service details
            if service_type == "ftp":
                service_details = {
                    "type": "ftp",
                    "port": port,
                    "banner": f"220 FTP Server Ready",
                    "credentials": {
                        "username": random.choice(["admin", "backup", "user"]),
                        "password": self._generate_fake_password()
                    },
                    "files": [
                        "/backups/system.tar.gz",
                        "/configs/server.conf",
                        "/data/users.csv"
                    ]
                }
            elif service_type == "smb":
                service_details = {
                    "type": "smb",
                    "port": port,
                    "hostname": f"FILE-SERVER-{random.randint(1, 9)}",
                    "domain": "WORKGROUP",
                    "shares": [
                        {"name": "public", "path": "/shares/public"},
                        {"name": "backup", "path": "/shares/backup"},
                        {"name": "admin", "path": "/shares/admin", "protected": True}
                    ]
                }
            elif service_type == "web_admin":
                service_details = {
                    "type": "web_admin",
                    "port": port,
                    "server": random.choice(["Apache", "Nginx", "IIS"]),
                    "login_path": "/admin/login.php",
                    "credentials": {
                        "username": random.choice(["admin", "administrator", "root"]),
                        "password": self._generate_fake_password()
                    }
                }
            elif service_type == "database":
                service_details = {
                    "type": "database",
                    "port": port,
                    "dbms": random.choice(["MySQL", "PostgreSQL", "MongoDB"]),
                    "banner": f"Welcome to MySQL Server version 5.7.{random.randint(1, 35)}",
                    "credentials": {
                        "username": random.choice(["root", "admin", "dbuser"]),
                        "password": self._generate_fake_password()
                    }
                }
            elif service_type == "api":
                service_details = {
                    "type": "api",
                    "port": port,
                    "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                    "endpoints": [
                        "/api/users",
                        "/api/config",
                        "/api/status",
                        "/api/admin"
                    ],
                    "api_key": self._generate_api_key()
                }
            
            self.decoy_data = service_details
            self.add_note(f"Deployed fake {service_type} service on port {port}")
            
            # In a real system, you would actually start this service
            logger.info(f"Deployed fake {service_type} service on port {port} for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error deploying fake service: {str(e)}")
            logger.error(f"Error deploying fake service for session {self.session_id}: {str(e)}")
            return False
            
    def _generate_fake_password(self) -> str:
        """Generate a fake password"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(random.choices(chars, k=random.randint(8, 12)))
        
    def _generate_api_key(self) -> str:
        """Generate a fake API key"""
        return "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=32))
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        data = super().to_dict()
        data["deception_type"] = self.deception_type
        data["decoy_data"] = self.decoy_data
        return data


class EvidenceCollectionAction(ResponseAction):
    """Action to collect evidence"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any], 
                 collection_type: str = "session_dump"):
        super().__init__(session_id, client_ip, threat_data)
        self.collection_type = collection_type
        self.evidence_path = None
        
    def execute(self) -> bool:
        """Execute the evidence collection action"""
        if self.collection_type == "session_dump":
            # Dump the entire session
            success = self._dump_session()
        elif self.collection_type == "memory_dump":
            # Dump memory for analysis
            success = self._dump_memory()
        elif self.collection_type == "network_capture":
            # Capture network traffic
            success = self._capture_network()
        elif self.collection_type == "system_logs":
            # Collect system logs
            success = self._collect_logs()
        else:
            self.add_note(f"Unknown collection type: {self.collection_type}")
            return False
            
        self.successful = success
        return success
        
    def _dump_session(self) -> bool:
        """Dump the entire session for analysis"""
        try:
            # Create evidence directory
            evidence_dir = f"data/responses/evidence_{self.session_id}"
            os.makedirs(evidence_dir, exist_ok=True)
            
            # Save session data
            session_file = f"{evidence_dir}/session_data.json"
            with open(session_file, 'w') as f:
                json.dump({
                    "session_id": self.session_id,
                    "client_ip": self.client_ip,
                    "threat_data": self.threat_data,
                    "timestamp": datetime.now().isoformat(),
                    "collection_type": "session_dump"
                }, f, indent=2)
                
            # In a real system, you would dump all session data, commands, etc.
            self.evidence_path = evidence_dir
            self.add_note(f"Session dumped to {evidence_dir}")
            logger.info(f"Collected session dump for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error dumping session: {str(e)}")
            logger.error(f"Error dumping session {self.session_id}: {str(e)}")
            return False
            
    def _dump_memory(self) -> bool:
        """Dump memory for analysis"""
        try:
            # Create evidence directory
            evidence_dir = f"data/responses/evidence_{self.session_id}"
            os.makedirs(evidence_dir, exist_ok=True)
            
            # In a real system, you would create a memory dump
            memory_file = f"{evidence_dir}/memory_dump.bin"
            
            # For the honeypot, just create a placeholder file
            with open(memory_file, 'wb') as f:
                f.write(b"Memory dump placeholder")
                
            self.evidence_path = memory_file
            self.add_note(f"Memory dumped to {memory_file}")
            logger.info(f"Collected memory dump for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error dumping memory: {str(e)}")
            logger.error(f"Error dumping memory for session {self.session_id}: {str(e)}")
            return False
            
    def _capture_network(self) -> bool:
        """Capture network traffic"""
        try:
            # Create evidence directory
            evidence_dir = f"data/responses/evidence_{self.session_id}"
            os.makedirs(evidence_dir, exist_ok=True)
            
            # In a real system, you would start tcpdump or another capture tool
            pcap_file = f"{evidence_dir}/network_capture.pcap"
            
            # For the honeypot, just create a placeholder file
            with open(pcap_file, 'wb') as f:
                f.write(b"PCAP file placeholder")
                
            self.evidence_path = pcap_file
            self.add_note(f"Network traffic captured to {pcap_file}")
            logger.info(f"Captured network traffic for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error capturing network traffic: {str(e)}")
            logger.error(f"Error capturing network traffic for session {self.session_id}: {str(e)}")
            return False
            
    def _collect_logs(self) -> bool:
        """Collect system logs"""
        try:
            # Create evidence directory
            evidence_dir = f"data/responses/evidence_{self.session_id}"
            os.makedirs(evidence_dir, exist_ok=True)
            
            # In a real system, you would collect various system logs
            log_types = ["auth", "syslog", "apache", "mysql", "audit"]
            collected_logs = []
            
            for log_type in log_types:
                log_file = f"{evidence_dir}/{log_type}.log"
                
                # For the honeypot, just create placeholder files
                with open(log_file, 'w') as f:
                    f.write(f"{log_type} log placeholder\n")
                    f.write(f"Session ID: {self.session_id}\n")
                    f.write(f"Client IP: {self.client_ip}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    
                collected_logs.append(log_file)
                
            self.evidence_path = evidence_dir
            self.add_note(f"System logs collected to {evidence_dir}")
            logger.info(f"Collected system logs for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error collecting system logs: {str(e)}")
            logger.error(f"Error collecting system logs for session {self.session_id}: {str(e)}")
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        data = super().to_dict()
        data["collection_type"] = self.collection_type
        data["evidence_path"] = self.evidence_path
        return data


class NotificationAction(ResponseAction):
    """Action to send notifications"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any], 
                 notification_type: str = "email", recipients: List[str] = None):
        super().__init__(session_id, client_ip, threat_data)
        self.notification_type = notification_type
        self.recipients = recipients or ["security@example.com"]
        
    def execute(self) -> bool:
        """Execute the notification action"""
        if self.notification_type == "email":
            # Send email notification
            success = self._send_email()
        elif self.notification_type == "sms":
            # Send SMS notification
            success = self._send_sms()
        elif self.notification_type == "webhook":
            # Send webhook notification
            success = self._send_webhook()
        elif self.notification_type == "siem":
            # Send to SIEM
            success = self._send_to_siem()
        else:
            self.add_note(f"Unknown notification type: {self.notification_type}")
            return False
            
        self.successful = success
        return success
        
    def _send_email(self) -> bool:
        """Send email notification"""
        try:
            # In a real system, you would send an actual email
            severity = self.threat_data.get("threat_severity", "unknown")
            
            # Create email content
            subject = f"[NEXDIS] {severity.upper()} Threat Alert - Session {self.session_id}"
            body = f"""
NEXDIS Threat Alert

Severity: {severity.upper()}
Session ID: {self.session_id}
Client IP: {self.client_ip}
Timestamp: {datetime.now().isoformat()}

Threat Details:
{json.dumps(self.threat_data, indent=2)}

This alert was automatically generated by NEXDIS.
            """
            
            # Log the email (in a real system, you would send it)
            email_file = f"data/responses/email_alert_{self.session_id}.txt"
            with open(email_file, 'w') as f:
                f.write(f"To: {', '.join(self.recipients)}\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"Body:\n{body}")
                
            self.add_note(f"Email notification sent to {', '.join(self.recipients)}")
            logger.info(f"Sent email notification for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error sending email: {str(e)}")
            logger.error(f"Error sending email for session {self.session_id}: {str(e)}")
            return False
            
    def _send_sms(self) -> bool:
        """Send SMS notification"""
        try:
            # In a real system, you would send an actual SMS
            severity = self.threat_data.get("threat_severity", "unknown")
            
            # Create SMS content
            message = f"NEXDIS {severity.upper()} Alert: Threat detected from IP {self.client_ip}. Session ID: {self.session_id}."
            
            # Log the SMS (in a real system, you would send it)
            sms_file = f"data/responses/sms_alert_{self.session_id}.txt"
            with open(sms_file, 'w') as f:
                f.write(f"To: {', '.join(self.recipients)}\n")
                f.write(f"Message: {message}")
                
            self.add_note(f"SMS notification sent to {', '.join(self.recipients)}")
            logger.info(f"Sent SMS notification for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error sending SMS: {str(e)}")
            logger.error(f"Error sending SMS for session {self.session_id}: {str(e)}")
            return False
            
    def _send_webhook(self) -> bool:
        """Send webhook notification"""
        try:
            # In a real system, you would send an actual webhook request
            webhook_url = "https://example.com/webhooks/security"
            
            # Create webhook payload
            payload = {
                "alert_type": "threat_detection",
                "severity": self.threat_data.get("threat_severity", "unknown"),
                "session_id": self.session_id,
                "client_ip": self.client_ip,
                "timestamp": datetime.now().isoformat(),
                "threat_data": self.threat_data
            }
            
            # Log the webhook (in a real system, you would send it)
            webhook_file = f"data/responses/webhook_alert_{self.session_id}.json"
            with open(webhook_file, 'w') as f:
                json.dump({
                    "url": webhook_url,
                    "payload": payload
                }, f, indent=2)
                
            self.add_note(f"Webhook notification sent to {webhook_url}")
            logger.info(f"Sent webhook notification for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error sending webhook: {str(e)}")
            logger.error(f"Error sending webhook for session {self.session_id}: {str(e)}")
            return False
            
    def _send_to_siem(self) -> bool:
        """Send to SIEM"""
        try:
            # In a real system, you would send to your SIEM
            siem_server = "siem.example.com"
            
            # Create SIEM event
            event = {
                "event_type": "security_threat",
                "severity": self.threat_data.get("threat_severity", "unknown"),
                "source_ip": self.client_ip,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "details": self.threat_data
            }
            
            # Log the SIEM event (in a real system, you would send it)
            siem_file = f"data/responses/siem_event_{self.session_id}.json"
            with open(siem_file, 'w') as f:
                json.dump({
                    "server": siem_server,
                    "event": event
                }, f, indent=2)
                
            self.add_note(f"SIEM event sent to {siem_server}")
            logger.info(f"Sent SIEM event for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error sending to SIEM: {str(e)}")
            logger.error(f"Error sending to SIEM for session {self.session_id}: {str(e)}")
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        data = super().to_dict()
        data["notification_type"] = self.notification_type
        data["recipients"] = self.recipients
        return data


class HoneypotReconfigurationAction(ResponseAction):
    """Action to reconfigure honeypot dynamically"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any], 
                 reconfiguration_type: str = "service_exposure"):
        super().__init__(session_id, client_ip, threat_data)
        self.reconfiguration_type = reconfiguration_type
        self.reconfiguration_data = {}
        
    def execute(self) -> bool:
        """Execute the honeypot reconfiguration action"""
        if self.reconfiguration_type == "service_exposure":
            # Expose additional services
            success = self._expose_services()
        elif self.reconfiguration_type == "vulnerability_exposure":
            # Expose additional vulnerabilities
            success = self._expose_vulnerabilities()
        elif self.reconfiguration_type == "complexity_increase":
            # Increase honeypot complexity
            success = self._increase_complexity()
        elif self.reconfiguration_type == "behavioral_adaptation":
            # Adapt behavior based on attacker actions
            success = self._adapt_behavior()
        else:
            self.add_note(f"Unknown reconfiguration type: {self.reconfiguration_type}")
            return False
            
        self.successful = success
        return success
        
    def _expose_services(self) -> bool:
        """Expose additional services"""
        try:
            # Generate service exposure configuration
            num_services = random.randint(1, 3)
            services = []
            
            service_options = [
                {
                    "protocol": "ssh",
                    "port": 2222,
                    "banner": "SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7"
                },
                {
                    "protocol": "ftp",
                    "port": 2121,
                    "banner": "220 FTP Server Ready"
                },
                {
                    "protocol": "http",
                    "port": 8080,
                    "banner": "Apache/2.4.25 (Debian)"
                },
                {
                    "protocol": "smb",
                    "port": 4445,
                    "banner": "SMB Server"
                },
                {
                    "protocol": "telnet",
                    "port": 2323,
                    "banner": "Debian GNU/Linux 9"
                },
                {
                    "protocol": "mysql",
                    "port": 3307,
                    "banner": "5.5.5-10.1.38-MariaDB-0+deb9u1"
                }
            ]
            
            # Select random services
            selected_services = random.sample(service_options, min(num_services, len(service_options)))
            
            for service in selected_services:
                # Modify port to avoid conflicts
                service["port"] = random.randint(10000, 60000)
                services.append(service)
                
            self.reconfiguration_data = {"services": services}
            self.add_note(f"Exposed {len(services)} additional services")
            
            # In a real system, you would actually start these services
            logger.info(f"Exposed additional services for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error exposing services: {str(e)}")
            logger.error(f"Error exposing services for session {self.session_id}: {str(e)}")
            return False
            
    def _expose_vulnerabilities(self) -> bool:
        """Expose additional vulnerabilities"""
        try:
            # Generate vulnerability exposure configuration
            num_vulns = random.randint(1, 3)
            vulnerabilities = []
            
            vuln_options = [
                {
                    "type": "command_injection",
                    "service": "web",
                    "path": "/cgi-bin/status.cgi",
                    "parameter": "cmd"
                },
                {
                    "type": "sql_injection",
                    "service": "web",
                    "path": "/login.php",
                    "parameter": "username"
                },
                {
                    "type": "path_traversal",
                    "service": "web",
                    "path": "/download.php",
                    "parameter": "file"
                },
                {
                    "type": "default_credentials",
                    "service": "ssh",
                    "username": "admin",
                    "password": "admin123"
                },
                {
                    "type": "default_credentials",
                    "service": "ftp",
                    "username": "anonymous",
                    "password": ""
                },
                {
                    "type": "buffer_overflow",
                    "service": "custom",
                    "port": 9999,
                    "trigger": "OVERFLOW "
                }
            ]
            
            # Select random vulnerabilities
            selected_vulns = random.sample(vuln_options, min(num_vulns, len(vuln_options)))
            
            for vuln in selected_vulns:
                # Modify some details to make them unique
                if "port" in vuln:
                    vuln["port"] = random.randint(10000, 60000)
                if "path" in vuln:
                    paths = ["/admin", "/status", "/api", "/system", "/control"]
                    files = [".php", ".cgi", ".jsp", ".aspx"]
                    vuln["path"] = f"{random.choice(paths)}{random.choice(files)}"
                vulnerabilities.append(vuln)
                
            self.reconfiguration_data = {"vulnerabilities": vulnerabilities}
            self.add_note(f"Exposed {len(vulnerabilities)} additional vulnerabilities")
            
            # In a real system, you would actually implement these vulnerabilities
            logger.info(f"Exposed additional vulnerabilities for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error exposing vulnerabilities: {str(e)}")
            logger.error(f"Error exposing vulnerabilities for session {self.session_id}: {str(e)}")
            return False
            
    def _increase_complexity(self) -> bool:
        """Increase honeypot complexity"""
        try:
            # Generate complexity increase configuration
            complexity_features = []
            
            feature_options = [
                {
                    "type": "filesystem_depth",
                    "depth_increase": random.randint(2, 5)
                },
                {
                    "type": "process_simulation",
                    "num_processes": random.randint(10, 30)
                },
                {
                    "type": "network_topology",
                    "num_virtual_hosts": random.randint(3, 8)
                },
                {
                    "type": "user_accounts",
                    "num_accounts": random.randint(5, 15)
                },
                {
                    "type": "service_interdependencies",
                    "enable": True
                },
                {
                    "type": "delayed_responses",
                    "delay_ms": random.randint(100, 500)
                }
            ]
            
            # Select random features
            num_features = random.randint(2, 5)
            selected_features = random.sample(feature_options, min(num_features, len(feature_options)))
            
            complexity_features.extend(selected_features)
                
            self.reconfiguration_data = {"complexity_features": complexity_features}
            self.add_note(f"Increased honeypot complexity with {len(complexity_features)} features")
            
            # In a real system, you would actually implement these complexity features
            logger.info(f"Increased honeypot complexity for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error increasing complexity: {str(e)}")
            logger.error(f"Error increasing complexity for session {self.session_id}: {str(e)}")
            return False
            
    def _adapt_behavior(self) -> bool:
        """Adapt behavior based on attacker actions"""
        try:
            # Analyze previous commands to determine attacker focus
            attacker_focus = "unknown"
            if "threat_data" in self.threat_data:
                # Look at recent commands
                if "commands" in self.threat_data["threat_data"]:
                    commands = self.threat_data["threat_data"]["commands"]
                    
                    # Simple analysis to determine focus
                    recon_commands = ["ls", "cat", "dir", "find", "whoami", "id", "uname", "systeminfo"]
                    exploit_commands = ["wget", "curl", "nc", "bash", "python", "perl", "chmod"]
                    lateral_commands = ["ssh", "scp", "net", "ping", "telnet"]
                    exfil_commands = ["tar", "zip", "scp", "base64"]
                    
                    command_counts = {
                        "reconnaissance": 0,
                        "exploitation": 0,
                        "lateral_movement": 0,
                        "exfiltration": 0
                    }
                    
                    # Count command types
                    for cmd in commands:
                        cmd_parts = cmd.split()
                        base_cmd = cmd_parts[0] if cmd_parts else ""
                        
                        if base_cmd in recon_commands:
                            command_counts["reconnaissance"] += 1
                        elif base_cmd in exploit_commands:
                            command_counts["exploitation"] += 1
                        elif base_cmd in lateral_commands:
                            command_counts["lateral_movement"] += 1
                        elif base_cmd in exfil_commands:
                            command_counts["exfiltration"] += 1
                            
                    # Determine primary focus
                    if command_counts:
                        attacker_focus = max(command_counts.items(), key=lambda x: x[1])[0]
            
            # Generate behavior adaptations based on focus
            adaptations = []
            
            if attacker_focus == "reconnaissance":
                adaptations.extend([
                    {
                        "type": "filesystem_expansion",
                        "directories": random.randint(5, 15),
                        "files_per_directory": random.randint(3, 10)
                    },
                    {
                        "type": "process_simulation",
                        "processes": random.randint(10, 30)
                    },
                    {
                        "type": "fake_users",
                        "num_users": random.randint(5, 15)
                    }
                ])
            elif attacker_focus == "exploitation":
                adaptations.extend([
                    {
                        "type": "vulnerability_hints",
                        "num_hints": random.randint(2, 5)
                    },
                    {
                        "type": "service_exposure",
                        "num_services": random.randint(1, 3)
                    },
                    {
                        "type": "command_delays",
                        "delay_ms": random.randint(100, 500)
                    }
                ])
            elif attacker_focus == "lateral_movement":
                adaptations.extend([
                    {
                        "type": "network_hosts",
                        "num_hosts": random.randint(3, 8)
                    },
                    {
                        "type": "credential_hints",
                        "num_credentials": random.randint(2, 5)
                    },
                    {
                        "type": "service_banners",
                        "enable": True
                    }
                ])
            elif attacker_focus == "exfiltration":
                adaptations.extend([
                    {
                        "type": "fake_data",
                        "data_types": ["credentials", "configs", "personal_info"]
                    },
                    {
                        "type": "bandwidth_throttling",
                        "throttle_percent": random.randint(30, 70)
                    },
                    {
                        "type": "file_size_increase",
                        "size_multiplier": random.randint(2, 10)
                    }
                ])
            else:
                # Default adaptations
                adaptations.extend([
                    {
                        "type": "command_response_delay",
                        "delay_ms": random.randint(100, 300)
                    },
                    {
                        "type": "filesystem_noise",
                        "enable": True
                    },
                    {
                        "type": "process_noise",
                        "enable": True
                    }
                ])
                
            self.reconfiguration_data = {
                "attacker_focus": attacker_focus,
                "adaptations": adaptations
            }
            
            self.add_note(f"Adapted behavior for {attacker_focus} focus with {len(adaptations)} adaptations")
            
            # In a real system, you would actually implement these adaptations
            logger.info(f"Adapted honeypot behavior for session {self.session_id} (focus: {attacker_focus})")
            return True
        except Exception as e:
            self.add_note(f"Error adapting behavior: {str(e)}")
            logger.error(f"Error adapting behavior for session {self.session_id}: {str(e)}")
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        data = super().to_dict()
        data["reconfiguration_type"] = self.reconfiguration_type
        data["reconfiguration_data"] = self.reconfiguration_data
        return data


class CountermeasureAction(ResponseAction):
    """Action to deploy active countermeasures"""
    
    def __init__(self, session_id: str, client_ip: str, threat_data: Dict[str, Any], 
                 countermeasure_type: str = "tarpitting"):
        super().__init__(session_id, client_ip, threat_data)
        self.countermeasure_type = countermeasure_type
        self.countermeasure_data = {}
        
    def execute(self) -> bool:
        """Execute the countermeasure action"""
        if self.countermeasure_type == "tarpitting":
            # Slow down attacker with tarpit
            success = self._deploy_tarpit()
        elif self.countermeasure_type == "connection_reset":
            # Reset connection
            success = self._reset_connection()
        elif self.countermeasure_type == "resource_exhaustion":
            # Exhaust attacker resources
            success = self._exhaust_resources()
        elif self.countermeasure_type == "fake_errors":
            # Generate fake errors
            success = self._generate_fake_errors()
        else:
            self.add_note(f"Unknown countermeasure type: {self.countermeasure_type}")
            return False
            
        self.successful = success
        return success
        
    def _deploy_tarpit(self) -> bool:
        """Deploy a tarpit to slow down the attacker"""
        try:
            # Generate tarpit configuration
            tarpit_config = {
                "delay_type": random.choice(["fixed", "increasing", "random"]),
                "initial_delay_ms": random.randint(500, 2000),
                "max_delay_ms": random.randint(5000, 15000),
                "increment_ms": random.randint(500, 1000) if random.random() < 0.5 else None,
                "packet_size_bytes": random.randint(1, 10)
            }
            
            self.countermeasure_data = tarpit_config
            self.add_note(f"Deployed tarpit with {tarpit_config['delay_type']} delay")
            
            # In a real system, you would actually implement the tarpit
            logger.info(f"Deployed tarpit for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error deploying tarpit: {str(e)}")
            logger.error(f"Error deploying tarpit for session {self.session_id}: {str(e)}")
            return False
            
    def _reset_connection(self) -> bool:
        """Reset the connection"""
        try:
            # Generate reset configuration
            reset_config = {
                "method": random.choice(["tcp_reset", "application_close", "timeout"]),
                "delay_before_reset_ms": random.randint(0, 5000),
                "reconnect_allowed": random.choice([True, False])
            }
            
            self.countermeasure_data = reset_config
            self.add_note(f"Reset connection using {reset_config['method']}")
            
            # In a real system, you would actually reset the connection
            logger.info(f"Reset connection for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error resetting connection: {str(e)}")
            logger.error(f"Error resetting connection for session {self.session_id}: {str(e)}")
            return False
            
    def _exhaust_resources(self) -> bool:
        """Exhaust attacker resources"""
        try:
            # Generate resource exhaustion configuration
            exhaustion_config = {
                "method": random.choice(["large_responses", "memory_intensive", "cpu_intensive"]),
                "intensity": random.choice(["low", "medium", "high"]),
                "duration_seconds": random.randint(30, 300)
            }
            
            if exhaustion_config["method"] == "large_responses":
                exhaustion_config["response_size_kb"] = random.randint(1000, 10000)
            elif exhaustion_config["method"] == "memory_intensive":
                exhaustion_config["memory_pattern"] = random.choice(["random", "incremental", "fragmented"])
            elif exhaustion_config["method"] == "cpu_intensive":
                exhaustion_config["cpu_pattern"] = random.choice(["calculation", "compression", "encryption"])
                
            self.countermeasure_data = exhaustion_config
            self.add_note(f"Deployed {exhaustion_config['method']} resource exhaustion at {exhaustion_config['intensity']} intensity")
            
            # In a real system, you would actually implement resource exhaustion
            logger.info(f"Deployed resource exhaustion for session {self.session_id}")
            return True
        except Exception as e:
            self.add_note(f"Error deploying resource exhaustion: {str(e)}")
            logger.error(f"Error deploying resource exhaustion for session {self.session_id}: {str(e)}")
            return False
            
    def _generate_fake_errors(self) -> bool:
        """Generate fake errors to confuse the attacker"""
        try:
            # Generate fake error configuration
            error_config = {
                "error_types": random.sample(["permission", "not_found", "timeout", "server", "syntax"], 
                                           random.randint(1, 5)),
                "frequency": random.choice(["low", "medium", "high"]),
                "pattern": random.choice(["random", "escalating", "alternating"]),
                "recoverable": random.choice([True, False])
            }
            
            # Generate specific errors
            errors = []
            
            if "permission" in error_config["error_types"]:
                errors.append({
                    "type": "permission",
                    "message": random.choice([
                        "Permission denied",
                        "Access forbidden",
                        "Operation not permitted",
                        "Insufficient privileges"
                    ])
                })
                
            if "not_found" in error_config["error_types"]:
                errors.append({
                    "type": "not_found",
                    "message": random.choice([
                        "File not found",
                        "No such file or directory",
                        "Resource unavailable",
                        "Path does not exist"
                    ])
                })
                
            if "timeout" in error_config["error_types"]:
                errors.append({
                    "type": "timeout",
                    "message": random.choice([
                        "Operation timed out",
                        "Connection timed out",
                        "Request timed out",
                        "Response timeout"
                    ])
                })
                
            if "server" in error_config["error_types"]:
                errors.append({
                    "type": "server",
                    "message": random.choice([
                        "Internal server error",
                        "Service unavailable",
                        "Server overloaded",
                        "Resource limits exceeded"
                    ])
                })
                
            if "syntax" in error_config["error_types"]:
                errors.append({
                    "type": "syntax",
                    "message": random.choice([
                        "Syntax error",
                        "Invalid command",
                        "Unrecognized parameter",
                        "Malformed request"
                    ])
                })
                
            error_config["errors"] = errors
            self.countermeasure_data = error_config
            self.add_note(f"Deployed fake errors with {error_config['frequency']} frequency and {error_config['pattern']} pattern")
            
            # In a real system, you would actually implement error injection
            return True
            
        except Exception as e:
            logger.error(f"Error deploying fake errors: {str(e)}")
            return False

class AutomatedResponseSystem:
    """Main automated response system coordinator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.response_actions = {
            "containment": ContainmentAction,
            "deception": DeceptionAction,
            "evidence": EvidenceCollectionAction,
            "notification": NotificationAction,
            "reconfiguration": HoneypotReconfigurationAction,
            "countermeasure": CountermeasureAction
        }
        self.threat_thresholds = {
            1: ["notification"],  # Low
            2: ["notification", "evidence"],  # Medium
            3: ["notification", "evidence", "deception"],  # High
            4: ["containment", "notification", "evidence", "deception", "countermeasure"]  # Critical
        }
        self.active_responses = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "auto_response": True,
            "response_delay": 5,  # seconds
            "max_concurrent_responses": 10,
            "escalation_enabled": True,
            "notification_targets": ["admin@example.com"]
        }
    
    def process_threat(self, threat_data: Dict[str, Any]) -> bool:
        """Process a threat and execute appropriate responses"""
        try:
            threat_level = threat_data.get("threat_level", 1)
            session_id = threat_data.get("session_id", "unknown")
            client_ip = threat_data.get("client_ip", "unknown")
            
            logger.info(f"Processing threat from {client_ip}: Level {threat_level}")
            
            # Get appropriate response actions for this threat level
            response_types = self.threat_thresholds.get(threat_level, ["notification"])
            
            # Execute each response action
            responses_executed = []
            for response_type in response_types:
                if response_type in self.response_actions:
                    action_class = self.response_actions[response_type]
                    action = action_class(threat_data, self.config)
                    
                    if action.execute():
                        responses_executed.append(response_type)
                        logger.info(f"Executed {response_type} response for {session_id}")
                    else:
                        logger.error(f"Failed to execute {response_type} response for {session_id}")
            
            # Store active response info
            self.active_responses[session_id] = {
                "threat_data": threat_data,
                "responses": responses_executed,
                "timestamp": datetime.now().isoformat()
            }
            
            return len(responses_executed) > 0
            
        except Exception as e:
            logger.error(f"Error processing threat: {str(e)}")
            return False
    
    def get_active_responses(self) -> Dict[str, Any]:
        """Get currently active responses"""
        return self.active_responses
    
    def stop_response(self, session_id: str) -> bool:
        """Stop active responses for a session"""
        if session_id in self.active_responses:
            del self.active_responses[session_id]
            logger.info(f"Stopped responses for session {session_id}")
            return True
        return False
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get statistics about response system"""
        total_responses = len(self.active_responses)
        response_types = {}
        
        for response_info in self.active_responses.values():
            for response_type in response_info.get("responses", []):
                response_types[response_type] = response_types.get(response_type, 0) + 1
        
        return {
            "total_active_responses": total_responses,
            "response_type_counts": response_types,
            "system_enabled": self.config.get("enabled", True)
        }

# Main execution for testing
if __name__ == "__main__":
    # Initialize response system
    response_system = AutomatedResponseSystem()
    
    # Test threat escalation
    sample_threat = {
        "session_id": "test_session",
        "client_ip": "192.168.1.100",
        "threat_level": 3,
        "threat_type": "reconnaissance",
        "confidence": 0.85,
        "command_sequence": ["ls", "whoami", "cat /etc/passwd"]
    }
    
    print("Testing NEXDIS Automated Response System...")
    print(f"Processing threat: {sample_threat['threat_type']} (Level: {sample_threat['threat_level']})")
    
    # Process the threat
    response_system.process_threat(sample_threat)
    
    print("Automated response system test completed.")