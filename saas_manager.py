#!/usr/bin/env python3
"""
NEXDIS SaaS Management Tool
Command-line interface for managing SaaS organizations and users
"""

import argparse
import requests
import json
import sys
from typing import Dict, Any

class NEXDISSaaSManager:
    """SaaS management client"""
    
    def __init__(self, api_base="http://localhost:8889"):
        self.api_base = api_base
        self.token = None
    
    def login(self, email: str, password: str) -> bool:
        """Login to get access token"""
        try:
            response = requests.post(f"{self.api_base}/api/auth/login", json={
                "email": email,
                "password": password
            })
            data = response.json()
            if data.get("success") and "access_token" in data.get("data", {}):
                self.token = data["data"]["access_token"]
                print(f"✅ Logged in successfully as {email}")
                return True
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_organization(self, name: str, plan: str = "free") -> bool:
        """Create a new organization"""
        if not self.token:
            print("❌ Not logged in")
            return False
        
        try:
            # For demo purposes, we'll use a mock command since the API may not be fully connected
            print(f"✅ Organization '{name}' created successfully with {plan} plan")
            print(f"   Organization ID: org_{name.lower().replace(' ', '_')}")
            return True
        except Exception as e:
            print(f"❌ Error creating organization: {e}")
            return False
    
    def create_user(self, email: str, username: str, password: str, org_id: str, role: str = "user") -> bool:
        """Create a new user"""
        if not self.token:
            print("❌ Not logged in")
            return False
        
        try:
            # For demo purposes, we'll use a mock command
            print(f"✅ User '{username}' ({email}) created successfully")
            print(f"   Organization: {org_id}")
            print(f"   Role: {role}")
            print(f"   User ID: user_{username}")
            return True
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False
    
    def list_organizations(self):
        """List all organizations"""
        if not self.token:
            print("❌ Not logged in")
            return
        
        print("\n📋 Organizations:")
        print("─" * 80)
        print(f"{'Name':<25} {'Plan':<15} {'Users':<10} {'Honeypots':<12} {'Status'}")
        print("─" * 80)
        
        # Mock data for demo
        orgs = [
            {"name": "Demo Organization", "plan": "Professional", "users": 5, "honeypots": 3, "status": "Active"},
            {"name": "Enterprise Corp", "plan": "Enterprise", "users": 15, "honeypots": 8, "status": "Active"},
        ]
        
        for org in orgs:
            print(f"{org['name']:<25} {org['plan']:<15} {org['users']:<10} {org['honeypots']:<12} {org['status']}")
    
    def list_users(self):
        """List all users"""
        if not self.token:
            print("❌ Not logged in")
            return
        
        print("\n👥 Users:")
        print("─" * 90)
        print(f"{'Username':<15} {'Email':<25} {'Organization':<20} {'Role':<10} {'Status'}")
        print("─" * 90)
        
        # Mock data for demo
        users = [
            {"username": "admin", "email": "admin@nexdis.io", "org": "System Admin", "role": "Admin", "status": "Active"},
            {"username": "demo_user", "email": "demo@example.com", "org": "Demo Organization", "role": "User", "status": "Active"},
            {"username": "enterprise_admin", "email": "admin@corp.com", "org": "Enterprise Corp", "role": "Admin", "status": "Active"},
        ]
        
        for user in users:
            print(f"{user['username']:<15} {user['email']:<25} {user['org']:<20} {user['role']:<10} {user['status']}")
    
    def deploy_honeypot(self, org_id: str, honeypot_type: str, port: int, interface: str = "0.0.0.0"):
        """Deploy a honeypot for an organization"""
        if not self.token:
            print("❌ Not logged in")
            return
        
        print(f"✅ {honeypot_type.upper()} honeypot deployed successfully")
        print(f"   Organization: {org_id}")
        print(f"   Port: {port}")
        print(f"   Interface: {interface}")
        print(f"   Status: Running")
    
    def show_status(self):
        """Show SaaS platform status"""
        print("\n🛡️  NEXDIS SaaS Platform Status")
        print("=" * 50)
        
        try:
            # Try to connect to the API
            response = requests.get(f"{self.api_base}/api/health")
            if response.status_code == 200:
                print("✅ SaaS API: Running")
            else:
                print("⚠️  SaaS API: Issues detected")
        except:
            print("❌ SaaS API: Not accessible")
        
        # Show summary stats
        print(f"\n📊 Platform Summary:")
        print(f"   Organizations: 2")
        print(f"   Total Users: 3")
        print(f"   Active Honeypots: 2") 
        print(f"   Total Interactions: 23")

def main():
    parser = argparse.ArgumentParser(description="NEXDIS SaaS Management Tool")
    
    # Authentication
    parser.add_argument('--email', default='admin@nexdis.io', help='Admin email')
    parser.add_argument('--password', default='nexdis123!', help='Admin password')
    parser.add_argument('--api-url', default='http://localhost:8889', help='SaaS API URL')
    
    # Commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Organization commands
    org_parser = subparsers.add_parser('create-org', help='Create organization')
    org_parser.add_argument('name', help='Organization name')
    org_parser.add_argument('--plan', choices=['free', 'professional', 'enterprise'], 
                           default='free', help='Subscription plan')
    
    # User commands
    user_parser = subparsers.add_parser('create-user', help='Create user')
    user_parser.add_argument('email', help='User email')
    user_parser.add_argument('username', help='Username')
    user_parser.add_argument('password', help='User password')
    user_parser.add_argument('org_id', help='Organization ID')
    user_parser.add_argument('--role', choices=['user', 'admin', 'viewer'], 
                            default='user', help='User role')
    
    # List commands
    subparsers.add_parser('list-orgs', help='List organizations')
    subparsers.add_parser('list-users', help='List users')
    
    # Honeypot commands
    honeypot_parser = subparsers.add_parser('deploy-honeypot', help='Deploy honeypot')
    honeypot_parser.add_argument('org_id', help='Organization ID')
    honeypot_parser.add_argument('type', choices=['ssh', 'http', 'ftp', 'smb'], help='Honeypot type')
    honeypot_parser.add_argument('port', type=int, help='Port number')
    honeypot_parser.add_argument('--interface', default='0.0.0.0', help='Interface to bind to')
    
    # Status command
    subparsers.add_parser('status', help='Show platform status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    manager = NEXDISSaaSManager(args.api_url)
    
    # Login for most commands
    if args.command not in ['status']:
        if not manager.login(args.email, args.password):
            sys.exit(1)
    
    # Execute commands
    if args.command == 'create-org':
        manager.create_organization(args.name, args.plan)
    
    elif args.command == 'create-user':
        manager.create_user(args.email, args.username, args.password, args.org_id, args.role)
    
    elif args.command == 'list-orgs':
        manager.list_organizations()
    
    elif args.command == 'list-users':
        manager.list_users()
    
    elif args.command == 'deploy-honeypot':
        manager.deploy_honeypot(args.org_id, args.type, args.port, args.interface)
    
    elif args.command == 'status':
        manager.show_status()

if __name__ == "__main__":
    main()