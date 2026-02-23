# How to Restart the Webapp to See Attack Reports

## ✅ Attack Reports Are Working!

The test confirms that AbuseIPDB now returns detailed attack information:
- ✅ **7 attack categories** detected
- ✅ **10 recent attacks** with dates, categories, and comments
- ✅ Data includes: Port Scan, Hacking, Brute-Force, SSH, etc.

## 🔄 You Need to Restart the Webapp

The webapp loads the CLI module when it starts. Since we updated the CLI code, you need to restart the webapp to see the new attack reports.

### Option 1: Restart via Ctrl+C (if running in terminal)

If the webapp is running in your terminal:

```bash
# Press Ctrl+C to stop it
# Then restart:
cd /home/aramirez/pentest/OSINT/Domain-Reputation-WebApp
python3 app.py
```

### Option 2: Restart systemd service (if deployed)

If you deployed it as a service:

```bash
sudo systemctl restart domain-reputation
```

### Option 3: Restart Docker container (if using Docker)

```bash
docker restart domain-reputation
```

## 🧪 Test After Restart

1. **Access the webapp**: http://localhost:5000
2. **Search for a domain**: Try `google.com` or any domain
3. **Check AbuseIPDB section**: You should now see:
   - Attack Categories (list of attack types)
   - Recent Attacks (with dates and comments)

### What You'll See:

```
AbuseIPDB
✅ SUCCESS

Details:
• Abuse Confidence: 0%
• Total Reports: 14
• Attack Categories: Port Scan, Hacking, Brute-Force, SSH, Web App Attack, Exploited Host, Fraud VoIP
• Recent Attacks:
  - 2026-01-22: [Port Scan, Hacking, Exploited Host] - Unauthorized connection attempt
  - 2026-01-20: [Port Scan, Hacking, Exploited Host] - Unauthorized connection attempt
  - 2026-01-20: [Fraud VoIP, Port Scan, Hacking, Brute-Force] - Detected port scanning activity...
  ... and 7 more
```

## 📊 When Attack Reports Appear

Attack details are fetched when:
- ✅ **Any reports exist** (even if confidence is 0%)
- ✅ **OR confidence ≥ 25%** (suspicious/malicious)

This means:
- Google DNS (14 reports, 0% confidence): **Shows attack details** ✅
- Clean IPs (0 reports): **No extra API call** (faster)
- Malicious IPs (high confidence): **Full attack details** ✅

## 🎯 Benefits

With attack reports, you now get:
- **Attack Timeline**: When attacks occurred
- **Attack Types**: Port Scan, Brute-Force, Phishing, DDoS, etc.
- **Context**: Comments describing the attacks
- **Patterns**: See if multiple attack types from same IP
- **Severity**: Understand the threat level better

## ✅ Verification

After restarting, you can verify it's working:

1. Open browser to webapp
2. Search any domain (e.g., `google.com`)
3. Look at AbuseIPDB section
4. You should see `attack_categories` and `recent_attacks` in the details

If you don't see them, check:
- Webapp was properly restarted (check logs)
- AbuseIPDB API key is valid (`echo $ABUSEIPDB_API_KEY`)
- Network connectivity to AbuseIPDB API

## 🐛 Troubleshooting

### Not seeing attack reports?

1. **Restart the webapp** (most common issue)
2. **Check API key**: `echo $ABUSEIPDB_API_KEY`
3. **Run test script**: `python3 test_attack_reports.py`
4. **Check browser console** for errors

### Test from command line:

```bash
cd /home/aramirez/pentest/OSINT/Domain-Reputation-Checker
python3 domain_reputation_checker.py --sources abuseipdb google.com
```

Should show attack categories in the output.

## 📝 Summary

**Status**: ✅ Attack reports are working in the CLI
**Action needed**: 🔄 Restart the webapp to see them in the web interface
**Expected result**: Attack categories and recent attacks shown for AbuseIPDB results

**Restart now to see the new attack intelligence!**
