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
        elif path == "/student":
            self.serve_student_dashboard()
        elif path == "/leaderboard":
            self.serve_leaderboard()
        elif path == "/api/sessions":
            self.serve_sessions()
        elif path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            self.serve_session_details(session_id)
        elif path == "/api/alerts":
            self.serve_alerts()
        elif path == "/api/stats":
            self.serve_stats()
        elif path == "/api/student/points":
            self.serve_student_points()
        elif path == "/api/leaderboard":
            self.serve_leaderboard_data()
        elif path == "/api/questions":
            self.serve_questions()
        elif path.startswith("/static/"):
            self.serve_static_file(path[8:])
        else:
            self.send_error(404)
            
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/api/submit-answer":
            self.handle_answer_submission()
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
                <li><a href="/student" class="nav-link">Student Portal</a></li>
                <li><a href="/leaderboard" class="nav-link">Leaderboard</a></li>
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
        
        // Disable right-click context menu
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Disable common copy/paste keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Disable Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+X, F12
            if ((e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'a' || e.key === 'x')) || e.key === 'F12') {
                e.preventDefault();
                return false;
            }
            
            // Disable Ctrl+Shift+I (developer tools)
            if (e.ctrlKey && e.shiftKey && e.key === 'I') {
                e.preventDefault();
                return false;
            }
            
            // Disable Ctrl+U (view source)
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                return false;
            }
        });

        // Disable text selection on drag
        document.addEventListener('selectstart', function(e) {
            e.preventDefault();
        });
        
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

    def serve_student_dashboard(self):
        """Serve the student dashboard HTML"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXDIS - Student Portal</title>
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
            user-select: none; /* Prevent text selection */
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }
        
        /* Disable copy/paste */
        .no-copy {
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            pointer-events: none;
        }
        
        input, textarea {
            pointer-events: auto; /* Re-enable for input fields */
        }
        
        /* Navigation */
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
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
        
        .student-header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .student-name {
            font-size: 2rem;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .student-points {
            font-size: 3rem;
            font-weight: bold;
            color: #28a745;
            margin-bottom: 10px;
        }
        
        .points-label {
            color: #6c757d;
            font-size: 1.1rem;
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
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
        }
        
        .question {
            margin-bottom: 20px;
        }
        
        .question-text {
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: #333;
        }
        
        .options {
            list-style: none;
            margin-bottom: 15px;
        }
        
        .option {
            margin-bottom: 10px;
        }
        
        .option input {
            margin-right: 10px;
        }
        
        .option label {
            cursor: pointer;
            font-size: 1rem;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            transition: opacity 0.3s;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .result {
            margin-top: 15px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        
        .result.correct {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .result.incorrect {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .leaderboard-preview {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .leaderboard-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .leaderboard-item:last-child {
            border-bottom: none;
        }
        
        .rank {
            font-weight: bold;
            color: #667eea;
            margin-right: 15px;
        }
        
        .username {
            flex-grow: 1;
        }
        
        .points {
            font-weight: bold;
            color: #28a745;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="navbar-brand">
                🛡️ NEXDIS Student Portal
            </div>
            <ul class="nav-menu">
                <li><a href="/" class="nav-link">Dashboard</a></li>
                <li><a href="/saas" class="nav-link">SaaS Admin</a></li>
                <li><a href="/student" class="nav-link active">Student Portal</a></li>
                <li><a href="/leaderboard" class="nav-link">Leaderboard</a></li>
                <li><a href="#sessions" class="nav-link">Sessions</a></li>
                <li><a href="#alerts" class="nav-link">Alerts</a></li>
                <li><a href="#reports" class="nav-link">Reports</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <!-- Student Header -->
        <div class="student-header">
            <div class="student-name" id="student-name">Student Dashboard</div>
            <div class="student-points" id="student-points">0</div>
            <div class="points-label">Points Earned</div>
        </div>

        <!-- Main Content -->
        <div class="content-grid">
            <div class="panel">
                <div class="panel-header">
                    🧠 Cybersecurity Challenge
                </div>
                <div class="panel-content">
                    <div id="question-container">
                        <div class="loading">Loading question...</div>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    🏆 Top Performers
                </div>
                <div class="panel-content">
                    <div class="leaderboard-preview" id="leaderboard-preview">
                        <div class="loading">Loading leaderboard...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Disable right-click context menu
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Disable common copy/paste keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Disable Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+X, F12
            if ((e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'a' || e.key === 'x')) || e.key === 'F12') {
                e.preventDefault();
                return false;
            }
            
            // Disable Ctrl+Shift+I (developer tools)
            if (e.ctrlKey && e.shiftKey && e.key === 'I') {
                e.preventDefault();
                return false;
            }
            
            // Disable Ctrl+U (view source)
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                return false;
            }
        });

        // Disable text selection on drag
        document.addEventListener('selectstart', function(e) {
            e.preventDefault();
        });

        let currentQuestion = null;
        let studentPoints = 0;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadStudentPoints();
            loadQuestion();
            loadLeaderboardPreview();
        });

        function loadStudentPoints() {
            fetch('/api/student/points')
                .then(response => response.json())
                .then(data => {
                    studentPoints = data.points || 0;
                    document.getElementById('student-points').textContent = studentPoints;
                })
                .catch(error => {
                    console.error('Error loading student points:', error);
                });
        }

        function loadQuestion() {
            fetch('/api/questions')
                .then(response => response.json())
                .then(data => {
                    currentQuestion = data;
                    displayQuestion(data);
                })
                .catch(error => {
                    console.error('Error loading question:', error);
                    document.getElementById('question-container').innerHTML = '<div class="loading">Error loading question</div>';
                });
        }

        function displayQuestion(questionData) {
            const container = document.getElementById('question-container');
            const optionsHtml = questionData.options.map((option, index) => 
                `<div class="option">
                    <input type="radio" id="option${index}" name="answer" value="${index}">
                    <label for="option${index}">${option}</label>
                </div>`
            ).join('');

            container.innerHTML = `
                <div class="question">
                    <div class="question-text">${questionData.question}</div>
                    <ul class="options">
                        ${optionsHtml}
                    </ul>
                    <button class="btn" onclick="submitAnswer()">Submit Answer</button>
                    <div class="result" id="result"></div>
                </div>
            `;
        }

        function submitAnswer() {
            const selectedOption = document.querySelector('input[name="answer"]:checked');
            if (!selectedOption) {
                alert('Please select an answer');
                return;
            }

            const answerData = {
                questionId: currentQuestion.id,
                selectedAnswer: parseInt(selectedOption.value)
            };

            fetch('/api/submit-answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(answerData)
            })
            .then(response => response.json())
            .then(data => {
                const resultElement = document.getElementById('result');
                resultElement.style.display = 'block';
                
                if (data.correct) {
                    resultElement.className = 'result correct';
                    resultElement.innerHTML = `
                        <strong>Correct!</strong> ${data.explanation}<br>
                        <strong>Points earned: +${data.pointsEarned}</strong>
                    `;
                    studentPoints = data.newPoints;
                    document.getElementById('student-points').textContent = studentPoints;
                    
                    // Load new question after a delay
                    setTimeout(() => {
                        loadQuestion();
                        loadLeaderboardPreview(); // Refresh leaderboard
                    }, 2000);
                } else {
                    resultElement.className = 'result incorrect';
                    resultElement.innerHTML = `
                        <strong>Incorrect.</strong> ${data.explanation}<br>
                        The correct answer was: ${currentQuestion.options[currentQuestion.correctAnswer]}
                    `;
                    
                    // Load new question after a delay
                    setTimeout(() => {
                        loadQuestion();
                    }, 3000);
                }

                // Disable submit button
                document.querySelector('.btn').disabled = true;
            })
            .catch(error => {
                console.error('Error submitting answer:', error);
                alert('Error submitting answer. Please try again.');
            });
        }

        function loadLeaderboardPreview() {
            fetch('/api/leaderboard')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('leaderboard-preview');
                    const leaderboardHtml = data.slice(0, 5).map((user, index) => 
                        `<div class="leaderboard-item">
                            <span class="rank">#${index + 1}</span>
                            <span class="username">${user.username}</span>
                            <span class="points">${user.points}</span>
                        </div>`
                    ).join('');
                    
                    container.innerHTML = leaderboardHtml || '<div class="loading">No data available</div>';
                })
                .catch(error => {
                    console.error('Error loading leaderboard:', error);
                    document.getElementById('leaderboard-preview').innerHTML = '<div class="loading">Error loading leaderboard</div>';
                });
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        response = html.encode('utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def serve_leaderboard(self):
        """Serve the leaderboard HTML"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXDIS - Leaderboard</title>
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
            user-select: none; /* Prevent text selection */
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }
        
        /* Navigation */
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
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
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .leaderboard-header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .leaderboard-title {
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .leaderboard-subtitle {
            color: #6c757d;
            font-size: 1.1rem;
        }
        
        .leaderboard-panel {
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
        
        .leaderboard-content {
            padding: 20px;
        }
        
        .leaderboard-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background-color 0.3s;
        }
        
        .leaderboard-item:last-child {
            border-bottom: none;
        }
        
        .leaderboard-item:hover {
            background-color: #f8f9fa;
        }
        
        .leaderboard-item.top-3 {
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #333;
        }
        
        .leaderboard-item.top-3:nth-child(1) {
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        }
        
        .leaderboard-item.top-3:nth-child(2) {
            background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
        }
        
        .leaderboard-item.top-3:nth-child(3) {
            background: linear-gradient(135deg, #cd7f32 0%, #deb887 100%);
        }
        
        .rank {
            font-weight: bold;
            color: #667eea;
            margin-right: 15px;
            font-size: 1.2rem;
            min-width: 40px;
        }
        
        .top-3 .rank {
            color: #333;
        }
        
        .user-info {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        .username {
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        .user-details {
            font-size: 0.9rem;
            color: #6c757d;
        }
        
        .points {
            font-weight: bold;
            color: #28a745;
            font-size: 1.2rem;
        }
        
        .top-3 .points {
            color: #333;
        }
        
        .loading {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 20px;
        }
        
        .medal {
            margin-right: 10px;
            font-size: 1.5rem;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="navbar-brand">
                🏆 NEXDIS Leaderboard
            </div>
            <ul class="nav-menu">
                <li><a href="/" class="nav-link">Dashboard</a></li>
                <li><a href="/saas" class="nav-link">SaaS Admin</a></li>
                <li><a href="/student" class="nav-link">Student Portal</a></li>
                <li><a href="/leaderboard" class="nav-link active">Leaderboard</a></li>
                <li><a href="#sessions" class="nav-link">Sessions</a></li>
                <li><a href="#alerts" class="nav-link">Alerts</a></li>
                <li><a href="#reports" class="nav-link">Reports</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <!-- Leaderboard Header -->
        <div class="leaderboard-header">
            <div class="leaderboard-title">🏆 Top Cybersecurity Students</div>
            <div class="leaderboard-subtitle">Rankings based on challenge completion points</div>
        </div>

        <!-- Leaderboard Panel -->
        <div class="leaderboard-panel">
            <div class="panel-header">
                Current Rankings
            </div>
            <div class="leaderboard-content" id="leaderboard-content">
                <div class="loading">Loading leaderboard...</div>
            </div>
        </div>
    </div>

    <script>
        // Disable right-click context menu
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Disable common copy/paste keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Disable Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+X, F12
            if ((e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'a' || e.key === 'x')) || e.key === 'F12') {
                e.preventDefault();
                return false;
            }
            
            // Disable Ctrl+Shift+I (developer tools)
            if (e.ctrlKey && e.shiftKey && e.key === 'I') {
                e.preventDefault();
                return false;
            }
            
            // Disable Ctrl+U (view source)
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                return false;
            }
        });

        // Initialize leaderboard
        document.addEventListener('DOMContentLoaded', function() {
            loadLeaderboard();
            
            // Refresh every 30 seconds
            setInterval(loadLeaderboard, 30000);
        });

        function loadLeaderboard() {
            fetch('/api/leaderboard')
                .then(response => response.json())
                .then(data => {
                    displayLeaderboard(data);
                })
                .catch(error => {
                    console.error('Error loading leaderboard:', error);
                    document.getElementById('leaderboard-content').innerHTML = '<div class="loading">Error loading leaderboard</div>';
                });
        }

        function displayLeaderboard(leaderboardData) {
            const container = document.getElementById('leaderboard-content');
            
            if (!leaderboardData || leaderboardData.length === 0) {
                container.innerHTML = '<div class="loading">No students have earned points yet</div>';
                return;
            }
            
            const getMedal = (rank) => {
                if (rank === 1) return '🥇';
                if (rank === 2) return '🥈';
                if (rank === 3) return '🥉';
                return '';
            };
            
            const leaderboardHtml = leaderboardData.map((user, index) => {
                const rank = index + 1;
                const isTop3 = rank <= 3;
                const medal = getMedal(rank);
                
                return `
                    <div class="leaderboard-item ${isTop3 ? 'top-3' : ''}">
                        <span class="rank">${medal}#${rank}</span>
                        <div class="user-info">
                            <div class="username">${user.username}</div>
                            <div class="user-details">Challenges completed: ${user.challengesCompleted || 0}</div>
                        </div>
                        <span class="points">${user.points}</span>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = leaderboardHtml;
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        response = html.encode('utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def serve_student_points(self):
        """Serve student points data"""
        # For now, return mock data. In a real implementation, this would come from a database
        points_data = self.get_student_data()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(points_data)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_leaderboard_data(self):
        """Serve leaderboard data"""
        leaderboard_data = self.get_leaderboard_data()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(leaderboard_data)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_questions(self):
        """Serve cybersecurity questions"""
        question_data = self.get_random_question()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        response = json.dumps(question_data)
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def handle_answer_submission(self):
        """Handle answer submission"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            answer_data = json.loads(post_data.decode('utf-8'))
            
            result = self.check_answer(answer_data['questionId'], answer_data['selectedAnswer'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            response = json.dumps(result)
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            error_response = {"error": "Invalid request", "details": str(e)}
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            response = json.dumps(error_response)
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

    def get_student_data(self):
        """Get or initialize student data"""
        # In a real implementation, this would use a database
        student_file = "data/student_data.json"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        try:
            if os.path.exists(student_file):
                with open(student_file, 'r') as f:
                    return json.load(f)
        except:
            pass
            
        # Default student data
        default_data = {
            "username": "Student",
            "points": 0,
            "challengesCompleted": 0,
            "lastActivity": datetime.datetime.now().isoformat()
        }
        
        # Save default data
        try:
            with open(student_file, 'w') as f:
                json.dump(default_data, f, indent=2)
        except:
            pass
            
        return default_data

    def update_student_points(self, points_earned):
        """Update student points"""
        student_data = self.get_student_data()
        student_data['points'] += points_earned
        student_data['challengesCompleted'] += 1
        student_data['lastActivity'] = datetime.datetime.now().isoformat()
        
        # Save updated data
        try:
            with open("data/student_data.json", 'w') as f:
                json.dump(student_data, f, indent=2)
        except:
            pass
            
        # Update leaderboard
        self.update_leaderboard(student_data)
        
        return student_data

    def get_leaderboard_data(self):
        """Get leaderboard data"""
        leaderboard_file = "data/leaderboard.json"
        
        try:
            if os.path.exists(leaderboard_file):
                with open(leaderboard_file, 'r') as f:
                    leaderboard = json.load(f)
                    # Sort by points descending
                    return sorted(leaderboard, key=lambda x: x['points'], reverse=True)
        except:
            pass
            
        # Return default leaderboard with current student
        student_data = self.get_student_data()
        return [student_data] if student_data['points'] > 0 else []

    def update_leaderboard(self, student_data):
        """Update leaderboard with student data"""
        leaderboard_file = "data/leaderboard.json"
        
        try:
            if os.path.exists(leaderboard_file):
                with open(leaderboard_file, 'r') as f:
                    leaderboard = json.load(f)
            else:
                leaderboard = []
        except:
            leaderboard = []
        
        # Find and update existing entry or add new one
        found = False
        for i, entry in enumerate(leaderboard):
            if entry['username'] == student_data['username']:
                leaderboard[i] = student_data
                found = True
                break
        
        if not found:
            leaderboard.append(student_data)
        
        # Sort by points and keep top 100
        leaderboard = sorted(leaderboard, key=lambda x: x['points'], reverse=True)[:100]
        
        # Save updated leaderboard
        try:
            with open(leaderboard_file, 'w') as f:
                json.dump(leaderboard, f, indent=2)
        except:
            pass

    def get_random_question(self):
        """Get a random cybersecurity question"""
        questions = [
            {
                "id": 1,
                "question": "What is the primary purpose of a honeypot in cybersecurity?",
                "options": [
                    "To store sensitive data securely",
                    "To attract and monitor attackers",
                    "To encrypt network traffic",
                    "To backup critical systems"
                ],
                "correctAnswer": 1,
                "explanation": "A honeypot is a decoy system designed to attract and monitor attackers, allowing security professionals to study their techniques.",
                "points": 10
            },
            {
                "id": 2,
                "question": "Which of the following is NOT a common type of social engineering attack?",
                "options": [
                    "Phishing",
                    "Pretexting",
                    "Buffer overflow",
                    "Baiting"
                ],
                "correctAnswer": 2,
                "explanation": "Buffer overflow is a technical vulnerability exploitation technique, not a social engineering attack.",
                "points": 15
            },
            {
                "id": 3,
                "question": "What does SSH stand for in cybersecurity?",
                "options": [
                    "Secure Socket Handler",
                    "System Security Hub",
                    "Secure Shell",
                    "Security Service Host"
                ],
                "correctAnswer": 2,
                "explanation": "SSH stands for Secure Shell, a network protocol for secure communication between computers.",
                "points": 5
            },
            {
                "id": 4,
                "question": "Which port is commonly used for HTTPS traffic?",
                "options": [
                    "80",
                    "22",
                    "443",
                    "21"
                ],
                "correctAnswer": 2,
                "explanation": "Port 443 is the standard port for HTTPS (secure HTTP) traffic.",
                "points": 5
            },
            {
                "id": 5,
                "question": "What is the main difference between a vulnerability and an exploit?",
                "options": [
                    "There is no difference",
                    "A vulnerability is a weakness; an exploit takes advantage of it",
                    "An exploit is theoretical; a vulnerability is practical",
                    "Vulnerabilities are in hardware; exploits are in software"
                ],
                "correctAnswer": 1,
                "explanation": "A vulnerability is a security weakness or flaw, while an exploit is code or technique that takes advantage of that vulnerability.",
                "points": 20
            }
        ]
        
        # Return a random question
        import random
        return random.choice(questions)

    def check_answer(self, question_id, selected_answer):
        """Check if the submitted answer is correct"""
        # In a real implementation, you'd look up the question by ID
        # For now, we'll get a fresh question and compare (this is not ideal for production)
        questions = [
            {
                "id": 1,
                "correctAnswer": 1,
                "explanation": "A honeypot is a decoy system designed to attract and monitor attackers, allowing security professionals to study their techniques.",
                "points": 10
            },
            {
                "id": 2,
                "correctAnswer": 2,
                "explanation": "Buffer overflow is a technical vulnerability exploitation technique, not a social engineering attack.",
                "points": 15
            },
            {
                "id": 3,
                "correctAnswer": 2,
                "explanation": "SSH stands for Secure Shell, a network protocol for secure communication between computers.",
                "points": 5
            },
            {
                "id": 4,
                "correctAnswer": 2,
                "explanation": "Port 443 is the standard port for HTTPS (secure HTTP) traffic.",
                "points": 5
            },
            {
                "id": 5,
                "correctAnswer": 1,
                "explanation": "A vulnerability is a security weakness or flaw, while an exploit is code or technique that takes advantage of that vulnerability.",
                "points": 20
            }
        ]
        
        # Find question by ID
        question = None
        for q in questions:
            if q["id"] == question_id:
                question = q
                break
        
        if not question:
            return {
                "correct": False,
                "explanation": "Question not found",
                "pointsEarned": 0,
                "newPoints": self.get_student_data()['points']
            }
        
        correct = selected_answer == question["correctAnswer"]
        points_earned = question["points"] if correct else 0
        
        if correct:
            updated_student = self.update_student_points(points_earned)
            new_points = updated_student['points']
        else:
            new_points = self.get_student_data()['points']
        
        return {
            "correct": correct,
            "explanation": question["explanation"],
            "pointsEarned": points_earned,
            "newPoints": new_points
        }

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