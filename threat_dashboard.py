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
logger = logging.getLogger("ThreatDashboard")

class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the threat dashboard"""
    
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
            self.send_error(404, "Not Found")
            
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXDIS - Threat Intelligence Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
        }
        .navbar-brand {
            font-weight: bold;
            color: #fff !important;
        }
        .card {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .card-header {
            font-weight: bold;
            background-color: #f8f9fa;
            border-bottom: 1px solid #eaeaea;
        }
        .alert-info { background-color: #e3f2fd; color: #0c5460; }
        .alert-low { background-color: #d4edda; color: #155724; }
        .alert-medium { background-color: #fff3cd; color: #856404; }
        .alert-high { background-color: #f8d7da; color: #721c24; }
        .alert-critical { background-color: #dc3545; color: white; }
        
        .threat-info { color: #0c5460; }
        .threat-low { color: #155724; }
        .threat-medium { color: #856404; }
        .threat-high { color: #721c24; }
        .threat-critical { color: #dc3545; }
        
        #map-container {
            height: 300px;
            border-radius: 10px;
            overflow: hidden;
        }
        .stat-card {
            text-align: center;
            padding: 15px;
        }
        .stat-card .number {
            font-size: 2rem;
            font-weight: bold;
        }
        .stat-card .label {
            font-size: 0.9rem;
            color: #6c757d;
        }
        .timeline {
            position: relative;
            max-height: 400px;
            overflow-y: auto;
        }
        .timeline:before {
            content: '';
            position: absolute;
            left: 20px;
            top: 0;
            height: 100%;
            width: 2px;
            background: #e9ecef;
        }
        .timeline-item {
            position: relative;
            padding-left: 40px;
            padding-bottom: 20px;
        }
        .timeline-item:before {
            content: '';
            position: absolute;
            left: 16px;
            top: 0;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #6c757d;
        }
        .timeline-item.info:before { background: #17a2b8; }
        .timeline-item.low:before { background: #28a745; }
        .timeline-item.medium:before { background: #ffc107; }
        .timeline-item.high:before { background: #dc3545; }
        .timeline-item.critical:before { background: #dc3545; }
        
        .table-hover tbody tr:hover {
            background-color: rgba(0,0,0,.075);
            cursor: pointer;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class='bx bx-shield-quarter'></i> NEXDIS
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link active" href="#">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#sessions">Sessions</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#alerts">Alerts</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#reports">Reports</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <!-- Summary Stats -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="number" id="total-sessions">-</div>
                    <div class="label">Active Sessions</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="number" id="total-commands">-</div>
                    <div class="label">Commands Processed</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="number" id="total-alerts">-</div>
                    <div class="label">Total Alerts</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="number" id="critical-alerts">-</div>
                    <div class="label">Critical Alerts</div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="row">
            <!-- Left Column -->
            <div class="col-md-8">
                <!-- Recent Alerts -->
                <div class="card" id="alerts">
                    <div class="card-header">
                        <i class='bx bx-bell'></i> Recent Alerts
                    </div>
                    <div class="card-body">
                        <div class="timeline" id="alerts-timeline">
                            <div class="text-center py-3 text-muted">Loading alerts...</div>
                        </div>
                    </div>
                </div>

                <!-- Active Sessions -->
                <div class="card" id="sessions">
                    <div class="card-header">
                        <i class='bx bx-desktop'></i> Active Sessions
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
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
                                        <td colspan="5" class="text-center">Loading sessions...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column -->
            <div class="col-md-4">
                <!-- Threat Distribution -->
                <div class="card">
                    <div class="card-header">
                        <i class='bx bx-pie-chart-alt-2'></i> Threat Distribution
                    </div>
                    <div class="card-body">
                        <canvas id="threatChart" height="200"></canvas>
                    </div>
                </div>

                <!-- Top Attack Types -->
                <div class="card">
                    <div class="card-header">
                        <i class='bx bx-target-lock'></i> Top Attack Types
                    </div>
                    <div class="card-body">
                        <canvas id="attackTypesChart" height="200"></canvas>
                    </div>
                </div>

                <!-- Recent Commands -->
                <div class="card">
                    <div class="card-header">
                        <i class='bx bx-code-alt'></i> Recent Commands
                    </div>
                    <div class="card-body">
                        <ul class="list-group" id="recent-commands">
                            <li class="list-group-item text-center">Loading commands...</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Session Detail Modal -->
    <div class="modal fade" id="sessionModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Session Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" id="session-detail-content">
                    Loading session details...
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Global charts
        let threatChart;
        let attackTypesChart;
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            loadStats();
            loadSessions();
            loadAlerts();
            
            // Set up refresh interval
            setInterval(function() {
                loadStats();
                loadSessions();
                loadAlerts();
            }, 30000); // Refresh every 30 seconds
        });
        
        // Initialize charts
        function initCharts() {
            // Threat Distribution Chart
            const threatCtx = document.getElementById('threatChart').getContext('2d');
            threatChart = new Chart(threatCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Info', 'Low', 'Medium', 'High', 'Critical'],
                    datasets: [{
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: [
                            '#17a2b8',
                            '#28a745',
                            '#ffc107',
                            '#dc3545',
                            '#721c24'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // Attack Types Chart
            const attackTypesCtx = document.getElementById('attackTypesChart').getContext('2d');
            attackTypesChart = new Chart(attackTypesCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Count',
                        data: [],
                        backgroundColor: '#6c757d'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        }
        
        // Load statistics
        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-sessions').textContent = data.active_sessions;
                    document.getElementById('total-commands').textContent = data.total_commands;
                    document.getElementById('total-alerts').textContent = data.total_alerts;
                    document.getElementById('critical-alerts').textContent = data.critical_alerts;
                    
                    // Update threat distribution chart
                    threatChart.data.datasets[0].data = [
                        data.threat_distribution.info,
                        data.threat_distribution.low,
                        data.threat_distribution.medium,
                        data.threat_distribution.high,
                        data.threat_distribution.critical
                    ];
                    threatChart.update();
                    
                    // Update attack types chart
                    const attackTypes = data.attack_types;
                    const labels = Object.keys(attackTypes);
                    const values = Object.values(attackTypes);
                    
                    attackTypesChart.data.labels = labels;
                    attackTypesChart.data.datasets[0].data = values;
                    attackTypesChart.update();
                    
                    // Update recent commands
                    const commandsList = document.getElementById('recent-commands');
                    commandsList.innerHTML = '';
                    
                    data.recent_commands.forEach(cmd => {
                        const item = document.createElement('li');
                        item.className = 'list-group-item';
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="text-truncate" title="${cmd.command}">${cmd.command}</span>
                                <span class="badge text-bg-${getSeverityClass(cmd.severity)}">${cmd.severity}</span>
                            </div>
                            <small class="text-muted">${formatTimeAgo(cmd.timestamp)}</small>
                        `;
                        commandsList.appendChild(item);
                    });
                })
                .catch(error => console.error('Error loading stats:', error));
        }
        
        // Load sessions
        function loadSessions() {
            fetch('/api/sessions')
                .then(response => response.json())
                .then(data => {
                    const sessionsTable = document.getElementById('sessions-table');
                    sessionsTable.innerHTML = '';
                    
                    if (data.sessions.length === 0) {
                        sessionsTable.innerHTML = '<tr><td colspan="5" class="text-center">No active sessions</td></tr>';
                        return;
                    }
                    
                    data.sessions.forEach(session => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${session.client_ip}</td>
                            <td>${formatTime(session.start_time)}</td>
                            <td>${session.command_count}</td>
                            <td><span class="threat-${session.max_threat_severity}">${session.max_threat_severity}</span></td>
                            <td>${formatTimeAgo(session.last_activity)}</td>
                        `;
                        row.addEventListener('click', () => showSessionDetails(session.session_id));
                        sessionsTable.appendChild(row);
                    });
                })
                .catch(error => console.error('Error loading sessions:', error));
        }
        
        // Load alerts
        function loadAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    const alertsTimeline = document.getElementById('alerts-timeline');
                    alertsTimeline.innerHTML = '';
                    
                    if (data.alerts.length === 0) {
                        alertsTimeline.innerHTML = '<div class="text-center py-3 text-muted">No alerts</div>';
                        return;
                    }
                    
                    data.alerts.forEach(alert => {
                        const item = document.createElement('div');
                        item.className = `timeline-item ${alert.severity}`;
                        item.innerHTML = `
                            <div class="alert alert-${alert.severity} mb-2">
                                <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}
                            </div>
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">IP: ${alert.client_ip}</small>
                                <small class="text-muted">${formatTimeAgo(alert.timestamp)}</small>
                            </div>
                        `;
                        alertsTimeline.appendChild(item);
                    });
                })
                .catch(error => console.error('Error loading alerts:', error));
        }
        
        // Show session details
        function showSessionDetails(sessionId) {
            const modal = new bootstrap.Modal(document.getElementById('sessionModal'));
            const contentDiv = document.getElementById('session-detail-content');
            contentDiv.innerHTML = 'Loading session details...';
            modal.show();
            
            fetch(`/api/session/${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    let threatTypesHtml = '';
                    for (const [type, count] of Object.entries(