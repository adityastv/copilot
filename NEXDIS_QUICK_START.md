# NEXDIS SaaS - Quick Start Guide

This quick start guide gets you up and running with NEXDIS SaaS in under 10 minutes.

## Prerequisites

- Python 3.8+ installed
- Git (to clone the repository)
- Terminal/Command prompt access

## 1. Installation & Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/adityastv/copilot.git
cd copilot

# Install dependencies
pip install -r requirements.txt
```

## 2. Start the Platform (1 minute)

Open two terminal windows:

**Terminal 1 - Start SaaS API:**
```bash
python saas_api.py --port 8889 --host 0.0.0.0
```

**Terminal 2 - Start Dashboard:**
```bash
python improved_dashboard.py
```

You should see:
```
🚀 Starting NEXDIS SaaS API...
📊 Admin credentials: admin@nexdis.io / nexdis123!
🌐 API Documentation: http://0.0.0.0:8889/api/docs
```

## 3. Access the Platform (30 seconds)

Open your web browser and navigate to:

- **Main Dashboard**: http://localhost:8081
- **SaaS Admin**: http://localhost:8081/saas
- **API Docs**: http://localhost:8889/api/docs

**Default Login**:
- Email: `admin@nexdis.io`
- Password: `nexdis123!`

## 4. Create Your First Organization (2 minutes)

### Via Web Interface:
1. Go to http://localhost:8081/saas
2. Click "Create Organization"
3. Enter organization name (e.g., "My Company")
4. Select plan (Free/Professional/Enterprise)
5. Click "Create Organization"

### Via CLI:
```bash
python saas_manager.py create-org "My Company" --plan professional
```

## 5. Deploy Your First Honeypot (2 minutes)

### Via CLI (Recommended):
```bash
# Deploy SSH honeypot (replace org_id with your organization ID)
python saas_manager.py deploy-honeypot org_my_company ssh 2222

# Deploy HTTP honeypot  
python saas_manager.py deploy-honeypot org_my_company http 8080
```

### Check Status:
```bash
python saas_manager.py status
```

You should see:
```
🛡️  NEXDIS SaaS Platform Status
==================================================
✅ SaaS API: Running

📊 Platform Summary:
   Organizations: 3  # Increased by 1
   Total Users: 3
   Active Honeypots: 4  # Increased by 2
   Total Interactions: 23+
```

## 6. Monitor Threats (2 minutes)

1. **View Dashboard**: Go to http://localhost:8081
2. **Check Active Sessions**: See real-time connections
3. **Review Alerts**: Monitor security events
4. **Analyze Statistics**: Review threat metrics

## 7. Next Steps

Now that you have NEXDIS SaaS running:

### Immediate Actions:
- [ ] Create additional users for your team
- [ ] Deploy more honeypot types (FTP, SMB)
- [ ] Configure custom ports and interfaces
- [ ] Review the comprehensive [NEXDIS SaaS User Guide](NEXDIS_SAAS_USER_GUIDE.md)

### API Integration:
```python
import requests

# Login to get token
response = requests.post('http://localhost:8889/api/auth/login', json={
    'email': 'admin@nexdis.io',
    'password': 'nexdis123!'
})
token = response.json()['data']['token']

# Get analytics
headers = {'Authorization': f'Bearer {token}'}
analytics = requests.get('http://localhost:8889/api/analytics/dashboard', headers=headers)
print(analytics.json())
```

### CLI Management:
```bash
# List all organizations
python saas_manager.py list-orgs

# Create users  
python saas_manager.py create-user user@company.com username password123 org_my_company --role user

# Deploy additional honeypots
python saas_manager.py deploy-honeypot org_my_company ftp 2121
python saas_manager.py deploy-honeypot org_my_company smb 445
```

## Troubleshooting

### API Not Starting:
```bash
# Check if port 8889 is available
netstat -tulpn | grep 8889

# Try alternative port
python saas_api.py --port 8890 --host 0.0.0.0
```

### Dashboard Not Loading:
```bash
# Check if port 8081 is available  
netstat -tulpn | grep 8081

# Access via localhost
http://127.0.0.1:8081
```

### CLI Authentication Issues:
```bash
# Test API login directly
curl -X POST http://localhost:8889/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@nexdis.io", "password": "nexdis123!"}'
```

## What You Now Have

✅ **Running NEXDIS SaaS Platform** with real threat detection  
✅ **Web Dashboard** for monitoring and management  
✅ **API Access** for automation and integration  
✅ **CLI Tools** for command-line management  
✅ **Multi-tenant Environment** ready for scaling  
✅ **Active Honeypots** capturing real security threats  

## Support

- **Complete Documentation**: [NEXDIS SaaS User Guide](NEXDIS_SAAS_USER_GUIDE.md)
- **Platform Status**: `python saas_manager.py status`  
- **API Documentation**: http://localhost:8889/api/docs

---

🎉 **Congratulations!** You now have a fully operational enterprise cybersecurity deception platform.

*Time to complete: ~7 minutes*