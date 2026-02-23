#!/usr/bin/env python3
"""
Domain Reputation Checker - Web Application
Flask backend for domain reputation analysis
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
import sys
import os
import re
import logging
from logging.handlers import RotatingFileHandler
from io import BytesIO
from datetime import datetime

# Add CLI directory to path to import the domain checker module
# Works both in Docker (cli/) and development (../Domain-Reputation-Checker/)
cli_paths = [
    os.path.join(os.path.dirname(__file__), 'cli'),  # Docker path
    os.path.join(os.path.dirname(__file__), '..', 'Domain-Reputation-Checker')  # Development path
]

for path in cli_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from domain_reputation_checker import DomainReputationChecker
except ImportError as e:
    # If import fails, we'll handle it gracefully
    print(f"Warning: Could not import DomainReputationChecker: {e}")
    DomainReputationChecker = None

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)
Compress(app)

# Configure rate limiting to prevent abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize the checker with quiet startup
checker = None

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler(
    'logs/domain_reputation.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Domain Reputation Checker startup')

# Security headers
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' http://ip-api.com https://cdn.jsdelivr.net; frame-ancestors 'none'"
    return response

def get_checker():
    """Get or initialize the domain reputation checker with API keys"""
    global checker
    if checker is None and DomainReputationChecker:
        checker = DomainReputationChecker(
            use_visual=False,
            quiet_startup=True
        )
        
        # Inject API keys from encrypted config + environment variables
        api_keys = get_api_keys()
        if api_keys:
            checker.api_keys.update(api_keys)
            app.logger.info(f'Loaded {len(api_keys)} API keys from config/environment')
    
    return checker

# Statistics tracking
import json
from pathlib import Path
from api_manager import APIKeyManager

# Initialize API manager globally
api_manager = APIKeyManager()

def get_api_keys():
    """Get API keys from encrypted config with fallback to environment variables"""
    # Load from encrypted storage
    encrypted_keys = api_manager.load_api_keys()
    
    # Environment variable mapping
    env_mapping = {
        'virustotal': 'VIRUSTOTAL_API_KEY',
        'abuseipdb': 'ABUSEIPDB_API_KEY',
        'securitytrails': 'ST_API_KEY',
        'shodan': 'SHODAN_API_KEY',
        'urlscan': 'URLSCAN_API_KEY',
        'ipapi': 'IPAPI_ACCESS_KEY',
        'ipdata': 'IPDATA_API_KEY',
        'apivoid': 'APIVOID_KEY',
        'abusech': 'ABUSECH_API_KEY',
        'pdcp': 'PDCP_API_KEY',
        'alienvault_otx': 'ALIENVAULT_API_KEY',
        'threatfox': 'THREATFOX_API_KEY'
    }
    
    # Merge: prioritize encrypted config, fallback to environment
    api_keys = {}
    for source, env_var in env_mapping.items():
        # First try encrypted storage
        if source in encrypted_keys and encrypted_keys[source]:
            api_keys[source] = encrypted_keys[source]
        # Fallback to environment variable
        else:
            env_value = os.getenv(env_var)
            if env_value:
                api_keys[source] = env_value
    
    return api_keys

STATS_FILE = Path(__file__).parent / 'stats.json'

def load_stats():
    """Load statistics from file"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'searches': [], 'summary': {'total': 0, 'domains': 0, 'ips': 0, 'hashes': 0, 'malicious': 0, 'suspicious': 0, 'clean': 0}}
    return {'searches': [], 'summary': {'total': 0, 'domains': 0, 'ips': 0, 'hashes': 0, 'malicious': 0, 'suspicious': 0, 'clean': 0}}

def save_stats(stats):
    """Save statistics to file"""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")

