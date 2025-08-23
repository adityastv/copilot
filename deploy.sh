#!/bin/bash

# NEXDIS Platform Deployment Script
# Quick setup and deployment for NEXDIS cybersecurity deception platform

set -e

echo "🚀 NEXDIS Platform Deployment Script"
echo "====================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --user --quiet

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs/{threats,honeypots,dashboard}
mkdir -p data/{threat_intel,uploads,backups}
mkdir -p models
mkdir -p keys
mkdir -p plugins/{installed,available}

# Generate SSH key if needed
if [ ! -f "server.key" ]; then
    echo "🔑 Generating SSH key..."
    ssh-keygen -t rsa -b 2048 -f server.key -N "" -q
    chmod 600 server.key
fi

# Initialize platform
echo "🏗️ Initializing NEXDIS platform..."
python3 nexdis.py --init

echo ""
echo "✅ NEXDIS Platform deployed successfully!"
echo ""
echo "📋 Quick Start Guide:"
echo "  • Start all services:    python3 nexdis.py --start-all"
echo "  • Start SSH honeypot:    python3 nexdis.py --service ssh"
echo "  • Start dashboard:       python3 nexdis.py --service dashboard"
echo "  • Check status:          python3 nexdis.py --status"
echo "  • View help:             python3 nexdis.py --help"
echo ""
echo "🌐 Web Interfaces:"
echo "  • Dashboard:    http://localhost:9090"
echo "  • SaaS API:     http://localhost:8888/api/docs"
echo ""
echo "📖 Configuration:"
echo "  • Main config:  config.json"
echo "  • Logs:         logs/"
echo "  • Data:         data/"
echo ""
echo "⚠️  Security Notice:"
echo "  • Run honeypots on isolated network segments"
echo "  • Monitor logs for legitimate traffic"
echo "  • Review configuration before production use"
echo ""
echo "🎯 NEXDIS is ready for cybersecurity deception operations!"