# 🚀 Quick Start Guide

Get the Domain Reputation Checker web app running in 3 easy steps!

## Step 1: Install Dependencies

```bash
cd /home/aramirez/pentest/OSINT/Domain-Reputation-WebApp
pip install -r requirements.txt
```

## Step 2: Launch the Application

**Option A: Using the startup script (Recommended)**
```bash
./run.sh
```

**Option B: Direct Python execution**
```bash
python3 app.py
```

## Step 3: Open Your Browser

Navigate to: **http://localhost:5000**

That's it! 🎉

---

## First-Time Use

1. **Enter a domain** in the search box (e.g., `google.com`, `github.com`)
2. **Click "Check Reputation"**
3. **Wait** for the analysis (30-60 seconds)
4. **Review results** from multiple threat intelligence sources

---

## Pro Tips

### 🔑 Add API Keys for More Sources

Set environment variables before launching:

```bash
# Add your API keys
export VIRUSTOTAL_API_KEY="your_key_here"
export ABUSEIPDB_API_KEY="your_key_here"
export URLSCAN_API_KEY="your_key_here"

# Then launch the app
./run.sh
```

### 📋 Where to Get API Keys

- **VirusTotal**: https://www.virustotal.com/gui/join-us
- **AbuseIPDB**: https://www.abuseipdb.com/register
- **URLScan.io**: https://urlscan.io/user/signup
- **IP-API**: https://members.ip-api.com/
- **IPData**: https://ipdata.co/sign-up.html

Most offer free tiers! 🆓

### 🎯 Example Domains to Try

**Clean Domains:**
- google.com
- github.com
- microsoft.com

**For Testing (Known Malicious - BE CAREFUL):**
- Use test domains from threat intel feeds
- Never visit malicious domains directly!

---

## Troubleshooting

### ❌ "Port 5000 already in use"

Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### ❌ "Module not found: domain_reputation_checker"

Make sure the original CLI script exists at:
```
../Domain-Reputation-Checker/domain_reputation_checker.py
```

### ❌ "No sources available"

Some sources work without API keys! But for full functionality, add API keys (see above).

---

## Features Overview

✅ **Multi-Source Analysis**
- VirusTotal, URLVoid, AlienVault OTX
- AbuseIPDB, URLScan.io, WHOIS
- Hybrid Analysis, and more!

✅ **Safe Operation**
- No direct DNS queries
- Won't trigger XDR alerts

✅ **Beautiful UI**
- Dark theme
- Real-time updates
- Mobile responsive

✅ **Detailed Results**
- Overall reputation score
- Per-source breakdown
- Investigation links

---

## Need Help?

1. Check the full [README.md](README.md)
2. Review error messages in the terminal
3. Verify API keys are set correctly
4. Ensure all dependencies are installed

---

**Happy Hunting! 🔍🛡️**
