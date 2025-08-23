#!/usr/bin/env python3
"""
NEXDIS - AI-Driven Cybersecurity Deception Platform
Main orchestrator and launcher for the NEXDIS platform.
"""

import os
import sys
import json
import time
import signal
import threading
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import NEXDIS modules
from ssh_honeypot_server import main as ssh_main, SSH_BANNER, VERSION
from http_honeypot import HTTPHoneypot
from ftp_honeypot import FTPHoneypot
from threat_dashboard import ThreatDashboard
from threat_classification import ThreatClassifier
from automated_response import AutomatedResponseSystem
from honeypot_integration import patch_ssh_honeypot
import ai_personas

# NEXDIS Platform Information
NEXDIS_VERSION = "1.0.0"
NEXDIS_BANNER = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ███╗   ██╗███████╗██╗  ██╗██████╗ ██╗███████╗            ║
║    ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██║██╔════╝            ║
║    ██╔██╗ ██║█████╗   ╚███╔╝ ██║  ██║██║███████╗            ║
║    ██║╚██╗██║██╔══╝   ██╔██╗ ██║  ██║██║╚════██║            ║
║    ██║ ╚████║███████╗██╔╝ ██╗██████╔╝██║███████║            ║
║    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝╚══════╝            ║
║                                                              ║
║          AI-Driven Cybersecurity Deception Platform         ║
║                        Version {NEXDIS_VERSION}                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