def get_country_from_ip(ip_address):
    """Get country from IP address using ip-api.com (free, no key required)"""
    try:
        import requests
        response = requests.get(f'http://ip-api.com/json/{ip_address}?fields=country,countryCode', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get('countryCode') or data.get('country')
    except:
        pass
    return None

def add_search_stat(search_type, target, reputation, country=None):
    """Add a search to statistics"""
    stats = load_stats()
    
    search_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': search_type,
        'target': target,
        'reputation': reputation,
        'country': country
    }
    
    stats['searches'].insert(0, search_entry)
    stats['searches'] = stats['searches'][:100]  # Keep last 100
    
    # Update summary
    stats['summary']['total'] += 1
    stats['summary'][f"{search_type}s"] = stats['summary'].get(f"{search_type}s", 0) + 1
    
    if reputation in ['malicious', 'suspicious', 'clean']:
        stats['summary'][reputation] = stats['summary'].get(reputation, 0) + 1
    
    save_stats(stats)

def sanitize_input(input_string):
    """
    Sanitize and validate input string (domain or hash)
    Returns tuple: (sanitized_string, error_message)
    """
    if not input_string:
        return None, "Input cannot be empty"
    
    # Remove whitespace and convert to lowercase
    sanitized = input_string.strip().lower()
    
    # Check length limits
    if len(sanitized) > 256:
        return None, "Input exceeds maximum length of 256 characters"
    
    if len(sanitized) < 3:
        return None, "Input is too short (minimum 3 characters)"
    
    # Remove dangerous characters for shell injection prevention
    # Allow only: alphanumeric, dots, hyphens, underscores (for domains and hashes)
    if not re.match(r'^[a-z0-9._-]+$', sanitized):
        return None, "Invalid characters detected. Only alphanumeric, dots, hyphens, and underscores are allowed"
    
    # Validate it's either a domain or hash
    # Domain pattern: letters/numbers with dots and hyphens
    domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$'
    # Hash patterns: MD5 (32), SHA1 (40), SHA256 (64)
    hash_pattern = r'^[a-f0-9]{32}$|^[a-f0-9]{40}$|^[a-f0-9]{64}$'
    
    is_domain = re.match(domain_pattern, sanitized)
    is_hash = re.match(hash_pattern, sanitized)
    
    if not is_domain and not is_hash:
        return None, "Input must be a valid domain (e.g., example.com) or hash (MD5/SHA1/SHA256)"
    
    # Additional security: block common malicious patterns
    dangerous_patterns = [
        r'\.\.',  # Directory traversal
        r'^-',    # Command injection via flags
        r'[;&|`$()]',  # Shell metacharacters
        r'<script',  # XSS attempts
        r'javascript:',  # XSS
        r'on\w+\s*=',  # Event handlers
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            return None, "Input contains potentially malicious patterns"
    
    return sanitized, None

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
@limiter.limit("10 per minute")  # Strict limit for analysis endpoint
def check_domain():
    """API endpoint to check domain reputation"""
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'error': 'Domain is required'}), 400
    
    raw_input = data['domain']
    sources = data.get('sources', None)
    
    # Sanitize and validate input
    domain, error = sanitize_input(raw_input)
    if error:
        return jsonify({'error': error}), 400
    
    # Get the checker instance
    checker_instance = get_checker()
    
    if not checker_instance:
        return jsonify({'error': 'Domain reputation checker not available'}), 500
    
    try:
        # Reset results for new check
        checker_instance.results = {}
        
        # Parse sources if provided
        if sources and sources != 'all':
            sources_list = [s.strip() for s in sources.split(',')]
        elif sources == 'all':
            sources_list = ['all']
        else:
            sources_list = None
        
        # Perform the analysis
        results = checker_instance.analyze_domain(
            domain,
            sources=sources_list,
            use_cache=False
        )
        
        # Calculate overall reputation
        overall_reputation = checker_instance.calculate_overall_reputation()
        
        # Determine if it's a hash or domain
        is_hash = re.match(r'^[a-f0-9]{32}$|^[a-f0-9]{40}$|^[a-f0-9]{64}$', domain)
        search_type = 'hash' if is_hash else 'domain'
        
        # Track statistics - get country from whois or IP resolution
        country = results.get('whois_info', {}).get('country', None)
        
        # Fallback: if no country from whois and it's a domain, try to resolve to IP and get country
        if not country and search_type == 'domain':
            try:
                import socket
                ip_addr = socket.gethostbyname(domain)
                country = get_country_from_ip(ip_addr)
            except:
                pass
        
        add_search_stat(search_type, domain, overall_reputation, country)
        
        app.logger.info(f'{search_type.capitalize()} analysis completed: {domain} - {overall_reputation}')
        
        # Format results for frontend
        formatted_results = []
        for source_id, result in results.items():
            formatted_result = {
                'source': source_id.replace('_', ' ').title(),
                'source_id': source_id,
                'status': result.get('status', 'unknown'),
                'reputation': result.get('reputation', 'unknown'),
                'message': result.get('message', ''),
                'details': {}
            }
            
            # Add source-specific details
            if result.get('status') == 'success':
                # Copy relevant fields to details
                detail_fields = [
                    'malicious', 'suspicious', 'harmless', 'undetected',
                    'pulse_count', 'detections', 'detection_rate', 'detected_by', 'total_engines',
                    'abuse_confidence', 'total_reports',
                    'ip_address', 'country', 'isp', 'age_years', 'age_days', 'age_risk',
                    'registrar', 'creation_date', 'scan_count', 'malicious_scans',
                    'suspicious_scans', 'analysis_count', 'malicious_indicators',
                    'suspicious_indicators', 'threat_indicators', 'location',
                    'open_ports', 'countries', 'additional_ips', 'geolocation_sources',
                    'services_used', 'ioc_type', 'hash_type', 'malware_detected',
                    'file_name', 'file_type', 'file_size', 'signature', 'tags', 
                    'delivery_method', 'vt_checked', 'mb_checked', 'first_seen',
                    'attack_categories', 'recent_attacks', 'engines', 'categories'
                ]
                
                for field in detail_fields:
                    if field in result:
                        value = result[field]
                        # Skip empty values EXCEPT for attack fields (show them as empty to indicate no attacks)
                        if value is None or value == '':
                            continue
                        if isinstance(value, list) and len(value) == 0:
                            # Show empty attack fields explicitly
                            if field in ['attack_categories', 'recent_attacks']:
                                formatted_result['details'][field] = []  # Include empty array
                            continue
                        
                        # Special handling for VirusTotal engines - extract malicious ones
                        if field == 'engines' and isinstance(value, dict):
                            malicious_engines = [name for name, data in value.items() 
                                               if isinstance(data, dict) and data.get('result') not in ['clean', 'unrated', None]]
                            if malicious_engines:
                                formatted_result['details']['malicious_engines'] = malicious_engines[:10]  # First 10
                            continue  # Don't add raw engines dict
                        
                        # Special handling for VirusTotal categories
                        if field == 'categories' and isinstance(value, dict):
                            # Extract non-empty categories
                            cats = [cat for cat, val in value.items() if val]
                            if cats:
                                formatted_result['details']['vt_categories'] = cats[:5]  # First 5
                            continue  # Don't add raw categories dict
                        
                        formatted_result['details'][field] = value
            
            # Add investigation URL if present
            if 'url' in result:
                formatted_result['url'] = result['url']
            
            # Add investigation workflow if present
            if 'investigation_workflow' in result:
                formatted_result['investigation_workflow'] = result['investigation_workflow']
            
            formatted_results.append(formatted_result)
        
        return jsonify({
            'domain': domain,
            'overall_reputation': overall_reputation,
            'results': formatted_results,
            'timestamp': checker_instance.results.get('timestamp', None)
        })
        
    except Exception as e:
        app.logger.error(f'Analysis failed for {domain}: {str(e)}')
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Get available sources and their status"""
    checker_instance = get_checker()
    
    if not checker_instance:
        return jsonify({'error': 'Domain reputation checker not available'}), 500
    
    sources_info = {
        'virustotal': {
            'name': 'VirusTotal',
            'description': 'Multi-engine malware scanner',
            'api_required': True,
            'available': 'virustotal' in checker_instance.available_sources['available']
        },
        'urlvoid': {
            'name': 'URLVoid',
            'description': 'URL reputation checker',
            'api_required': False,
            'available': True
        },
        'alienvault_otx': {
            'name': 'AlienVault OTX',
            'description': 'Open threat intelligence',
            'api_required': False,
            'available': True
        },
        'malware_bazaar': {
            'name': 'MalwareBazaar',
            'description': 'IoC checker (domains & hashes)',
            'api_required': False,
            'available': True
        },
        'abuseipdb': {
            'name': 'AbuseIPDB',
            'description': 'IP abuse database',
            'api_required': True,
            'available': 'abuseipdb' in checker_instance.available_sources['available']
        },
        'urlscan': {
            'name': 'URLScan.io',
            'description': 'URL scanner and analyzer',
            'api_required': True,
            'available': 'urlscan' in checker_instance.available_sources['available']
        },
        'whois_info': {
            'name': 'WHOIS Info',
            'description': 'Domain registration details',
            'api_required': False,
            'available': True
        },
        'hybrid_analysis': {
            'name': 'Hybrid Analysis',
            'description': 'Malware analysis sandbox',
            'api_required': False,
            'available': True
        }
    }
    
    return jsonify({
        'sources': sources_info,
        'available_count': len(checker_instance.available_sources['available']),
        'total_count': len(sources_info)
    })

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Generate and download PDF report"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.platypus import Image as RLImage
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        return jsonify({'error': 'PDF library not installed. Run: pip install reportlab'}), 500
    
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400
    
    try:
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#00d4ff'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0099cc'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("🛡️ Domain Reputation Analysis Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Domain and metadata
        domain = data.get('domain', 'N/A')
        overall_reputation = data.get('overall_reputation', 'unknown').upper()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get reputation emoji and color
        reputation_colors = {
            'CLEAN': colors.green,
            'MALICIOUS': colors.red,
            'SUSPICIOUS': colors.orange,
            'QUESTIONABLE': colors.orange,
            'UNKNOWN': colors.grey
        }
        rep_color = reputation_colors.get(overall_reputation, colors.grey)
        
        info_data = [
            ['Domain:', domain],
            ['Overall Reputation:', overall_reputation],
            ['Analysis Date:', timestamp],
            ['Sources Analyzed:', str(len(data.get('results', [])))]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (1, 1), (1, 1), rep_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Filter results - only include bad reports (malicious, suspicious, questionable)
        # Exclude INFO status and CLEAN reputation
        results = data.get('results', [])
        bad_results = []
        for result in results:
            status = result.get('status', 'unknown')
            reputation = result.get('reputation', 'unknown').lower()
            
            # Skip INFO sources (manual investigation)
            if status == 'info':
                continue
            
            # Skip CLEAN reputation
            if reputation == 'clean':
                continue
            
            # Include: malicious, suspicious, questionable, error, not_found
            bad_results.append(result)
        
        # Update sources count to show only bad results
        info_data[3] = ['Threat Sources Found:', str(len(bad_results))]
        
        # Check if there are any bad results
        if not bad_results:
            # Add a message that domain appears clean
            elements.append(Paragraph(
                '<para align="center"><b>✅ No Threats Detected</b><br/><br/>'
                'All analyzed sources indicate this domain is clean or no suspicious activity was found.</para>',
                styles['Normal']
            ))
        else:
            # Results by source
            elements.append(Paragraph(f'⚠️ Threat Intelligence Findings ({len(bad_results)} sources)', heading_style))
            elements.append(Spacer(1, 12))
            
            for result in bad_results:
                source_name = result.get('source', 'Unknown')
                status = result.get('status', 'unknown')
                reputation = result.get('reputation', 'unknown').upper()
                
                # Source header
                source_title = Paragraph(f"<b>{source_name}</b>", styles['Heading3'])
                elements.append(source_title)
                
                # Status and reputation
                source_data = [['Status:', status]]
                
                if status == 'success':
                    source_data.append(['Reputation:', reputation])
                    
                    # Add details
                    details = result.get('details', {})
                    for key, value in details.items():
                        label = key.replace('_', ' ').title()
                        # Format value with word wrapping using Paragraph
                        if isinstance(value, dict):
                            if key == 'location':
                                parts = []
                                if value.get('city'): parts.append(value['city'])
                                if value.get('region'): parts.append(value['region'])
                                if value.get('country'): parts.append(value['country'])
                                display_value = ', '.join(parts) if parts else 'N/A'
                            else:
                                display_value = ', '.join([f"{k}: {v}" for k, v in value.items() if v])
                        elif isinstance(value, list):
                            if key == 'recent_attacks':
                                # Special formatting for attack reports
                                display_value = f"{len(value)} attacks recorded"
                            elif len(value) == 0:
                                display_value = 'None'
                            elif len(value) <= 3:
                                display_value = ', '.join(map(str, value))
                            else:
                                display_value = f"{', '.join(map(str, value[:3]))} (+{len(value)-3} more)"
                        else:
                            display_value = str(value)
                        
                        # Wrap long text using Paragraph for better readability
                        if len(display_value) > 50:
                            display_value_para = Paragraph(
                                display_value,
                                ParagraphStyle('SmallText', parent=styles['Normal'], fontSize=8, leading=10)
                            )
                            source_data.append([f"{label}:", display_value_para])
                        else:
                            source_data.append([f"{label}:", display_value])
                elif status == 'error':
                    message = result.get('message', 'No additional information')
                    source_data.append(['Error:', message])
                elif status == 'not_found':
                    message = result.get('message', 'Not found in database')
                    source_data.append(['Note:', message])
                
                source_table = Table(source_data, colWidths=[2*inch, 4*inch])
                source_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align to top for better readability
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('WORDWRAP', (1, 0), (1, -1), True)  # Enable word wrap
                ]))
                
                elements.append(source_table)
                elements.append(Spacer(1, 15))
        
        # Footer
        elements.append(Spacer(1, 20))
        footer_text = Paragraph(
            "<i>Generated by Domain Reputation Checker - OSINT Tool</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        elements.append(footer_text)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        buffer.seek(0)
        
        # Send PDF file
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"domain-reputation-{domain}-{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/api/export-json', methods=['POST'])
def export_json():
    """Export analysis results as JSON"""
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400
    
    try:
        import json as json_module
        json_str = json_module.dumps(data, indent=2, ensure_ascii=False)
        
        response = app.response_class(
            response=json_str,
            mimetype='application/json'
        )
        response.headers['Content-Disposition'] = f'attachment; filename="reputation-{data["domain"]}-{datetime.now().strftime("%Y%m%d")}.json"'
        
        app.logger.info(f'JSON export: {data["domain"]}')
        return response
        
    except Exception as e:
        app.logger.error(f'JSON export failed: {str(e)}')
        return jsonify({'error': f'JSON export failed: {str(e)}'}), 500

@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """Export analysis results as CSV"""
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400
    
    try:
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Domain', data.get('domain', 'N/A')])
        writer.writerow(['Overall Reputation', data.get('overall_reputation', 'N/A').upper()])
        writer.writerow(['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])  # Empty row
        
        # Results header
        writer.writerow(['Source', 'Status', 'Reputation', 'Details'])
        
        # Results data
        for result in data.get('results', []):
            source = result.get('source', 'Unknown')
            status = result.get('status', 'unknown')
            reputation = result.get('reputation', 'N/A')
            
            # Combine details into a single string
            details = []
            if result.get('message'):
                details.append(result['message'])
            
            for key, value in result.get('details', {}).items():
                if value is not None and value != '':
                    label = key.replace('_', ' ').title()
                    if isinstance(value, list):
                        value = ', '.join(map(str, value))
                    details.append(f'{label}: {value}')
            
            details_str = ' | '.join(details) if details else 'N/A'
            
            writer.writerow([source, status, reputation, details_str])
        
        csv_content = output.getvalue()
        output.close()
        
        response = app.response_class(
            response=csv_content,
            mimetype='text/csv'
        )
        response.headers['Content-Disposition'] = f'attachment; filename="reputation-{data["domain"]}-{datetime.now().strftime("%Y%m%d")}.csv"'
        
        app.logger.info(f'CSV export: {data["domain"]}')
        return response
        
    except Exception as e:
        app.logger.error(f'CSV export failed: {str(e)}')
        return jsonify({'error': f'CSV export failed: {str(e)}'}), 500

@app.route('/api/check-ip', methods=['POST'])
@limiter.limit("10 per minute")
def check_ip():
    """API endpoint to check IP reputation - Simplified integrated version"""
    data = request.get_json()
    
    if not data or 'ip' not in data:
        return jsonify({'error': 'IP address is required'}), 400
    
    ip_address = data['ip'].strip()
    
    # Basic IP validation
    if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip_address):
        return jsonify({'error': 'Invalid IP address format'}), 400
    
    # Validate IP octets
    octets = ip_address.split('.')
    if not all(0 <= int(octet) <= 255 for octet in octets):
        return jsonify({'error': 'Invalid IP address range'}), 400
    
    try:
        import socket
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import json as json_module
        
        # Quick blacklist checks (top 20 most important)
        blacklists = [
            'zen.spamhaus.org',
            'bl.spamcop.net',
            'b.barracudacentral.org',
            'dnsbl.sorbs.net',
            'bl.blocklist.de',
            'spam.dnsbl.sorbs.net',
            'dnsbl-1.uceprotect.net',
            'psbl.surriel.com',
            'ubl.unsubscore.com',
            'cbl.abuseat.org',
            'dyna.spamrats.com',
            'http.dnsbl.sorbs.net',
            'misc.dnsbl.sorbs.net',
            'smtp.dnsbl.sorbs.net',
            'socks.dnsbl.sorbs.net',
            'spam.spamrats.com',
            'web.dnsbl.sorbs.net',
            'zombie.dnsbl.sorbs.net',
            'rbl.realtimeblacklist.com',
            'noptr.spamrats.com'
        ]
        
        def check_blacklist(bl_domain):
            """Check if IP is listed in blacklist"""
            reversed_ip = '.'.join(reversed(ip_address.split('.')))
            query = f"{reversed_ip}.{bl_domain}"
            try:
                socket.gethostbyname(query)
                return {'blacklist': bl_domain, 'listed': True}
            except socket.gaierror:
                return {'blacklist': bl_domain, 'listed': False}
            except Exception:
                return {'blacklist': bl_domain, 'listed': False}
        
        # Check blacklists in parallel (fast)
        blacklist_results = []
        listed_count = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_blacklist, bl): bl for bl in blacklists}
            for future in as_completed(futures):
                result = future.result()
                if result['listed']:
                    listed_count += 1
                    blacklist_results.append(result['blacklist'])
        
        # Get hostname
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
        except:
            hostname = 'No hostname'
        
        # Determine reputation
        if listed_count >= 3:
            reputation = 'malicious'
        elif listed_count >= 1:
            reputation = 'suspicious'
        else:
            reputation = 'clean'
        
        # Basic geolocation (would require API key for full data)
        # Using simple heuristics for demo
        results = {
            'blacklist_check': {
                'checked': len(blacklists),
                'listed': listed_count,
                'clean': len(blacklists) - listed_count,
                'blacklists': blacklist_results[:10] if blacklist_results else ['None']
            },
            'basic_info': {
                'ip': ip_address,
                'hostname': hostname,
                'reversed_dns': hostname if hostname != 'No hostname' else 'Not available'
            },
            'analysis': {
                'reputation_score': f"{max(0, 100 - (listed_count * 15))}/100",
                'threat_level': 'High' if listed_count >= 3 else 'Medium' if listed_count >= 1 else 'Low',
                'recommendation': 'Block' if listed_count >= 3 else 'Monitor' if listed_count >= 1 else 'Allow'
            }
        }
        
        # Track statistics - get country from IP
        country = get_country_from_ip(ip_address)
        add_search_stat('ip', ip_address, reputation, country)
        app.logger.info(f'IP analysis completed: {ip_address} - {reputation} (listed in {listed_count} blacklists) - Country: {country}')
        
        return jsonify({
            'ip': ip_address,
            'reputation': reputation,
            'results': results
        })
        
    except Exception as e:
        app.logger.error(f'IP analysis failed for {ip_address}: {str(e)}')
        return jsonify({'error': f'IP analysis failed: {str(e)}'}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """API endpoint to get statistics"""
    try:
        stats = load_stats()
        
        # Process data for frontend
        recent_searches = stats['searches'][:20]
        summary = stats['summary']
        
        # Calculate threat map data (group by country)
        threat_map = {}
        for search in stats['searches']:
            if search.get('country') and search.get('reputation') in ['malicious', 'suspicious']:
                country = search['country']
                threat_map[country] = threat_map.get(country, 0) + 1
        
        # Top threats
        top_threats = sorted(threat_map.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Reputation distribution
        reputation_dist = {
            'malicious': summary.get('malicious', 0),
            'suspicious': summary.get('suspicious', 0),
            'clean': summary.get('clean', 0)
        }
        
        return jsonify({
            'summary': summary,
            'recent_searches': recent_searches,
            'threat_map': top_threats,
            'reputation_distribution': reputation_dist
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/status', methods=['GET'])
def get_api_status():
    """Get API keys configuration status with source information"""
    try:
        # Get API keys from both sources
        encrypted_keys = api_manager.load_api_keys()
        all_keys = get_api_keys()
        
        # Environment variable mapping
        env_mapping = {
            'virustotal': 'VIRUSTOTAL_API_KEY',
            'abuseipdb': 'ABUSEIPDB_API_KEY',
            'securitytrails': 'ST_API_KEY',
            'shodan': 'SHODAN_API_KEY',
            'urlscan': 'URLSCAN_API_KEY',
            'ipapi': 'IPAPI_ACCESS_KEY',
            'ipdata': 'IPDATA_API_KEY',
            'apivoid': 'APIVOID_KEY',
            'abusech': 'ABUSECH_API_KEY',
            'alienvault_otx': 'ALIENVAULT_API_KEY',
            'threatfox': 'THREATFOX_API_KEY'
        }
        
        # Determine source for each key
        def get_key_source(source_name):
            if source_name in encrypted_keys and encrypted_keys[source_name]:
                return 'config'  # From encrypted config
            elif source_name in env_mapping and os.getenv(env_mapping[source_name]):
                return 'env'  # From environment variable
            return None
        
        # Add descriptions, tiers, and source info
        sources_info = {
            'virustotal': {'name': 'VirusTotal', 'tier': 1, 'description': '70+ motores antivirus', 'configured': bool(all_keys.get('virustotal')), 'source': get_key_source('virustotal')},
            'abuseipdb': {'name': 'AbuseIPDB', 'tier': 1, 'description': 'Reportes de abuse validados', 'configured': bool(all_keys.get('abuseipdb')), 'source': get_key_source('abuseipdb')},
            'alienvault_otx': {'name': 'AlienVault OTX', 'tier': 1, 'description': 'Threat intelligence profesional', 'configured': bool(all_keys.get('alienvault_otx')), 'source': get_key_source('alienvault_otx')},
            'urlscan': {'name': 'URLScan.io', 'tier': 2, 'description': 'Análisis automatizado de URLs', 'configured': bool(all_keys.get('urlscan')), 'source': get_key_source('urlscan')},
            'hybrid_analysis': {'name': 'Hybrid Analysis', 'tier': 2, 'description': 'Sandbox analysis', 'configured': False, 'source': None},
            'malware_bazaar': {'name': 'MalwareBazaar', 'tier': 2, 'description': 'Base de datos de malware', 'configured': bool(all_keys.get('abusech')), 'source': get_key_source('abusech')},
            'threatfox': {'name': 'ThreatFox', 'tier': 2, 'description': 'IOC database de abuse.ch', 'configured': bool(all_keys.get('threatfox')), 'source': get_key_source('threatfox')},
            'shodan': {'name': 'Shodan', 'tier': 3, 'description': 'Servicios expuestos', 'configured': bool(all_keys.get('shodan')), 'source': get_key_source('shodan')},
            'urlvoid': {'name': 'URLVoid (APIVoid)', 'tier': 3, 'description': 'Blacklists agregadas', 'configured': bool(all_keys.get('apivoid')), 'source': get_key_source('apivoid')},
            'securitytrails': {'name': 'SecurityTrails', 'tier': 3, 'description': 'Histórico DNS', 'configured': bool(all_keys.get('securitytrails')), 'source': get_key_source('securitytrails')},
            'ipapi': {'name': 'IP-API', 'tier': 4, 'description': 'Geolocalización de IPs', 'configured': bool(all_keys.get('ipapi')), 'source': get_key_source('ipapi')},
            'ipdata': {'name': 'IPData', 'tier': 4, 'description': 'Geolocalización alternativa', 'configured': bool(all_keys.get('ipdata')), 'source': get_key_source('ipdata')},
        }
        
        return jsonify({
            'sources': sources_info,
            'total_configured': len([k for k in all_keys if all_keys[k]]),
            'from_config': len([s for s in sources_info if sources_info[s]['source'] == 'config']),
            'from_env': len([s for s in sources_info if sources_info[s]['source'] == 'env'])
        })
        
    except Exception as e:
        app.logger.error(f'Error getting API status: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/get', methods=['GET'])
def get_api_config():
    """Get API keys configuration (masked for security)"""
    try:
        manager = APIKeyManager()
        api_keys = manager.load_api_keys()
        
        # Mask API keys for security (show only first/last 4 characters)
        masked_keys = {}
        for source, key in api_keys.items():
            if len(key) > 12:
                masked_keys[source] = f"{key[:4]}...{key[-4:]}"
            elif len(key) > 8:
                masked_keys[source] = f"{key[:3]}...{key[-3:]}"
            else:
                masked_keys[source] = "***configured***"
        
        return jsonify({'api_keys': masked_keys})
        
    except Exception as e:
        app.logger.error(f'Error getting API config: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/save', methods=['POST'])
def save_api_config():
    """Save API keys configuration"""
    try:
        data = request.get_json()
        
        if not data or 'api_keys' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        manager = APIKeyManager()
        success = manager.save_api_keys(data['api_keys'])
        
        if success:
            app.logger.info('API keys configuration updated successfully')
            return jsonify({
                'success': True,
                'message': 'API keys guardadas correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al guardar las API keys'
            }), 500
        
    except Exception as e:
        app.logger.error(f'Error saving API config: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/verify', methods=['GET'])
def verify_api_keys():
    """Verify all configured API keys from both config and environment"""
    try:
        # Get API keys from both sources
        encrypted_keys = api_manager.load_api_keys()
        all_keys = get_api_keys()
        
        # Environment variable mapping
        env_mapping = {
            'virustotal': 'VIRUSTOTAL_API_KEY',
            'abuseipdb': 'ABUSEIPDB_API_KEY',
            'securitytrails': 'ST_API_KEY',
            'shodan': 'SHODAN_API_KEY',
            'urlscan': 'URLSCAN_API_KEY',
            'ipapi': 'IPAPI_ACCESS_KEY',
            'ipdata': 'IPDATA_API_KEY',
            'apivoid': 'APIVOID_KEY',
            'abusech': 'ABUSECH_API_KEY',
            'alienvault_otx': 'ALIENVAULT_API_KEY',
            'threatfox': 'THREATFOX_API_KEY'
        }
        
        # Check environment variables
        env_keys = {}
        for source, env_var in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                env_keys[source] = {
                    'env_var': env_var,
                    'masked_value': f"{value[:4]}...{value[-4:]}" if len(value) > 12 else "***",
                    'length': len(value)
                }
        
        # Check config file keys
        config_keys = {}
        for source, key in encrypted_keys.items():
            if key:
                config_keys[source] = {
                    'masked_value': f"{key[:4]}...{key[-4:]}" if len(key) > 12 else "***",
                    'length': len(key)
                }
        
        # Combined result
        verification_result = {
            'environment_variables': env_keys,
            'config_file': config_keys,
            'total_env': len(env_keys),
            'total_config': len(config_keys),
            'total_unique': len(all_keys),
            'sources_priority': 'Config file takes priority over environment variables'
        }
        
        app.logger.info(f'API verification: {len(all_keys)} unique keys found ({len(config_keys)} from config, {len(env_keys)} from env)')
        
        return jsonify(verification_result)
        
    except Exception as e:
        app.logger.error(f'Error verifying API keys: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🛡️  Domain Reputation Checker - Web Application")
    print("=" * 60)
    print("Starting Flask server...")
    print("Access the web interface at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=5000)

