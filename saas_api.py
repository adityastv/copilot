"""
NEXDIS SaaS API
Enterprise-grade Software-as-a-Service API for NEXDIS platform
Provides multi-tenancy, user management, and advanced features
"""

import os
import json
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

logger = logging.getLogger("NEXDISSaaS")

# Database models
Base = declarative_base()

class Organization(Base):
    __tablename__ = 'organizations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default='free')  # free, professional, enterprise
    max_honeypots = Column(Integer, default=5)
    max_users = Column(Integer, default=3)
    features = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='user')  # admin, user, viewer
    organization_id = Column(String(36), nullable=False)
    api_key = Column(String(255), unique=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Honeypot(Base):
    __tablename__ = 'honeypots'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # ssh, http, ftp, custom
    organization_id = Column(String(36), nullable=False)
    config = Column(JSON, default=dict)
    status = Column(String(50), default='stopped')  # running, stopped, error
    port = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)
    is_active = Column(Boolean, default=True)

class ThreatEvent(Base):
    __tablename__ = 'threat_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), nullable=False)
    honeypot_id = Column(String(36), nullable=False)
    client_ip = Column(String(45), nullable=False)
    threat_type = Column(String(100), nullable=False)
    threat_level = Column(Integer, nullable=False)
    confidence = Column(String(20), nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

@dataclass
class APIResponse:
    success: bool
    data: Any = None
    error: str = None
    message: str = None
    pagination: Dict[str, Any] = None

    def to_dict(self):
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.message:
            result["message"] = self.message
        if self.pagination:
            result["pagination"] = self.pagination
        return result

class NEXDISSaaSAPI:
    """NEXDIS SaaS API Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.app = Flask(__name__)
        self._setup_flask()
        self._setup_database()
        self._setup_routes()
        
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "jwt_secret": os.getenv("JWT_SECRET", secrets.token_urlsafe(32)),
            "database_url": os.getenv("DATABASE_URL", "sqlite:///nexdis_saas.db"),
            "admin_email": os.getenv("ADMIN_EMAIL", "admin@nexdis.io"),
            "admin_password": os.getenv("ADMIN_PASSWORD", "nexdis123!"),
            "max_request_size": 16 * 1024 * 1024,  # 16MB
            "rate_limit": "100 per hour",
            "cors_origins": ["*"],
            "features": {
                "free": {
                    "max_honeypots": 2,
                    "max_users": 2,
                    "threat_retention_days": 7,
                    "api_calls_per_hour": 1000,
                    "features": ["basic_honeypots", "basic_dashboard"]
                },
                "professional": {
                    "max_honeypots": 10,
                    "max_users": 10,
                    "threat_retention_days": 30,
                    "api_calls_per_hour": 10000,
                    "features": ["all_honeypots", "advanced_analytics", "integrations"]
                },
                "enterprise": {
                    "max_honeypots": -1,  # unlimited
                    "max_users": -1,
                    "threat_retention_days": 365,
                    "api_calls_per_hour": 100000,
                    "features": ["everything", "custom_plugins", "priority_support"]
                }
            }
        }
    
    def _setup_flask(self):
        """Setup Flask application"""
        self.app.config['JWT_SECRET_KEY'] = self.config['jwt_secret']
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
        self.app.config['MAX_CONTENT_LENGTH'] = self.config['max_request_size']
        
        # Initialize extensions
        CORS(self.app, origins=self.config['cors_origins'])
        self.jwt = JWTManager(self.app)
        
    def _setup_database(self):
        """Setup database connection and tables"""
        self.engine = create_engine(self.config['database_url'])
        Base.metadata.create_all(self.engine)
        
        # Create database session
        SessionFactory = sessionmaker(bind=self.engine)
        self.db_session = scoped_session(SessionFactory)
        
        # Create default admin user and organization
        self._create_default_data()
    
    def _create_default_data(self):
        """Create default admin organization and user"""
        session = self.db_session()
        
        try:
            # Check if admin org exists
            admin_org = session.query(Organization).filter_by(slug='nexdis-admin').first()
            if not admin_org:
                admin_org = Organization(
                    name="NEXDIS Admin",
                    slug="nexdis-admin",
                    plan="enterprise",
                    max_honeypots=-1,
                    max_users=-1,
                    features={"admin": True, "full_access": True}
                )
                session.add(admin_org)
                session.flush()
            
            # Check if admin user exists
            admin_user = session.query(User).filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    email=self.config['admin_email'],
                    username='admin',
                    password_hash=self._hash_password(self.config['admin_password']),
                    role='admin',
                    organization_id=admin_org.id,
                    api_key=self._generate_api_key()
                )
                session.add(admin_user)
            
            session.commit()
            logger.info("Default admin user created")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating default data: {str(e)}")
        finally:
            session.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_api_key(self) -> str:
        """Generate API key"""
        return f"nxd_{secrets.token_urlsafe(32)}"
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Authentication routes
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify(APIResponse(success=False, error="Email and password required").to_dict()), 400
            
            session = self.db_session()
            try:
                user = session.query(User).filter_by(email=email, is_active=True).first()
                if user and user.password_hash == self._hash_password(password):
                    # Update last login
                    user.last_login = datetime.utcnow()
                    session.commit()
                    
                    # Create JWT token
                    token = create_access_token(
                        identity=user.id,
                        additional_claims={
                            "organization_id": user.organization_id,
                            "role": user.role
                        }
                    )
                    
                    return jsonify(APIResponse(
                        success=True,
                        data={
                            "token": token,
                            "user": {
                                "id": user.id,
                                "email": user.email,
                                "username": user.username,
                                "role": user.role,
                                "organization_id": user.organization_id
                            }
                        },
                        message="Login successful"
                    ).to_dict())
                else:
                    return jsonify(APIResponse(success=False, error="Invalid credentials").to_dict()), 401
            finally:
                session.close()
        
        # Organization routes
        @self.app.route('/api/organizations', methods=['GET'])
        @jwt_required()
        def get_organizations():
            current_user = get_jwt_identity()
            session = self.db_session()
            
            try:
                user = session.query(User).filter_by(id=current_user).first()
                if user.role == 'admin':
                    # Admins can see all organizations
                    orgs = session.query(Organization).all()
                else:
                    # Users can only see their own organization
                    orgs = session.query(Organization).filter_by(id=user.organization_id).all()
                
                return jsonify(APIResponse(
                    success=True,
                    data=[{
                        "id": org.id,
                        "name": org.name,
                        "slug": org.slug,
                        "plan": org.plan,
                        "created_at": org.created_at.isoformat(),
                        "is_active": org.is_active
                    } for org in orgs]
                ).to_dict())
            finally:
                session.close()
        
        # Honeypot routes
        @self.app.route('/api/honeypots', methods=['GET'])
        @jwt_required()
        def get_honeypots():
            current_user_id = get_jwt_identity()
            session = self.db_session()
            
            try:
                user = session.query(User).filter_by(id=current_user_id).first()
                honeypots = session.query(Honeypot).filter_by(
                    organization_id=user.organization_id,
                    is_active=True
                ).all()
                
                return jsonify(APIResponse(
                    success=True,
                    data=[{
                        "id": hp.id,
                        "name": hp.name,
                        "type": hp.type,
                        "status": hp.status,
                        "port": hp.port,
                        "created_at": hp.created_at.isoformat(),
                        "last_activity": hp.last_activity.isoformat() if hp.last_activity else None
                    } for hp in honeypots]
                ).to_dict())
            finally:
                session.close()
        
        @self.app.route('/api/honeypots', methods=['POST'])
        @jwt_required()
        def create_honeypot():
            current_user_id = get_jwt_identity()
            data = request.get_json()
            session = self.db_session()
            
            try:
                user = session.query(User).filter_by(id=current_user_id).first()
                org = session.query(Organization).filter_by(id=user.organization_id).first()
                
                # Check honeypot limit
                current_count = session.query(Honeypot).filter_by(
                    organization_id=org.id,
                    is_active=True
                ).count()
                
                if org.max_honeypots != -1 and current_count >= org.max_honeypots:
                    return jsonify(APIResponse(
                        success=False,
                        error=f"Honeypot limit reached ({org.max_honeypots})"
                    ).to_dict()), 403
                
                # Create honeypot
                honeypot = Honeypot(
                    name=data.get('name', 'New Honeypot'),
                    type=data.get('type', 'ssh'),
                    organization_id=org.id,
                    config=data.get('config', {}),
                    port=data.get('port')
                )
                
                session.add(honeypot)
                session.commit()
                
                return jsonify(APIResponse(
                    success=True,
                    data={
                        "id": honeypot.id,
                        "name": honeypot.name,
                        "type": honeypot.type,
                        "status": honeypot.status
                    },
                    message="Honeypot created successfully"
                ).to_dict()), 201
                
            finally:
                session.close()
        
        # Threat events routes
        @self.app.route('/api/threats', methods=['GET'])
        @jwt_required()
        def get_threats():
            current_user_id = get_jwt_identity()
            session = self.db_session()
            
            try:
                user = session.query(User).filter_by(id=current_user_id).first()
                
                # Query parameters
                limit = min(int(request.args.get('limit', 50)), 1000)
                offset = int(request.args.get('offset', 0))
                threat_level = request.args.get('threat_level')
                
                query = session.query(ThreatEvent).filter_by(organization_id=user.organization_id)
                
                if threat_level:
                    query = query.filter(ThreatEvent.threat_level >= int(threat_level))
                
                total_count = query.count()
                threats = query.offset(offset).limit(limit).all()
                
                return jsonify(APIResponse(
                    success=True,
                    data=[{
                        "id": threat.id,
                        "client_ip": threat.client_ip,
                        "threat_type": threat.threat_type,
                        "threat_level": threat.threat_level,
                        "confidence": threat.confidence,
                        "timestamp": threat.timestamp.isoformat(),
                        "resolved": threat.resolved,
                        "details": threat.details
                    } for threat in threats],
                    pagination={
                        "total": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_more": offset + limit < total_count
                    }
                ).to_dict())
            finally:
                session.close()
        
        # Analytics routes
        @self.app.route('/api/analytics/dashboard', methods=['GET'])
        @jwt_required()
        def get_dashboard_analytics():
            current_user_id = get_jwt_identity()
            session = self.db_session()
            
            try:
                user = session.query(User).filter_by(id=current_user_id).first()
                org_id = user.organization_id
                
                # Get various analytics
                total_honeypots = session.query(Honeypot).filter_by(
                    organization_id=org_id,
                    is_active=True
                ).count()
                
                active_honeypots = session.query(Honeypot).filter_by(
                    organization_id=org_id,
                    is_active=True,
                    status='running'
                ).count()
                
                total_threats = session.query(ThreatEvent).filter_by(organization_id=org_id).count()
                
                recent_threats = session.query(ThreatEvent).filter_by(
                    organization_id=org_id
                ).filter(
                    ThreatEvent.timestamp >= datetime.utcnow() - timedelta(days=7)
                ).count()
                
                return jsonify(APIResponse(
                    success=True,
                    data={
                        "total_honeypots": total_honeypots,
                        "active_honeypots": active_honeypots,
                        "total_threats": total_threats,
                        "recent_threats": recent_threats,
                        "threat_levels": {
                            "critical": session.query(ThreatEvent).filter_by(
                                organization_id=org_id, threat_level=4
                            ).count(),
                            "high": session.query(ThreatEvent).filter_by(
                                organization_id=org_id, threat_level=3
                            ).count(),
                            "medium": session.query(ThreatEvent).filter_by(
                                organization_id=org_id, threat_level=2
                            ).count(),
                            "low": session.query(ThreatEvent).filter_by(
                                organization_id=org_id, threat_level=1
                            ).count(),
                        }
                    }
                ).to_dict())
            finally:
                session.close()
        
        # Health check
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify(APIResponse(
                success=True,
                data={
                    "status": "healthy",
                    "version": "1.0.0",
                    "timestamp": datetime.utcnow().isoformat()
                },
                message="NEXDIS SaaS API is running"
            ).to_dict())
        
        # API documentation endpoint
        @self.app.route('/api/docs', methods=['GET'])
        def api_docs():
            docs = {
                "title": "NEXDIS SaaS API",
                "version": "1.0.0",
                "description": "Enterprise-grade API for NEXDIS cybersecurity deception platform",
                "endpoints": {
                    "Authentication": [
                        {"method": "POST", "path": "/api/auth/login", "description": "User login"}
                    ],
                    "Organizations": [
                        {"method": "GET", "path": "/api/organizations", "description": "List organizations"}
                    ],
                    "Honeypots": [
                        {"method": "GET", "path": "/api/honeypots", "description": "List honeypots"},
                        {"method": "POST", "path": "/api/honeypots", "description": "Create honeypot"}
                    ],
                    "Threats": [
                        {"method": "GET", "path": "/api/threats", "description": "List threat events"}
                    ],
                    "Analytics": [
                        {"method": "GET", "path": "/api/analytics/dashboard", "description": "Dashboard analytics"}
                    ]
                },
                "authentication": "JWT Bearer token required for most endpoints"
            }
            
            return jsonify(APIResponse(success=True, data=docs).to_dict())
    
    def start(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Start the SaaS API server"""
        logger.info(f"Starting NEXDIS SaaS API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    def get_app(self):
        """Get Flask app instance"""
        return self.app

# CLI for SaaS management
def create_organization(api: NEXDISSaaSAPI, name: str, plan: str = "free") -> str:
    """Create a new organization"""
    session = api.db_session()
    
    try:
        org = Organization(
            name=name,
            slug=name.lower().replace(' ', '-'),
            plan=plan,
            max_honeypots=api.config['features'][plan]['max_honeypots'],
            max_users=api.config['features'][plan]['max_users'],
            features=api.config['features'][plan]['features']
        )
        
        session.add(org)
        session.commit()
        
        logger.info(f"Created organization: {name} ({plan})")
        return org.id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating organization: {str(e)}")
        raise
    finally:
        session.close()

def create_user(api: NEXDISSaaSAPI, email: str, username: str, password: str, 
                organization_id: str, role: str = "user") -> str:
    """Create a new user"""
    session = api.db_session()
    
    try:
        user = User(
            email=email,
            username=username,
            password_hash=api._hash_password(password),
            role=role,
            organization_id=organization_id,
            api_key=api._generate_api_key()
        )
        
        session.add(user)
        session.commit()
        
        logger.info(f"Created user: {username} ({email})")
        return user.id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise
    finally:
        session.close()

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXDIS SaaS API Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--create-org', help='Create organization (name:plan)')
    parser.add_argument('--create-user', help='Create user (email:username:password:org_id:role)')
    
    args = parser.parse_args()
    
    # Initialize API
    api = NEXDISSaaSAPI()
    
    if args.create_org:
        parts = args.create_org.split(':')
        org_id = create_organization(api, parts[0], parts[1] if len(parts) > 1 else 'free')
        print(f"Created organization with ID: {org_id}")
        
    elif args.create_user:
        parts = args.create_user.split(':')
        if len(parts) >= 4:
            user_id = create_user(api, parts[0], parts[1], parts[2], parts[3], 
                                parts[4] if len(parts) > 4 else 'user')
            print(f"Created user with ID: {user_id}")
        else:
            print("Usage: --create-user email:username:password:org_id:role")
    
    else:
        print(f"🚀 Starting NEXDIS SaaS API...")
        print(f"📊 Admin credentials: {api.config['admin_email']} / {api.config['admin_password']}")
        print(f"🌐 API Documentation: http://{args.host}:{args.port}/api/docs")
        api.start(host=args.host, port=args.port, debug=args.debug)