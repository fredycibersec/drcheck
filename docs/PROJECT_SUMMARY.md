# Domain Reputation Checker - Web Application
## Project Summary

### 📁 Project Structure

```
Domain-Reputation-WebApp/
├── app.py              # Flask backend server
├── templates/
│   └── index.html      # Modern, aesthetic frontend UI
├── requirements.txt    # Python dependencies
├── run.sh             # Startup script (executable)
├── README.md          # Comprehensive documentation
├── QUICKSTART.md      # Quick start guide
└── PROJECT_SUMMARY.md # This file
```

### 🎯 What This Is

A **beautiful, modern web application** that wraps the Domain Reputation Checker CLI tool with:

- **Dark-themed UI** with gradients and smooth animations
- **Real-time analysis** across multiple threat intelligence sources
- **RESTful API** for programmatic access
- **Mobile-responsive** design
- **Zero DNS queries** to the target domain (safe for OSINT)

### 🚀 Quick Start

```bash
cd /home/aramirez/pentest/OSINT/Domain-Reputation-WebApp
./run.sh
# Open browser to http://localhost:5000
```

### ✨ Key Features

#### Frontend (index.html)
- Modern dark theme with cyan/blue gradients
- Smooth animations and hover effects
- Loading spinner during analysis
- Responsive grid layout for results
- Color-coded reputation badges
- Expandable detail cards
- Direct links to source investigation tools

#### Backend (app.py)
- Flask REST API
- Integrates with original CLI tool
- Endpoints:
  - `POST /api/check` - Analyze domain
  - `GET /api/sources` - List available sources
- JSON responses
- Error handling
- CORS enabled

#### Startup Script (run.sh)
- Automatic virtual environment creation
- Dependency installation check
- API key status display
- User-friendly error messages

### 🔧 Technology Stack

- **Backend**: Python 3, Flask 2.3+
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Dependencies**: 
  - Flask
  - flask-cors
  - requests
  - python-whois
  - urllib3

### 🎨 Design Philosophy

