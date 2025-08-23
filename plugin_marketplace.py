"""
NEXDIS Plugin Marketplace
Extensible plugin system for custom honeypots, deception techniques, and integrations.
"""

import os
import json
import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

logger = logging.getLogger("PluginMarketplace")

@dataclass
class PluginInfo:
    """Plugin metadata and information"""
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    requires: List[str] = None
    min_nexdis_version: str = "1.0.0"
    config_schema: Dict[str, Any] = None
    install_date: str = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.requires is None:
            self.requires = []
        if self.config_schema is None:
            self.config_schema = {}
        if self.install_date is None:
            self.install_date = datetime.now().isoformat()

class PluginBase(ABC):
    """Base class for all NEXDIS plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = True
        self.logger = logging.getLogger(f"Plugin.{self.__class__.__name__}")
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Return plugin information"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """Start the plugin"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the plugin"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        return {
            "enabled": self.enabled,
            "initialized": hasattr(self, '_initialized'),
            "running": hasattr(self, '_running')
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        return True

class HoneypotPlugin(PluginBase):
    """Base class for honeypot plugins"""
    
    @abstractmethod
    def get_honeypot_type(self) -> str:
        """Return the honeypot type (e.g., 'ssh', 'http', 'custom')"""
        pass
    
    @abstractmethod
    def handle_connection(self, client_data: Dict[str, Any]) -> bool:
        """Handle incoming connection"""
        pass
    
    @abstractmethod
    def get_fake_responses(self) -> Dict[str, Any]:
        """Get fake responses for various inputs"""
        pass

class DeceptionPlugin(PluginBase):
    """Base class for deception technique plugins"""
    
    @abstractmethod
    def deploy_deception(self, context: Dict[str, Any]) -> bool:
        """Deploy deception technique"""
        pass
    
    @abstractmethod
    def get_deception_data(self) -> Dict[str, Any]:
        """Get current deception data"""
        pass

class IntegrationPlugin(PluginBase):
    """Base class for external integration plugins"""
    
    @abstractmethod
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to external system"""
        pass
    
    @abstractmethod
    def get_threat_intel(self) -> Dict[str, Any]:
        """Get threat intelligence from external source"""
        pass

class PluginRegistry:
    """Registry for managing plugins"""
    
    def __init__(self, plugin_directory: str = "plugins"):
        self.plugin_directory = plugin_directory
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.categories = ["honeypot", "deception", "integration", "analysis", "response"]
        
        # Ensure plugin directory exists
        os.makedirs(plugin_directory, exist_ok=True)
        os.makedirs(f"{plugin_directory}/installed", exist_ok=True)
        os.makedirs(f"{plugin_directory}/available", exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        plugins = []
        
        for filename in os.listdir(f"{self.plugin_directory}/installed"):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_name = filename[:-3]  # Remove .py extension
                plugins.append(plugin_name)
        
        return plugins
    
    def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """Load a plugin"""
        try:
            # Import the plugin module
            plugin_path = f"{self.plugin_directory}.installed.{plugin_name}"
            plugin_module = importlib.import_module(plugin_path)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(plugin_module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error(f"No valid plugin class found in {plugin_name}")
                return False
            
            # Instantiate plugin
            plugin_instance = plugin_class(config)
            
            # Get plugin info
            plugin_info = plugin_instance.get_info()
            
            # Validate requirements
            if not self._check_requirements(plugin_info):
                logger.error(f"Plugin {plugin_name} requirements not met")
                return False
            
            # Initialize plugin
            if plugin_instance.initialize():
                self.plugins[plugin_name] = plugin_instance
                self.plugin_info[plugin_name] = plugin_info
                logger.info(f"Loaded plugin: {plugin_name} v{plugin_info.version}")
                return True
            else:
                logger.error(f"Failed to initialize plugin: {plugin_name}")
                return False
        
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].stop()
                del self.plugins[plugin_name]
                del self.plugin_info[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")
                return True
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {str(e)}")
                return False
        return False
    
    def start_plugin(self, plugin_name: str) -> bool:
        """Start a plugin"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].start()
        return False
    
    def stop_plugin(self, plugin_name: str) -> bool:
        """Stop a plugin"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].stop()
        return False
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a plugin"""
        return self.plugin_info.get(plugin_name)
    
    def list_plugins(self, category: str = None) -> List[Dict[str, Any]]:
        """List all plugins, optionally filtered by category"""
        plugins = []
        
        for name, info in self.plugin_info.items():
            if category is None or info.category == category:
                plugin_data = asdict(info)
                plugin_data['status'] = self.plugins[name].get_status()
                plugins.append(plugin_data)
        
        return plugins
    
    def install_plugin(self, plugin_data: bytes, plugin_name: str) -> bool:
        """Install a new plugin"""
        try:
            plugin_path = f"{self.plugin_directory}/installed/{plugin_name}.py"
            
            # Verify plugin integrity (basic check)
            plugin_hash = hashlib.sha256(plugin_data).hexdigest()
            
            # Write plugin file
            with open(plugin_path, 'wb') as f:
                f.write(plugin_data)
            
            # Try to load it to verify it's valid
            if self.load_plugin(plugin_name):
                logger.info(f"Installed plugin: {plugin_name} (hash: {plugin_hash[:8]})")
                return True
            else:
                # Remove invalid plugin
                os.remove(plugin_path)
                return False
        
        except Exception as e:
            logger.error(f"Error installing plugin {plugin_name}: {str(e)}")
            return False
    
    def _check_requirements(self, plugin_info: PluginInfo) -> bool:
        """Check if plugin requirements are met"""
        for requirement in plugin_info.requires:
            try:
                importlib.import_module(requirement)
            except ImportError:
                logger.error(f"Missing requirement: {requirement}")
                return False
        return True

# Built-in sample plugins

class SampleWebHoneypot(HoneypotPlugin):
    """Sample web honeypot plugin"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Sample Web Honeypot",
            version="1.0.0",
            description="A simple web honeypot that mimics a vulnerable web application",
            author="NEXDIS Team",
            category="honeypot",
            tags=["web", "http", "sample"],
            requires=["flask"]
        )
    
    def initialize(self) -> bool:
        self.logger.info("Initializing sample web honeypot")
        self._initialized = True
        return True
    
    def start(self) -> bool:
        self.logger.info("Starting sample web honeypot")
        self._running = True
        return True
    
    def stop(self) -> bool:
        self.logger.info("Stopping sample web honeypot")
        self._running = False
        return True
    
    def get_honeypot_type(self) -> str:
        return "web"
    
    def handle_connection(self, client_data: Dict[str, Any]) -> bool:
        self.logger.info(f"Handling web connection from {client_data.get('ip', 'unknown')}")
        return True
    
    def get_fake_responses(self) -> Dict[str, Any]:
        return {
            "login_page": "<html><body><h1>Admin Login</h1><form>...</form></body></html>",
            "error_pages": {
                "404": "Not Found",
                "500": "Internal Server Error"
            }
        }

class SlackIntegrationPlugin(IntegrationPlugin):
    """Slack integration plugin for alerts"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Slack Integration",
            version="1.0.0",
            description="Send threat alerts to Slack channels",
            author="NEXDIS Team",
            category="integration",
            tags=["slack", "alerts", "notifications"],
            requires=["requests"],
            config_schema={
                "webhook_url": {"type": "string", "required": True},
                "channel": {"type": "string", "default": "#security"},
                "username": {"type": "string", "default": "NEXDIS"}
            }
        )
    
    def initialize(self) -> bool:
        if not self.config.get("webhook_url"):
            logger.error("Slack webhook URL not configured")
            return False
        self._initialized = True
        return True
    
    def start(self) -> bool:
        self._running = True
        return True
    
    def stop(self) -> bool:
        self._running = False
        return True
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        import requests
        
        try:
            payload = {
                "channel": self.config.get("channel", "#security"),
                "username": self.config.get("username", "NEXDIS"),
                "text": f"🚨 NEXDIS Alert: {alert_data.get('title', 'Unknown Threat')}",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {"title": "IP Address", "value": alert_data.get("ip", "Unknown"), "short": True},
                            {"title": "Threat Level", "value": alert_data.get("level", "Unknown"), "short": True},
                            {"title": "Description", "value": alert_data.get("description", "No details"), "short": False}
                        ]
                    }
                ]
            }
            
            response = requests.post(self.config["webhook_url"], json=payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def get_threat_intel(self) -> Dict[str, Any]:
        return {}  # Slack doesn't provide threat intel

# Plugin Marketplace API
class PluginMarketplace:
    """Plugin marketplace management"""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self.marketplace_url = "https://marketplace.nexdis.io"
        
    def search_plugins(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search for plugins in the marketplace"""
        # In a real implementation, this would query a remote marketplace
        available_plugins = [
            {
                "name": "advanced_ssh_honeypot",
                "version": "2.1.0",
                "description": "Advanced SSH honeypot with AI-powered responses",
                "author": "Security Research Lab",
                "category": "honeypot",
                "tags": ["ssh", "ai", "advanced"],
                "downloads": 1250,
                "rating": 4.8,
                "price": "free"
            },
            {
                "name": "siem_integration",
                "version": "1.5.0",
                "description": "Integration with popular SIEM platforms",
                "author": "NEXDIS Partners",
                "category": "integration",
                "tags": ["siem", "splunk", "elastic"],
                "downloads": 890,
                "rating": 4.6,
                "price": "premium"
            },
            {
                "name": "ml_behavior_analyzer",
                "version": "1.0.0",
                "description": "Machine learning-based behavior analysis",
                "author": "ML Security Team",
                "category": "analysis",
                "tags": ["ml", "behavior", "analysis"],
                "downloads": 456,
                "rating": 4.3,
                "price": "free"
            }
        ]
        
        # Filter by query and category
        results = []
        for plugin in available_plugins:
            if query.lower() in plugin["name"].lower() or query.lower() in plugin["description"].lower():
                if category is None or plugin["category"] == category:
                    results.append(plugin)
        
        return results
    
    def install_from_marketplace(self, plugin_name: str) -> bool:
        """Install a plugin from the marketplace"""
        # In a real implementation, this would download from a remote marketplace
        logger.info(f"Installing plugin {plugin_name} from marketplace...")
        
        # Simulate plugin download and installation
        sample_plugin_code = f'''
"""
{plugin_name} - Downloaded from NEXDIS Marketplace
"""

from nexdis_plugins import HoneypotPlugin, PluginInfo

class {plugin_name.replace("_", "").title()}(HoneypotPlugin):
    def get_info(self):
        return PluginInfo(
            name="{plugin_name}",
            version="1.0.0",
            description="Downloaded from marketplace",
            author="Marketplace",
            category="honeypot",
            tags=["marketplace"]
        )
    
    def initialize(self):
        return True
    
    def start(self):
        return True
    
    def stop(self):
        return True
    
    def get_honeypot_type(self):
        return "custom"
    
    def handle_connection(self, client_data):
        return True
    
    def get_fake_responses(self):
        return {{}}
'''
        
        return self.registry.install_plugin(sample_plugin_code.encode(), plugin_name)
    
    def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """Get list of installed plugins"""
        return self.registry.list_plugins()
    
    def manage_plugin(self, plugin_name: str, action: str) -> bool:
        """Manage plugin (start, stop, enable, disable)"""
        if action == "start":
            return self.registry.start_plugin(plugin_name)
        elif action == "stop":
            return self.registry.stop_plugin(plugin_name)
        elif action == "uninstall":
            return self.registry.unload_plugin(plugin_name)
        else:
            return False

# Example usage and testing
if __name__ == "__main__":
    # Initialize marketplace
    marketplace = PluginMarketplace()
    
    print("🔌 NEXDIS Plugin Marketplace Demo")
    print("=" * 50)
    
    # Create sample plugins
    print("\n📦 Installing sample plugins...")
    
    # Install built-in sample plugins
    sample_web = SampleWebHoneypot()
    slack_integration = SlackIntegrationPlugin({"webhook_url": "https://hooks.slack.com/test"})
    
    marketplace.registry.plugins["sample_web"] = sample_web
    marketplace.registry.plugin_info["sample_web"] = sample_web.get_info()
    
    marketplace.registry.plugins["slack_integration"] = slack_integration
    marketplace.registry.plugin_info["slack_integration"] = slack_integration.get_info()
    
    # List installed plugins
    print("\n📋 Installed Plugins:")
    for plugin in marketplace.get_installed_plugins():
        print(f"  • {plugin['name']} v{plugin['version']} ({plugin['category']})")
    
    # Search marketplace
    print("\n🔍 Searching marketplace for 'honeypot':")
    results = marketplace.search_plugins("honeypot")
    for plugin in results:
        print(f"  • {plugin['name']} v{plugin['version']} - {plugin['downloads']} downloads")
    
    print("\n✅ Plugin marketplace demo completed!")