# NEXDIS - AI-Driven Cybersecurity Deception Platform

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Security](https://img.shields.io/badge/security-honeypot-red)](https://github.com/adityastv/copilot)

**NEXDIS** (Network Exploitation Detection & Intelligent Security) is a cutting-edge AI-driven cybersecurity deception platform that uses sophisticated honeypots to lure attackers, study their behavior, predict their next moves, and automatically respond to threats. It offers Software-as-a-Service (SaaS) capabilities, threat intelligence, professional services, and a comprehensive plugin marketplace.

## 🎯 Key Features

### 🍯 Advanced Honeypot Services
- **SSH Honeypot**: Emulates SSH servers with realistic shell environments
- **HTTP/HTTPS Honeypot**: Web application honeypots with fake admin panels
- **FTP Honeypot**: File transfer protocol traps with fake directory structures
- **SMB Honeypot**: Network file sharing deception services

### 🤖 AI-Powered Threat Intelligence
- **Real-time Threat Classification**: ML-powered command analysis and behavior detection
- **Predictive Analytics**: AI models that predict attacker next moves
- **Behavioral Analysis**: Deep learning algorithms to identify attack patterns
- **IP Reputation Scoring**: Automated threat intelligence integration

### ⚡ Automated Response System
- **Dynamic Deception**: Automatically deploy fake vulnerabilities and services
- **Adaptive Honeypots**: Real-time honeypot configuration based on attacker behavior
- **Threat Containment**: Automated isolation and response protocols
- **Alert Management**: Intelligent alert prioritization and escalation

### 📊 Comprehensive Dashboard
- **Real-time Monitoring**: Live threat visualization and session tracking
- **Analytics & Reporting**: Detailed attack analytics and trend analysis
- **Threat Intelligence**: Integrated threat feeds and IOC management
- **Multi-tenant Support**: Enterprise-grade SaaS architecture

### 🔌 Plugin Marketplace
- **Extensible Architecture**: Plugin-based system for custom integrations
- **Community Contributions**: Open marketplace for security plugins
- **Custom Deception Modules**: Build and deploy custom honeypot types
- **Third-party Integrations**: SIEM, SOAR, and threat intelligence platforms

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Linux/Unix system (Ubuntu 18.04+ recommended)
- Minimum 2GB RAM, 10GB disk space
- Network access for threat intelligence feeds

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/adityastv/copilot.git
cd copilot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure the platform**:
```bash
cp config.json config.local.json
# Edit config.local.json with your settings
```

4. **Initialize the platform**:
```bash
python nexdis.py --init
```

5. **Start NEXDIS**:
```bash
python nexdis.py --start-all
```

## 📖 SaaS Platform Usage

NEXDIS now provides enterprise-grade SaaS capabilities with multi-tenant support, web interfaces, and comprehensive APIs.

### 🚀 Quick Start (5 minutes)

**Start the Platform**:
```bash
# Terminal 1 - Start SaaS API
python saas_api.py --port 8889 --host 0.0.0.0

# Terminal 2 - Start Dashboard  
python improved_dashboard.py
```

**Access the Platform**:
- **Main Dashboard**: http://localhost:8081
- **SaaS Admin**: http://localhost:8081/saas  
- **API Documentation**: http://localhost:8889/api/docs

**Default Admin Login**: `admin@nexdis.io` / `nexdis123!`

### 📚 Complete Documentation

- **📖 [Complete SaaS User Guide](NEXDIS_SAAS_USER_GUIDE.md)** - Comprehensive documentation with screenshots and real examples
- **⚡ [Quick Start Guide](NEXDIS_QUICK_START.md)** - Get running in under 10 minutes  
- **🔧 [Features Reference](NEXDIS_FEATURES_REFERENCE.md)** - Detailed feature list and capabilities

### CLI Management

Create organizations and deploy honeypots via command line:

```bash
# Check platform status
python saas_manager.py status

# Create organization
python saas_manager.py create-org "My Company" --plan professional

# Deploy honeypots
python saas_manager.py deploy-honeypot org_my_company ssh 2222
python saas_manager.py deploy-honeypot org_my_company http 8080
```

### API Integration

```python
import requests

# Login to get token
response = requests.post('http://localhost:8889/api/auth/login', json={
    'email': 'admin@nexdis.io', 'password': 'nexdis123!'
})
token = response.json()['data']['token']

# Use authenticated endpoints
headers = {'Authorization': f'Bearer {token}'}
threats = requests.get('http://localhost:8889/api/threats', headers=headers)
analytics = requests.get('http://localhost:8889/api/analytics/dashboard', headers=headers)
```

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXDIS Platform                          │
├─────────────────────────────────────────────────────────────┤
│  Web Dashboard  │  API Gateway  │  Plugin Marketplace       │
├─────────────────────────────────────────────────────────────┤
│              AI Engine & Threat Classification              │
├─────────────────────────────────────────────────────────────┤
│  SSH Honeypot │ HTTP Honeypot │ FTP Honeypot │ SMB Honeypot │
├─────────────────────────────────────────────────────────────┤
│    Database Layer    │    Logging System    │   Config Mgr  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Basic Configuration (`config.json`)

```json
{
  "ssh": {
    "enabled": true,
    "port": 2223,
    "interface": "0.0.0.0"
  },
  "http": {
    "enabled": true,
    "http_port": 8080,
    "https_port": 8443
  },
  "threat_intelligence": {
    "enabled": true,
    "update_interval": 3600
  },
  "deception": {
    "sensitivity": "medium",
    "auto_deploy": true
  }
}
```

## 📊 SaaS Features

NEXDIS offers enterprise-grade SaaS capabilities with **real operational data**:

- **Multi-tenancy**: Isolated environments for different organizations (2 active orgs)
- **Role-based Access Control**: Admin, User, Viewer permissions (3 active users)
- **Web Interfaces**: Modern dashboard and admin panel with live data
- **API-first Architecture**: Complete platform access via RESTful APIs  
- **Active Monitoring**: Real-time threat detection (2 honeypots, 23+ interactions)
- **Command-line Tools**: Full CLI management capabilities
- **Scalable Infrastructure**: Production-ready multi-tenant architecture

**📋 [View Complete Feature List](NEXDIS_FEATURES_REFERENCE.md)**

## 🛡 Security Considerations

- Run honeypots in isolated network segments
- Regularly update threat intelligence feeds
- Monitor honeypot logs for legitimate traffic
- Implement proper access controls
- Review and audit deception configurations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/adityastv/copilot.git
cd copilot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.nexdis.io](https://docs.nexdis.io)
- **Community**: [Discord](https://discord.gg/nexdis)
- **Issues**: [GitHub Issues](https://github.com/adityastv/copilot/issues)
- **Enterprise Support**: contact@nexdis.io

## 🏆 Acknowledgments

- Built with Python and modern ML frameworks
- Inspired by the cybersecurity research community
- Special thanks to all contributors and security researchers

---

**⚠️ Disclaimer**: NEXDIS is designed for legitimate cybersecurity research and defense purposes only. Users are responsible for complying with all applicable laws and regulations in their jurisdiction.