**Modern Cybersecurity Aesthetic**
- Dark background (#0a0e27, #1a1f3a)
- Cyan primary color (#00d4ff)
- Gradient effects
- Smooth transitions
- Card-based layout
- Clean typography

**User Experience**
- Single-page application
- Instant feedback
- Clear status indicators
- Minimal clicks required
- Mobile-friendly

### 🔐 Security Features

1. **No Direct DNS Queries**
   - Uses threat intel APIs only
   - Won't trigger XDR alerts
   - Safe for investigations

2. **API Key Management**
   - Environment variable based
   - Never hardcoded
   - Optional for some sources

3. **Rate Limiting**
   - Built-in delays between requests
   - Respects API quotas

### 📊 Supported Sources

**With API Keys:**
- VirusTotal
- AbuseIPDB
- URLScan.io
- Shodan
- SecurityTrails
- IP Geolocation APIs

**Without API Keys:**
- URLVoid
- AlienVault OTX
- WHOIS Info
- Hybrid Analysis
- Multiple manual investigation tools

### 🎓 Use Cases

- **OSINT Investigations** - Quickly assess domain reputation
- **Threat Hunting** - Identify malicious domains
- **Incident Response** - Validate suspicious domains
- **Security Research** - Analyze domain patterns
- **Training** - Demonstrate threat intelligence workflows

### 📈 Performance

- **Analysis Time**: 30-60 seconds per domain
- **Concurrent Users**: Suitable for small teams
- **Caching**: Built-in (24-hour cache in CLI tool)
- **API Calls**: Optimized with rate limiting

### 🔄 How It Works

1. User enters domain in web form
2. Frontend sends POST request to `/api/check`
3. Backend calls original CLI checker
4. CLI queries multiple threat intel sources
5. Results aggregated and formatted
6. JSON response sent to frontend
7. Frontend displays in beautiful cards
8. User reviews overall reputation + details

### 🛠️ Customization Options

**Change Port:**
Edit `app.py` line 198:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

**Add New Sources:**
Extend the `sources_info` dict in `app.py`

**Modify Theme:**
Edit CSS variables in `index.html`:
```css
:root {
    --primary-color: #00d4ff;
    --background-dark: #0a0e27;
    /* ... */
}
```

**Add Features:**
- Batch domain checking
- Export results (CSV, JSON)
- Historical tracking
- Comparison views
- Notifications

### 📝 Dependencies on Original Tool

This web app requires the original CLI script:
```
../Domain-Reputation-Checker/domain_reputation_checker.py
```

**What it provides:**
- DomainReputationChecker class
- API integrations
- Result parsing
- Cache management
- Rate limiting

### 🐛 Known Limitations

1. **Single Domain Analysis**
   - No batch processing in UI yet
   - Can be added as feature

2. **No Result History**
   - Each search is independent
   - Cache exists at CLI level only

3. **API Key Input**
   - Must be set as environment variables
   - No web UI for key management

4. **Performance**
   - Analysis takes 30-60 seconds
   - Limited by API rate limits
   - No parallel source querying

### 🔮 Future Enhancements

- [ ] Batch domain upload (CSV)
- [ ] Results export functionality
- [ ] Historical analysis tracking
- [ ] API key management UI
- [ ] Real-time progress updates
- [ ] Comparison mode (multiple domains)
- [ ] Dark/light theme toggle
- [ ] User authentication
- [ ] Team collaboration features
- [ ] Webhook notifications

### 📊 Comparison with CLI Tool

| Feature | CLI Tool | Web App |
|---------|----------|---------|
| Interface | Terminal | Browser |
| Usability | Technical users | All users |
| Visualization | Text tables | Cards & badges |
| Accessibility | Command line | Any device |
| Setup | Python env | Python + browser |
| Batch processing | ✅ Yes | ❌ Not yet |
| Real-time updates | Limited | Loading indicators |
| Mobile friendly | ❌ No | ✅ Yes |

### 🎯 Target Audience

- **Security Analysts** - Quick domain checks
- **OSINT Investigators** - Reputation assessment
- **SOC Teams** - Incident triage
- **Threat Hunters** - Domain analysis
- **Security Students** - Learning tool
- **Penetration Testers** - Reconnaissance

### 💡 Tips for Best Results

1. **Set API Keys** - Get free keys from services
2. **Start Simple** - Test with known domains first
3. **Read Details** - Check individual source results
4. **Manual Review** - Use provided investigation links
5. **Cache Awareness** - CLI tool caches for 24h
6. **Rate Limits** - Respect API quotas
7. **Combine Sources** - No single source is perfect

### 📚 Additional Resources

**Documentation:**
- README.md - Full documentation
- QUICKSTART.md - Quick start guide
- Comments in source code

**API Keys:**
- VirusTotal: https://www.virustotal.com
- AbuseIPDB: https://www.abuseipdb.com
- URLScan: https://urlscan.io
- IPData: https://ipdata.co

**Learning:**
- OSINT Framework: https://osintframework.com
- Threat Intel Platforms
- Security blogs and forums

### 🤝 Contributing

To enhance this project:
1. Fork or modify the code
2. Follow Python PEP 8 style
3. Test thoroughly
4. Update documentation
5. Keep security in mind

### ⚖️ Legal & Ethics

- For authorized use only
- Respect API terms of service
- Don't abuse rate limits
- Educational purposes
- Check local laws
- Get proper authorization

### 🎉 Conclusion

This web application transforms the powerful Domain Reputation Checker CLI tool into an accessible, beautiful web interface suitable for both technical and non-technical users. Perfect for OSINT investigations, threat hunting, and security operations.

**Built for the OSINT community with ❤️**

---

**Version**: 1.0.0  
**Created**: 2026-01-23  
**Author**: Security Tools Team  
**License**: Educational Use
