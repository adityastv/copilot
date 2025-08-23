import json
import os
import glob
import time
import threading
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ImprovedDashboard")

class ImprovedDashboardRequestHandler(BaseHTTPRequestHandler):
    """Improved HTTP request handler for the threat dashboard"""
    
    def __init__(self, *args, **kwargs):
        self.dashboard = kwargs.pop('dashboard', None)
        super().__init__(*args, **kwargs)
        
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")
        
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/" or path == "/index.html":
            self.serve_dashboard()
        elif path == "/saas":
            self.serve_saas_interface()
        elif path == "/api/sessions":
            self.serve_sessions()
        elif path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            self.serve_session_details(session_id)
        elif path == "/api/alerts":
            self.serve_alerts()
        elif path == "/api/stats":
            self.serve_stats()
        elif path.startswith("/static/"):
            self.serve_static_file(path[8:])
        else:
            self.send_error(404)
            
    def serve_dashboard(self):
        """Serve the improved dashboard HTML with embedded CSS and JS"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXDIS - Threat Intelligence Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        
        /* Navigation */
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-menu {
            display: flex;
            list-style: none;
            gap: 30px;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 10px 15px;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        
        .nav-link:hover, .nav-link.active {
            background-color: rgba(255,255,255,0.2);
        }
        
        /* Main content */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Stats cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 1rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Content grid */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .panel {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .panel-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        .panel-content {
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        /* Table styles */
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        .table tr:hover {
            background-color: #f8f9fa;
            cursor: pointer;
        }
        
        /* Alert styles */
        .alert {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-info {
            background-color: #e3f2fd;
            border-left-color: #2196f3;
            color: #0c5460;
        }
        
        .alert-low {
            background-color: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        
        .alert-medium {
            background-color: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }
        
        .alert-high {
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        
        .alert-critical {
            background-color: #dc3545;
            border-left-color: #a71e2a;
            color: white;
        }
        
        /* Chart container */
        .chart-container {
            width: 100%;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
            font-size: 1.1rem;
        }
        
        /* Buttons */
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: opacity 0.3s;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 10% auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 600px;
            position: relative;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        /* Loading states */
        .loading {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 20px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            
            .nav-menu {
                flex-direction: column;
                gap: 10px;
            }
            
            .nav-container {
                flex-direction: column;
                gap: 20px;
            }
        }
        
        /* Status indicators */
        .status-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-active { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-danger { background-color: #dc3545; }
        .status-info { background-color: #17a2b8; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="navbar-brand">
                🛡️ NEXDIS
            </div>
            <ul class="nav-menu">
                <li><a href="#" class="nav-link active">Dashboard</a></li>
                <li><a href="/saas" class="nav-link">SaaS Admin</a></li>
                <li><a href="#sessions" class="nav-link">Sessions</a></li>
                <li><a href="#alerts" class="nav-link">Alerts</a></li>
                <li><a href="#reports" class="nav-link">Reports</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <!-- Stats Section -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="active-sessions">-</div>
                <div class="stat-label">Active Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="commands-processed">-</div>
                <div class="stat-label">Commands Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-alerts">-</div>
                <div class="stat-label">Total Alerts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="critical-alerts">-</div>
                <div class="stat-label">Critical Alerts</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="content-grid">
            <div class="panel">
                <div class="panel-header">Recent Alerts</div>
                <div class="panel-content">
                    <div id="alerts-timeline" class="loading">Loading alerts...</div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Active Sessions</div>
                <div class="panel-content">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>IP Address</th>
                                <th>Start Time</th>
                                <th>Commands</th>
                                <th>Threat Level</th>
                                <th>Last Activity</th>
                            </tr>
                        </thead>
                        <tbody id="sessions-table">
                            <tr>
                                <td colspan="5" class="loading">Loading sessions...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="content-grid">
            <div class="panel">
                <div class="panel-header">Threat Distribution</div>
                <div class="panel-content">
                    <div class="chart-container">
                        📊 Threat analytics visualization would appear here
                        <br><small>Chart.js integration available</small>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Top Attack Types</div>
                <div class="panel-content">
                    <div class="chart-container">
                        📈 Attack type distribution would appear here
                        <br><small>Chart.js integration available</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Commands -->
        <div class="panel">
            <div class="panel-header">Recent Commands</div>
            <div class="panel-content">
                <div id="commands-list" class="loading">Loading commands...</div>
            </div>
        </div>
    </div>

    <!-- Session Details Modal -->
    <div id="sessionModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h3>Session Details</h3>
            <div id="session-detail-content" class="loading">Loading session details...</div>
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
        </div>
    </div>

    <script>
        // Global variables
        let refreshInterval;
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadSessions();
            loadAlerts();
            loadCommands();
            
            // Set up refresh interval
            refreshInterval = setInterval(function() {
                loadStats();
                loadSessions();
                loadAlerts();
                loadCommands();
            }, 30000); // Refresh every 30 seconds
            
            // Modal setup
            setupModal();
        });
        
        // Load dashboard stats
        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('active-sessions').textContent = data.active_sessions || 0;
                    document.getElementById('commands-processed').textContent = data.commands_processed || 0;
                    document.getElementById('total-alerts').textContent = data.total_alerts || 0;
                    document.getElementById('critical-alerts').textContent = data.critical_alerts || 0;
                })
                .catch(error => {
                    console.error('Error loading stats:', error);
                    // Set placeholder values
                    document.getElementById('active-sessions').textContent = '0';
                    document.getElementById('commands-processed').textContent = '0';
                    document.getElementById('total-alerts').textContent = '0';
                    document.getElementById('critical-alerts').textContent = '0';
                });
        }
        
        // Load active sessions
        function loadSessions() {
            fetch('/api/sessions')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('sessions-table');
                    tbody.innerHTML = '';
                    
                    if (data.sessions.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" class="loading">No active sessions</td></tr>';
                        return;
                    }
                    
                    data.sessions.forEach(session => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td><span class="status-dot status-active"></span>${session.client_ip}</td>
                            <td>${formatTime(session.start_time)}</td>
                            <td>${session.command_count}</td>
                            <td><span class="status-dot status-${session.max_threat_severity}"></span>${session.max_threat_severity}</td>
                            <td>${formatTimeAgo(session.last_activity)}</td>
                        `;
                        row.addEventListener('click', () => showSessionDetails(session.session_id));
                        tbody.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Error loading sessions:', error);
                    document.getElementById('sessions-table').innerHTML = 
                        '<tr><td colspan="5" class="loading">Error loading sessions</td></tr>';
                });
        }
        
        // Load alerts
        function loadAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    const alertsTimeline = document.getElementById('alerts-timeline');
                    alertsTimeline.innerHTML = '';
                    
                    if (data.alerts.length === 0) {
                        alertsTimeline.innerHTML = '<div class="loading">No alerts</div>';
                        return;
                    }
                    
                    data.alerts.forEach(alert => {
                        const alertElement = document.createElement('div');
                        alertElement.className = `alert alert-${alert.severity}`;
                        alertElement.innerHTML = `
                            <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}
                            <br><small>IP: ${alert.client_ip} • ${formatTimeAgo(alert.timestamp)}</small>
                        `;
                        alertsTimeline.appendChild(alertElement);
                    });
                })
                .catch(error => {
                    console.error('Error loading alerts:', error);
                    document.getElementById('alerts-timeline').innerHTML = 
                        '<div class="loading">Error loading alerts</div>';
                });
        }
        
        // Load recent commands
        function loadCommands() {
            // This would fetch from a commands API endpoint
            const commandsList = document.getElementById('commands-list');
            commandsList.innerHTML = `
                <div class="loading">Recent command monitoring active</div>
                <div style="margin-top: 15px; font-size: 0.9rem; color: #6c757d;">
                    Commands will appear here as honeypot interactions occur
                </div>
            `;
        }
        
        // Show session details in modal
        function showSessionDetails(sessionId) {
            const modal = document.getElementById('sessionModal');
            const contentDiv = document.getElementById('session-detail-content');
            contentDiv.innerHTML = '<div class="loading">Loading session details...</div>';
            modal.style.display = 'block';
            
            fetch(`/api/session/${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    contentDiv.innerHTML = `
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
                            <div>
                                <h6>Session Information</h6>
                                <p><strong>Session ID:</strong> ${data.session_id}</p>
                                <p><strong>Client IP:</strong> ${data.client_ip}</p>
                                <p><strong>Protocol:</strong> ${data.protocol}</p>
                                <p><strong>Start Time:</strong> ${formatTime(data.start_time)}</p>
                                <p><strong>Duration:</strong> ${data.duration || 'Ongoing'}</p>
                            </div>
                            <div>
                                <h6>Threat Analysis</h6>
                                <p><strong>Threat Level:</strong> ${data.threat_level || 'Unknown'}</p>
                                <p><strong>Status:</strong> ${data.status || 'Active'}</p>
                                <p><strong>Commands:</strong> ${data.command_count || 0}</p>
                            </div>
                        </div>
                    `;
                })
                .catch(error => {
                    console.error('Error loading session details:', error);
                    contentDiv.innerHTML = '<p class="loading">Error loading session details</p>';
                });
        }
        
        // Setup modal
        function setupModal() {
            const modal = document.getElementById('sessionModal');
            const closeBtn = document.querySelector('.close');
            
            closeBtn.onclick = function() {
                modal.style.display = 'none';
            }
            
            window.onclick = function(event) {
                if (event.target == modal) {
                    modal.style.display = 'none';
                }
            }
        }
        
        function closeModal() {
            document.getElementById('sessionModal').style.display = 'none';
        }
        
        // Utility functions
        function formatTime(timestamp) {
            return new Date(timestamp).toLocaleString();
        }
        
        function formatTimeAgo(timestamp) {
            const now = new Date();
            const time = new Date(timestamp);
            const diffInSeconds = Math.floor((now - time) / 1000);
            
            if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
            return `${Math.floor(diffInSeconds / 86400)}d ago`;
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def serve_saas_interface(self):
        """Serve the SaaS management interface"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXDIS - SaaS Administration</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        
        /* Navigation */
        .navbar {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            color: white;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-menu {
            display: flex;
            list-style: none;
            gap: 30px;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 10px 15px;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        
        .nav-link:hover, .nav-link.active {
            background-color: rgba(255,255,255,0.2);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .section-header {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .section-title {
            font-size: 2rem;
            color: #333;
            margin-bottom: 10px;
        }
        
        .section-subtitle {
            color: #666;
            font-size: 1.1rem;
        }
        
        .admin-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .admin-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .admin-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .card-icon {
            font-size: 2rem;
            margin-right: 15px;
            color: #764ba2;
        }
        
        .card-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: #333;
        }
        
        .btn {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: opacity 0.3s;
            text-decoration: none;
            display: inline-block;
            margin: 5px 5px 5px 0;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .btn-success {
            background: #28a745;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        
        .form-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .form-select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            background: white;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-active {
            background-color: #d4edda;
            color: #155724;
        }
        
        .status-inactive {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .data-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        .data-table tr:hover {
            background-color: #f8f9fa;
        }
        
        .loading {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 20px;
        }
        
        .alert {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-success {
            background-color: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="navbar-brand">
                ⚙️ NEXDIS SaaS Admin
            </div>
            <ul class="nav-menu">
                <li><a href="/" class="nav-link">Dashboard</a></li>
                <li><a href="/saas" class="nav-link active">SaaS Admin</a></li>
                <li><a href="#organizations" class="nav-link">Organizations</a></li>
                <li><a href="#users" class="nav-link">Users</a></li>
                <li><a href="#honeypots" class="nav-link">Honeypots</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <div class="section-header">
            <h1 class="section-title">SaaS Administration Panel</h1>
            <p class="section-subtitle">Manage organizations, users, and honeypot deployments</p>
        </div>

        <!-- Quick Actions -->
        <div class="admin-grid">
            <div class="admin-card">
                <div class="card-header">
                    <div class="card-icon">🏢</div>
                    <div class="card-title">Organizations</div>
                </div>
                <p>Manage customer organizations and their subscriptions.</p>
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="showCreateOrganization()">Create Organization</button>
                    <button class="btn btn-secondary" onclick="loadOrganizations()">View All</button>
                </div>
            </div>

            <div class="admin-card">
                <div class="card-header">
                    <div class="card-icon">👥</div>
                    <div class="card-title">Users</div>
                </div>
                <p>Manage user accounts and permissions across organizations.</p>
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="showCreateUser()">Create User</button>
                    <button class="btn btn-secondary" onclick="loadUsers()">View All</button>
                </div>
            </div>

            <div class="admin-card">
                <div class="card-header">
                    <div class="card-icon">🍯</div>
                    <div class="card-title">Honeypots</div>
                </div>
                <p>Deploy and manage honeypot instances for organizations.</p>
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="showDeployHoneypot()">Deploy Honeypot</button>
                    <button class="btn btn-secondary" onclick="loadHoneypots()">View Active</button>
                </div>
            </div>

            <div class="admin-card">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <div class="card-title">Analytics</div>
                </div>
                <p>View system-wide analytics and usage metrics.</p>
                <div style="margin-top: 15px;">
                    <button class="btn btn-secondary" onclick="loadAnalytics()">View Analytics</button>
                </div>
            </div>
        </div>

        <!-- Data Display Area -->
        <div class="admin-card">
            <div class="card-header">
                <div class="card-icon">📋</div>
                <div class="card-title" id="data-title">System Overview</div>
            </div>
            <div id="data-content">
                <div class="loading">Select an action above to begin managing your SaaS platform</div>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        const SAAS_API_BASE = 'http://localhost:8889/api';
        let authToken = null;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Try to authenticate with default admin credentials
            login('admin@nexdis.io', 'nexdis123!');
        });

        // Authentication
        function login(email, password) {
            fetch(`${SAAS_API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    authToken = data.data.access_token;
                    showMessage('Successfully authenticated as admin', 'success');
                } else {
                    showMessage('Authentication failed: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                showMessage('Authentication service not available', 'error');
            });
        }

        // Organization management
        function showCreateOrganization() {
            document.getElementById('data-title').textContent = 'Create Organization';
            document.getElementById('data-content').innerHTML = `
                <form onsubmit="createOrganization(event)">
                    <div class="form-group">
                        <label class="form-label">Organization Name</label>
                        <input type="text" id="org-name" class="form-input" required placeholder="Acme Corporation">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Plan</label>
                        <select id="org-plan" class="form-select">
                            <option value="free">Free</option>
                            <option value="professional">Professional</option>
                            <option value="enterprise">Enterprise</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Create Organization</button>
                    <button type="button" class="btn btn-secondary" onclick="loadOrganizations()">Cancel</button>
                </form>
            `;
        }

        function createOrganization(event) {
            event.preventDefault();
            const name = document.getElementById('org-name').value;
            const plan = document.getElementById('org-plan').value;

            if (!authToken) {
                showMessage('Please authenticate first', 'error');
                return;
            }

            // For demo purposes, we'll simulate the API call
            showMessage(`Organization "${name}" created successfully with ${plan} plan`, 'success');
            setTimeout(() => loadOrganizations(), 1000);
        }

        function loadOrganizations() {
            document.getElementById('data-title').textContent = 'Organizations';
            document.getElementById('data-content').innerHTML = `
                <div class="loading">Loading organizations...</div>
            `;

            // Simulate loading organizations
            setTimeout(() => {
                document.getElementById('data-content').innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Plan</th>
                                <th>Users</th>
                                <th>Honeypots</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Demo Organization</td>
                                <td>Professional</td>
                                <td>5</td>
                                <td>3</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>2024-01-15</td>
                                <td>
                                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;">Edit</button>
                                </td>
                            </tr>
                            <tr>
                                <td>Enterprise Corp</td>
                                <td>Enterprise</td>
                                <td>15</td>
                                <td>8</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>2024-02-20</td>
                                <td>
                                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;">Edit</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div style="margin-top: 20px;">
                        <button class="btn" onclick="showCreateOrganization()">Add New Organization</button>
                    </div>
                `;
            }, 500);
        }

        // User management
        function showCreateUser() {
            document.getElementById('data-title').textContent = 'Create User';
            document.getElementById('data-content').innerHTML = `
                <form onsubmit="createUser(event)">
                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" id="user-email" class="form-input" required placeholder="user@example.com">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Username</label>
                        <input type="text" id="user-username" class="form-input" required placeholder="username">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <input type="password" id="user-password" class="form-input" required placeholder="password">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Organization</label>
                        <select id="user-org" class="form-select">
                            <option value="demo-org">Demo Organization</option>
                            <option value="enterprise-corp">Enterprise Corp</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Role</label>
                        <select id="user-role" class="form-select">
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                            <option value="viewer">Viewer</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Create User</button>
                    <button type="button" class="btn btn-secondary" onclick="loadUsers()">Cancel</button>
                </form>
            `;
        }

        function createUser(event) {
            event.preventDefault();
            const email = document.getElementById('user-email').value;
            const username = document.getElementById('user-username').value;
            
            showMessage(`User "${username}" (${email}) created successfully`, 'success');
            setTimeout(() => loadUsers(), 1000);
        }

        function loadUsers() {
            document.getElementById('data-title').textContent = 'Users';
            document.getElementById('data-content').innerHTML = `
                <div class="loading">Loading users...</div>
            `;

            setTimeout(() => {
                document.getElementById('data-content').innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Organization</th>
                                <th>Role</th>
                                <th>Last Login</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>admin</td>
                                <td>admin@nexdis.io</td>
                                <td>System Admin</td>
                                <td>Admin</td>
                                <td>2024-08-23</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>
                                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;">Edit</button>
                                </td>
                            </tr>
                            <tr>
                                <td>demo_user</td>
                                <td>demo@example.com</td>
                                <td>Demo Organization</td>
                                <td>User</td>
                                <td>2024-08-20</td>
                                <td><span class="status-badge status-active">Active</span></td>
                                <td>
                                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;">Edit</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div style="margin-top: 20px;">
                        <button class="btn" onclick="showCreateUser()">Add New User</button>
                    </div>
                `;
            }, 500);
        }

        // Honeypot management
        function showDeployHoneypot() {
            document.getElementById('data-title').textContent = 'Deploy Honeypot';
            document.getElementById('data-content').innerHTML = `
                <form onsubmit="deployHoneypot(event)">
                    <div class="form-group">
                        <label class="form-label">Honeypot Type</label>
                        <select id="honeypot-type" class="form-select">
                            <option value="ssh">SSH Honeypot</option>
                            <option value="http">HTTP Honeypot</option>
                            <option value="ftp">FTP Honeypot</option>
                            <option value="smb">SMB Honeypot</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Organization</label>
                        <select id="honeypot-org" class="form-select">
                            <option value="demo-org">Demo Organization</option>
                            <option value="enterprise-corp">Enterprise Corp</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Port</label>
                        <input type="number" id="honeypot-port" class="form-input" placeholder="2222" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Interface</label>
                        <input type="text" id="honeypot-interface" class="form-input" placeholder="0.0.0.0" value="0.0.0.0">
                    </div>
                    <button type="submit" class="btn">Deploy Honeypot</button>
                    <button type="button" class="btn btn-secondary" onclick="loadHoneypots()">Cancel</button>
                </form>
            `;
        }

        function deployHoneypot(event) {
            event.preventDefault();
            const type = document.getElementById('honeypot-type').value;
            const port = document.getElementById('honeypot-port').value;
            
            showMessage(`${type.toUpperCase()} honeypot deployed on port ${port}`, 'success');
            setTimeout(() => loadHoneypots(), 1000);
        }

        function loadHoneypots() {
            document.getElementById('data-title').textContent = 'Active Honeypots';
            document.getElementById('data-content').innerHTML = `
                <div class="loading">Loading honeypots...</div>
            `;

            setTimeout(() => {
                document.getElementById('data-content').innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Organization</th>
                                <th>Port</th>
                                <th>Interface</th>
                                <th>Status</th>
                                <th>Deployed</th>
                                <th>Interactions</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>SSH</td>
                                <td>Demo Organization</td>
                                <td>2222</td>
                                <td>0.0.0.0</td>
                                <td><span class="status-badge status-active">Running</span></td>
                                <td>2024-08-20</td>
                                <td>15</td>
                                <td>
                                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;">Stop</button>
                                </td>
                            </tr>
                            <tr>
                                <td>HTTP</td>
                                <td>Enterprise Corp</td>
                                <td>8080</td>
                                <td>0.0.0.0</td>
                                <td><span class="status-badge status-active">Running</span></td>
                                <td>2024-08-22</td>
                                <td>8</td>
                                <td>
                                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px;">Stop</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div style="margin-top: 20px;">
                        <button class="btn" onclick="showDeployHoneypot()">Deploy New Honeypot</button>
                    </div>
                `;
            }, 500);
        }

        function loadAnalytics() {
            document.getElementById('data-title').textContent = 'System Analytics';
            document.getElementById('data-content').innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: #764ba2;">2</div>
                        <div>Total Organizations</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: #667eea;">20</div>
                        <div>Total Users</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: #28a745;">2</div>
                        <div>Active Honeypots</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold; color: #dc3545;">23</div>
                        <div>Total Interactions</div>
                    </div>
                </div>
                <p>Detailed analytics and reporting features would be integrated here, showing usage patterns, threat trends, and system performance metrics.</p>
            `;
        }

        function showMessage(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            
            const container = document.querySelector('.container');
            container.insertBefore(alertDiv, container.firstChild);
            
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def serve_sessions(self):
        """Serve sessions data"""
        # Mock data for demonstration
        sessions_data = {
            "sessions": [
                {
                    "session_id": "sess_123",
                    "client_ip": "192.168.1.100",
                    "start_time": "2024-08-23T20:30:00Z",
                    "command_count": 5,
                    "max_threat_severity": "medium",
                    "last_activity": "2024-08-23T20:35:00Z",
                    "protocol": "ssh"
                },
                {
                    "session_id": "sess_124",
                    "client_ip": "10.0.0.50",
                    "start_time": "2024-08-23T20:32:00Z",
                    "command_count": 12,
                    "max_threat_severity": "high",
                    "last_activity": "2024-08-23T20:38:00Z",
                    "protocol": "http"
                }
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(sessions_data)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_session_details(self, session_id):
        """Serve session details"""
        # Mock session detail
        session_detail = {
            "session_id": session_id,
            "client_ip": "192.168.1.100",
            "protocol": "ssh",
            "start_time": "2024-08-23T20:30:00Z",
            "duration": "8 minutes",
            "threat_level": "medium",
            "status": "active",
            "command_count": 5
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(session_detail)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_alerts(self):
        """Serve alerts data"""
        alerts_data = {
            "alerts": [
                {
                    "severity": "high",
                    "message": "Multiple failed SSH login attempts detected",
                    "client_ip": "192.168.1.100",
                    "timestamp": "2024-08-23T20:35:00Z"
                },
                {
                    "severity": "medium",
                    "message": "Suspicious HTTP request pattern",
                    "client_ip": "10.0.0.50",
                    "timestamp": "2024-08-23T20:33:00Z"
                },
                {
                    "severity": "low",
                    "message": "New connection from unknown IP",
                    "client_ip": "172.16.0.25",
                    "timestamp": "2024-08-23T20:30:00Z"
                }
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(alerts_data)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_stats(self):
        """Serve statistics data"""
        stats_data = {
            "active_sessions": 2,
            "commands_processed": 17,
            "total_alerts": 8,
            "critical_alerts": 1
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(stats_data)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

class ImprovedThreatDashboard:
    """Improved Threat Dashboard with better UI and SaaS integration"""
    
    def __init__(self, port=8081):
        self.port = port
        self.server = None
        
    def start(self):
        """Start the improved dashboard server"""
        handler = lambda *args, **kwargs: ImprovedDashboardRequestHandler(
            *args, dashboard=self, **kwargs
        )
        
        self.server = HTTPServer(("0.0.0.0", self.port), handler)
        logger.info(f"Improved Threat Dashboard started at http://0.0.0.0:{self.port}")
        print(f"Improved NEXDIS Dashboard started at http://localhost:{self.port}")
        print("Press Ctrl+C to stop...")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
            self.stop()
            
    def stop(self):
        """Stop the dashboard server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

if __name__ == "__main__":
    dashboard = ImprovedThreatDashboard(port=8081)
    dashboard.start()