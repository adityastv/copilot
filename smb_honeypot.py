import socket
import threading
import struct
import os
import time
import json
import logging
from datetime import datetime
import uuid
import random

# Import database and logging from main module
# In a real implementation, these would be properly imported
# For demonstration purposes, we'll redefine minimal versions
class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        
    def add_connection(self, data):
        print(f"[DB] New SMB connection: {data}")
        
    def add_smb_command(self, data):
        print(f"[DB] SMB command: {data}")
        
    def start_session(self, session_id, client_ip, protocol, username=None):
        print(f"[DB] Started session {session_id} for {client_ip} using {protocol}")
        
    def end_session(self, session_id):
        print(f"[DB] Ended session {session_id}")

class LogManager:
    def __init__(self):
        self.logger = logging.getLogger('SMBHoneypot')
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
        
    def log_smb_command(self, client_ip, session_id, command, details, response):
        data = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'session_id': session_id,
            'command': command,
            'details': details,
            'response': response
        }
        self.logger.info(f"SMB Command: {json.dumps(data)}")
        return data

# Load configuration
def load_config(config_file='config.json'):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {
        "smb": {
            "enabled": True,
            "port": 445,
            "interface": "0.0.0.0",
            "hostname": "FILESERVER",
            "domain": "WORKGROUP"
        }
    }

# SMB Protocol Constants
class SMBConstants:
    # SMB Commands
    SMB_COM_NEGOTIATE = 0x72
    SMB_COM_SESSION_SETUP_ANDX = 0x73
    SMB_COM_TREE_CONNECT_ANDX = 0x75
    SMB_COM_TRANSACTION = 0x25
    SMB_COM_TRANSACTION2 = 0x32
    SMB_COM_NT_TRANSACT = 0xA0
    SMB_COM_NT_CREATE_ANDX = 0xA2
    SMB_COM_READ_ANDX = 0x2E
    SMB_COM_WRITE_ANDX = 0x2F
    SMB_COM_CLOSE = 0x04
    SMB_COM_TREE_DISCONNECT = 0x71
    SMB_COM_LOGOFF_ANDX = 0x74
    
    # SMB Flags
    SMB_FLAGS_CASE_INSENSITIVE = 0x08
    SMB_FLAGS_CANONICALIZED_PATHS = 0x10
    SMB_FLAGS_REPLY = 0x80
    
    # SMB Flags2
    SMB_FLAGS2_LONG_NAMES = 0x0001
    SMB_FLAGS2_EAS = 0x0002
    SMB_FLAGS2_SMB_SECURITY_SIGNATURE = 0x0004
    SMB_FLAGS2_KNOWS_LONG_NAMES = 0x0040
    SMB_FLAGS2_IS_LONG_NAME = 0x0040
    SMB_FLAGS2_UNICODE = 0x8000
    
    # Status Codes
    STATUS_SUCCESS = 0x00000000
    STATUS_ACCESS_DENIED = 0xC0000022
    STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
    STATUS_LOGON_FAILURE = 0xC000006D