class NEXDISPlatform:
    """Main NEXDIS platform orchestrator"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.services = {}
        self.threads = {}
        self.running = False
        self.setup_logging()
        self.setup_directories()
        
        # Initialize core components
        self.threat_classifier = ThreatClassifier()
        self.response_system = AutomatedResponseSystem()
        self.dashboard = ThreatDashboard()
        
    def load_config(self) -> Dict[str, Any]:
        """Load platform configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "nexdis": {
                "version": NEXDIS_VERSION,
                "mode": "standalone",
                "auto_start": ["ssh", "http", "dashboard"]
            },
            "ssh": {
                "enabled": True,
                "port": 2223,
                "interface": "0.0.0.0",
                "banner": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1",
                "key_file": "server.key"
            },
            "http": {
                "enabled": True,
                "http_port": 8080,
                "https_port": 8443,
                "interface": "0.0.0.0"
            },
            "ftp": {
                "enabled": False,
                "port": 2121,
                "interface": "0.0.0.0"
            },
            "smb": {
                "enabled": False,
                "port": 445,
                "interface": "0.0.0.0"
            },
            "dashboard": {
                "enabled": True,
                "port": 9090,
                "interface": "0.0.0.0"
            },
            "threat_intelligence": {
                "enabled": True,
                "update_interval": 3600,
                "sources": ["demo"]
            },
            "automated_response": {
                "enabled": True,
                "sensitivity": "medium",
                "auto_deploy_deception": True
            },
            "logging": {
                "level": "INFO",
                "max_size": 10485760,
                "backup_count": 10
            },
            "database": {
                "type": "sqlite",
                "file": "nexdis.db"
            },
            "api": {
                "enabled": True,
                "port": 8888,
                "auth_required": False
            }
        }
    
    def setup_logging(self):
        """Setup platform logging"""
        log_level = getattr(logging, self.config.get("logging", {}).get("level", "INFO"))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/nexdis.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("NEXDIS")
        self.logger.info(f"NEXDIS Platform v{NEXDIS_VERSION} initialized")
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            "logs", "logs/threats", "data", "data/threat_intel",
            "models", "plugins", "keys", "uploads", "backups"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        try:
            if service_name == "ssh" and self.config.get("ssh", {}).get("enabled", False):
                self.logger.info("Starting SSH honeypot service...")
                ssh_thread = threading.Thread(
                    target=self._run_ssh_honeypot,
                    daemon=True,
                    name="SSH-Honeypot"
                )
                ssh_thread.start()
                self.threads["ssh"] = ssh_thread
                self.services["ssh"] = "running"
                
            elif service_name == "http" and self.config.get("http", {}).get("enabled", False):
                self.logger.info("Starting HTTP honeypot service...")
                http_honeypot = HTTPHoneypot(config=self.config)
                http_thread = threading.Thread(
                    target=http_honeypot.start,
                    daemon=True,
                    name="HTTP-Honeypot"
                )
                http_thread.start()
                self.threads["http"] = http_thread
                self.services["http"] = "running"
                
            elif service_name == "ftp" and self.config.get("ftp", {}).get("enabled", False):
                self.logger.info("Starting FTP honeypot service...")
                ftp_honeypot = FTPHoneypot(config=self.config)
                ftp_thread = threading.Thread(
                    target=ftp_honeypot.start,
                    daemon=True,
                    name="FTP-Honeypot"
                )
                ftp_thread.start()
                self.threads["ftp"] = ftp_thread
                self.services["ftp"] = "running"
                
            elif service_name == "dashboard" and self.config.get("dashboard", {}).get("enabled", False):
                self.logger.info("Starting threat dashboard...")
                dashboard_thread = threading.Thread(
                    target=self.dashboard.start,
                    daemon=True,
                    name="Threat-Dashboard"
                )
                dashboard_thread.start()
                self.threads["dashboard"] = dashboard_thread
                self.services["dashboard"] = "running"
                
            elif service_name == "api" and self.config.get("api", {}).get("enabled", False):
                self.logger.info("Starting API service...")
                api_thread = threading.Thread(
                    target=self._run_api_server,
                    daemon=True,
                    name="API-Server"
                )
                api_thread.start()
                self.threads["api"] = api_thread
                self.services["api"] = "running"
                
            else:
                self.logger.warning(f"Service '{service_name}' is disabled or unknown")
                return False
                
            self.logger.info(f"Service '{service_name}' started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service '{service_name}': {str(e)}")
            return False
    
    def _run_ssh_honeypot(self):
        """Run SSH honeypot in thread"""
        try:
            # Monkey patch SSH honeypot for integration
            patch_ssh_honeypot()
            ssh_main()
        except Exception as e:
            self.logger.error(f"SSH honeypot error: {str(e)}")
    
    def _run_api_server(self):
        """Run API server"""
        from flask import Flask, jsonify, request
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        @app.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({
                "platform": "NEXDIS",
                "version": NEXDIS_VERSION,
                "status": "running" if self.running else "stopped",
                "services": self.services,
                "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
            })
        
        @app.route('/api/threats', methods=['GET'])
        def get_threats():
            # Get recent threats from classifier
            return jsonify({
                "threats": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route('/api/honeypots', methods=['GET', 'POST'])
        def manage_honeypots():
            if request.method == 'GET':
                return jsonify({"honeypots": list(self.services.keys())})
            else:
                # Deploy new honeypot
                config = request.get_json()
                return jsonify({"status": "deployed", "config": config})
        
        @app.route('/api/config', methods=['GET', 'PUT'])
        def manage_config():
            if request.method == 'GET':
                return jsonify(self.config)
            else:
                # Update configuration
                new_config = request.get_json()
                self.config.update(new_config)
                return jsonify({"status": "updated"})
        
        api_port = self.config.get("api", {}).get("port", 8888)
        app.run(host="0.0.0.0", port=api_port, debug=False)
    
    def start_all(self):
        """Start all configured services"""
        print(NEXDIS_BANNER)
        self.logger.info("Starting NEXDIS platform...")
        
        self.running = True
        self.start_time = time.time()
        
        # Start auto-start services
        auto_start = self.config.get("nexdis", {}).get("auto_start", [])
        for service in auto_start:
            self.start_service(service)
        
        # Start threat intelligence processing
        if self.config.get("threat_intelligence", {}).get("enabled", False):
            self.logger.info("Starting threat intelligence engine...")
        
        # Start automated response system
        if self.config.get("automated_response", {}).get("enabled", False):
            self.logger.info("Starting automated response system...")
        
        self.logger.info("NEXDIS platform startup complete")
        print("\n🛡️  NEXDIS Platform is running!")
        print(f"📊 Dashboard: http://localhost:{self.config.get('dashboard', {}).get('port', 9090)}")
        print(f"🔌 API: http://localhost:{self.config.get('api', {}).get('port', 8888)}/api/status")
        print("📋 Services running:")
        
        for service, status in self.services.items():
            print(f"   • {service.upper()}: {status}")
        
        print("\n⏹️  Press Ctrl+C to stop all services")
    
    def stop_all(self):
        """Stop all services"""
        self.logger.info("Stopping NEXDIS platform...")
        self.running = False
        
        # Stop dashboard
        if hasattr(self, 'dashboard'):
            self.dashboard.stop()
        
        # Services will stop when main thread exits due to daemon=True
        self.logger.info("NEXDIS platform stopped")
        print("\n🛑 NEXDIS platform stopped successfully")
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "NEXDIS",
            "version": NEXDIS_VERSION,
            "description": "AI-Driven Cybersecurity Deception Platform",
            "services": self.services,
            "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0,
            "config_file": self.config_file
        }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Received shutdown signal...")
    if 'nexdis' in globals():
        nexdis.stop_all()
    sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NEXDIS - AI-Driven Cybersecurity Deception Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nexdis.py --start-all              Start all services
  python nexdis.py --service ssh            Start SSH honeypot only
  python nexdis.py --service dashboard      Start dashboard only
  python nexdis.py --config config.json     Use custom config file
  python nexdis.py --init                   Initialize platform
  python nexdis.py --status                 Show platform status
        """
    )
    
    parser.add_argument('--version', action='version', version=f'NEXDIS {NEXDIS_VERSION}')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--start-all', action='store_true', help='Start all configured services')
    parser.add_argument('--service', help='Start a specific service (ssh, http, ftp, dashboard, api)')
    parser.add_argument('--init', action='store_true', help='Initialize NEXDIS platform')
    parser.add_argument('--status', action='store_true', help='Show platform status')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize platform
    global nexdis
    nexdis = NEXDISPlatform(args.config)
    
    if args.init:
        print("🚀 Initializing NEXDIS platform...")
        nexdis.setup_directories()
        
        # Create default config if it doesn't exist
        if not os.path.exists(args.config):
            with open(args.config, 'w') as f:
                json.dump(nexdis.get_default_config(), f, indent=4)
            print(f"📋 Created default configuration: {args.config}")
        
        print("✅ NEXDIS platform initialized successfully!")
        print(f"📝 Edit {args.config} to customize your configuration")
        print("🚀 Run 'python nexdis.py --start-all' to start all services")
        return
    
    if args.status:
        info = nexdis.get_platform_info()
        print(f"\n📊 NEXDIS Platform Status")
        print(f"Version: {info['version']}")
        print(f"Config: {info['config_file']}")
        print(f"Services: {len(info['services'])}")
        for service, status in info['services'].items():
            print(f"  • {service}: {status}")
        return
    
    if args.service:
        nexdis.start_service(args.service)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return
    
    if args.start_all:
        nexdis.start_all()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            nexdis.stop_all()
        return
    
    # Default behavior - show help
    parser.print_help()

if __name__ == "__main__":
    main()