# SMB Session Handler
class SMBSession:
    def __init__(self, client_socket, client_address, config, db_manager, log_manager):
        self.socket = client_socket
        self.client_ip = client_address[0]
        self.client_port = client_address[1]
        self.config = config
        self.db_manager = db_manager
        self.log_manager = log_manager
        
        self.session_id = str(uuid.uuid4())
        self.tree_id = random.randint(1, 65535)
        self.user_id = random.randint(1, 65535)
        self.process_id = 0
        self.multiplex_id = 0
        self.authenticated = False
        self.negotiated = False
        self.hostname = config.get('hostname', 'FILESERVER')
        self.domain = config.get('domain', 'WORKGROUP')
        
        # Log connection
        connection_data = self.log_manager.log_connection(
            self.client_ip,
            self.client_port,
            'smb',
            success=True
        )
        self.db_manager.add_connection(connection_data)
        
        # Start session
        self.db_manager.start_session(self.session_id, self.client_ip, 'smb')
        
    def start(self):
        """Start handling SMB requests"""
        try:
            while True:
                # Read NetBIOS header (4 bytes)
                netbios_header = self.socket.recv(4)
                if not netbios_header or len(netbios_header) < 4:
                    break
                    
                # Parse NetBIOS header
                if netbios_header[0] != 0x00:
                    continue  # Not a session message
                    
                # Get packet length from NetBIOS header
                packet_length = (netbios_header[1] << 16) | (netbios_header[2] << 8) | netbios_header[3]
                
                # Read SMB packet
                smb_data = self.socket.recv(packet_length)
                if not smb_data or len(smb_data) < 32:  # Minimum SMB header size
                    break
                    
                # Process SMB packet
                self.process_smb_packet(smb_data)
        except Exception as e:
            print(f"Error in SMB session: {str(e)}")
        finally:
            self.close()
            
    def close(self):
        """Close the SMB session"""
        try:
            self.socket.close()
        except:
            pass
            
        # End session
        self.db_manager.end_session(self.session_id)
        
    def process_smb_packet(self, data):
        """Process SMB packet"""
        # Check SMB header
        if data[0:4] != b'\xff\x53\x4d\x42':  # SMB signature '\xffSMB'
            return
            
        # Extract command code
        command = data[4]
        
        # Extract flags
        flags = data[9]
        flags2 = struct.unpack("<H", data[10:12])[0]
        
        # Extract process ID, user ID, and multiplex ID
        self.process_id = struct.unpack("<H", data[24:26])[0]
        self.multiplex_id = struct.unpack("<H", data[30:32])[0]
        
        # If this is a response (should not happen in a honeypot), ignore it
        if flags & SMBConstants.SMB_FLAGS_REPLY:
            return
            
        # Process command
        response = None
        command_name = "UNKNOWN"
        details = {}
        
        if command == SMBConstants.SMB_COM_NEGOTIATE:
            command_name = "SMB_COM_NEGOTIATE"
            response = self.handle_negotiate(data)
            details = {"negotiation": "SMBv1"}
        elif command == SMBConstants.SMB_COM_SESSION_SETUP_ANDX:
            command_name = "SMB_COM_SESSION_SETUP_ANDX"
            response, auth_details = self.handle_session_setup(data)
            details = auth_details
        elif command == SMBConstants.SMB_COM_TREE_CONNECT_ANDX:
            command_name = "SMB_COM_TREE_CONNECT_ANDX"
            response, tree_details = self.handle_tree_connect(data)
            details = tree_details
        elif command == SMBConstants.SMB_COM_NT_CREATE_ANDX:
            command_name = "SMB_COM_NT_CREATE_ANDX"
            response, file_details = self.handle_nt_create(data)
            details = file_details
        elif command == SMBConstants.SMB_COM_READ_ANDX:
            command_name = "SMB_COM_READ_ANDX"
            response = self.handle_read(data)
            details = {"action": "read_file"}
        elif command == SMBConstants.SMB_COM_WRITE_ANDX:
            command_name = "SMB_COM_WRITE_ANDX"
            response = self.handle_write(data)
            details = {"action": "write_file"}
        elif command == SMBConstants.SMB_COM_CLOSE:
            command_name = "SMB_COM_CLOSE"
            response = self.handle_close(data)
            details = {"action": "close_file"}
        elif command == SMBConstants.SMB_COM_TREE_DISCONNECT:
            command_name = "SMB_COM_TREE_DISCONNECT"
            response = self.handle_tree_disconnect(data)
            details = {"action": "disconnect_tree"}
        elif command == SMBConstants.SMB_COM_LOGOFF_ANDX:
            command_name = "SMB_COM_LOGOFF_ANDX"
            response = self.handle_logoff(data)
            details = {"action": "logoff"}
        elif command in (SMBConstants.SMB_COM_TRANSACTION, SMBConstants.SMB_COM_TRANSACTION2, SMBConstants.SMB_COM_NT_TRANSACT):
            command_name = "SMB_COM_TRANSACTION"
            response = self.handle_transaction(data, command)
            details = {"action": "transaction"}
        else:
            # Generic response for unsupported commands
            response = self.create_error_response(data, SMBConstants.STATUS_SUCCESS)
            
        # Log the command
        if response:
            # Send response
            self.send_response(response)
            
            # Log command
            log_data = self.log_manager.log_smb_command(
                self.client_ip,
                self.session_id,
                command_name,
                details,
                "Response sent"
            )
            self.db_manager.add_smb_command(log_data)
            
    def send_response(self, data):
        """Send SMB response"""
        # Calculate NetBIOS header
        length = len(data)
        netbios_header = struct.pack(">BBH", 0x00, (length >> 16) & 0xFF, length & 0xFFFF)
        
        # Send packet
        try:
            self.socket.sendall(netbios_header + data)
        except Exception as e:
            print(f"Error sending SMB response: {str(e)}")
            
    def handle_negotiate(self, data):
        """Handle SMB_COM_NEGOTIATE request"""
        self.negotiated = True
        
        # Create response header
        response = bytearray(b'\xff\x53\x4d\x42')  # SMB signature
        response.append(SMBConstants.SMB_COM_NEGOTIATE)  # Command
        response.extend(b'\x00\x00\x00\x00')  # Status (success)
        response.append(SMBConstants.SMB_FLAGS_CASE_INSENSITIVE | SMBConstants.SMB_FLAGS_REPLY)  # Flags
        response.extend(struct.pack("<H", SMBConstants.SMB_FLAGS2_UNICODE | SMBConstants.SMB_FLAGS2_LONG_NAMES))  # Flags2
        response.extend(b'\x00\x00')  # PID High
        response.extend(b'\x00\x00\x00\x00\x00\x00\x00\x00')  # Signature
        response.extend(b'\x00\x00')  # Reserved
        response.extend(struct.pack("<H", self.tree_id))  # Tree ID
        response.extend(struct.pack("<H", self.process_id))  # PID
        response.extend(struct.pack("<H", self.user_id))  # UID
        response.extend(struct.pack("<H", self.multiplex_id))  # Multiplex ID
        
        # Response parameters
        dialect_index = 5  # Assuming NT LM 0.12 dialect (most common for SMBv1)
        security_mode = 3  # User level, encrypted passwords
        max_mpx_count = 50
        max_vcs = 1
        max_buffer_size = 16644
        max_raw_size = 65536
        session_key = random.randint(1, 65535)
        capabilities = 0x8000F3FD  # Extended security, large files, NT SMBs, etc.
        system_time = datetime.now().strftime("%Y%m%d%H%M%S")
        server_timezone = 0
        challenge_length = 8
        
        # Add parameters to response
        response.extend(struct.pack("<H", 17))  # Word count
        response.extend(struct.pack("<H", dialect_index))
        response.append(security_mode)
        response.extend(struct.pack("<H", max_mpx_count))
        response.extend(struct.pack("<H", max_vcs))
        response.extend(struct.pack("<I", max_buffer_size))
        response.extend(struct.pack("<I", max_raw_size))
        response.extend(struct.pack("<I", session_key))
        response.extend(struct.pack("<I", capabilities))
        response.extend(b'\x01\x02\x03\x04\x05\x06\x07\x08')  # System time (placeholder)
        response.extend(struct.pack("<H", server_timezone))
        response.append(challenge_length)
        
        # Byte count and data
        guid = uuid.uuid4().bytes
        challenge = os.urandom(8)
        domain_name = self.domain.encode('utf-16-le')
        
        # Add data to response
        response.extend(struct.pack("<H", len(challenge) + len(domain_name) + len(guid) + 2))  # Byte count
        response.extend(challenge)  # Challenge
        response.extend(domain_name)  # Domain name (Unicode)
        response.extend(b'\x00\x00')  # Null terminator
        response.extend(guid)  # Server GUID
        
        return bytes(response)
        
    def handle_session_setup(self, data):
        """Handle SMB_COM_SESSION_SETUP_ANDX request"""
        # In a real scenario, we would extract and validate credentials
        # For the honeypot, we'll accept the login attempt and generate user ID
        
        # Extract username and domain if available (simplified)
        offset = 36  # Skip to parameter words
        word_count = data[offset]
        offset += 1 + (word_count * 2)  # Skip parameter words
        
        byte_count = struct.unpack("<H", data[offset:offset+2])[0]
        offset += 2
        
        # Attempt to extract credentials (very simplified)
        # In a real implementation, you would parse NTLMSSP or other auth mechanisms
        auth_data = data[offset:offset+byte_count]
        username = "unknown"
        password = "unknown"
        domain = "unknown"
        
        # Try to extract username from auth data
        try:
            # Very naive extraction - in real SMB this would be much more complex
            auth_str = auth_data.decode('utf-16-le', errors='ignore')
            parts = auth_str.split('\x00')
            if len(parts) >