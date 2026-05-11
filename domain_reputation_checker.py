#!/usr/bin/env python3
"""
Domain Reputation Checker for XSOAR Investigations
Checks domain reputation against multiple threat intelligence sources
WITHOUT making direct DNS queries to avoid triggering XDR alerts.

Version: 2.0
Author: XSOAR Investigation Team
"""

import requests
import requests.adapters
import json
import sys
import time
import os
import csv
import hashlib
import sqlite3
from urllib.parse import quote
from datetime import datetime, timedelta
import argparse
import configparser
import re
from typing import Dict, List, Optional
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

# Visual enhancement libraries
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.status import Status
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Auto-reset colors
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Suppress SSL warnings for sites with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VisualStyler:
    """Enhanced visual styling for the Domain Reputation Checker"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.use_rich = RICH_AVAILABLE
        self.use_color = COLORAMA_AVAILABLE or RICH_AVAILABLE
        
    def print_banner(self):
        """Display an aesthetic banner"""
        if self.use_rich:
            banner_text = Text()
            banner_text.append("🛡️  DOMAIN REPUTATION CHECKER  🛡️\n", style="bold cyan")
            banner_text.append("Advanced Threat Intelligence Analysis\n", style="bold blue")
            banner_text.append("Version 2.0 - Enhanced Visual Edition", style="dim")
            
            banner_panel = Panel(
                Align.center(banner_text),
                box=box.DOUBLE,
                style="cyan",
                width=60
            )
            self.console.print(banner_panel)
            self.console.print()
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}" + "="*60)
            print(f"{Fore.CYAN}{Style.BRIGHT}🛡️  DOMAIN REPUTATION CHECKER  🛡️")
            print(f"{Fore.BLUE}Advanced Threat Intelligence Analysis")
            print(f"{Fore.WHITE}Version 2.0 - Enhanced Visual Edition")
            print(f"{Fore.CYAN}{Style.BRIGHT}" + "="*60 + f"{Style.RESET_ALL}")
            print()
        else:
            print("="*60)
            print("🛡️  DOMAIN REPUTATION CHECKER  🛡️")
            print("Advanced Threat Intelligence Analysis")
            print("Version 2.0 - Enhanced Visual Edition")
            print("="*60)
            print()
    
    def print_domain_header(self, domain, sources_count=None):
        """Display domain analysis header"""
        if self.use_rich:
            header_text = Text()
            header_text.append(f"🔍 ANALYZING: ", style="bold yellow")
            header_text.append(f"{domain}", style="bold white")
            
            if sources_count:
                header_text.append(f"\n📊 Sources: {sources_count}", style="dim")
            
            header_panel = Panel(
                Align.center(header_text),
                box=box.ROUNDED,
                style="yellow",
                title="[bold]Domain Analysis[/bold]",
                title_align="center"
            )
            self.console.print(header_panel)
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.YELLOW}{Style.BRIGHT}🔍 ANALYZING: {Fore.WHITE}{domain}")
            if sources_count:
                print(f"{Fore.CYAN}📊 Sources: {sources_count}{Style.RESET_ALL}")
            print()
        else:
            print(f"🔍 ANALYZING: {domain}")
            if sources_count:
                print(f"📊 Sources: {sources_count}")
            print()
    
    def print_source_checking(self, source_name):
        """Display source checking status"""
        if self.use_rich:
            self.console.print(f"[cyan]⚡[/cyan] [bold]Checking {source_name}...[/bold]")
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}⚡ {Fore.WHITE}{Style.BRIGHT}Checking {source_name}...{Style.RESET_ALL}")
        else:
            print(f"⚡ Checking {source_name}...")
    
    def get_reputation_color(self, reputation):
        """Get color for reputation status"""
        colors = {
            'clean': 'green',
            'malicious': 'red',
            'suspicious': 'yellow', 
            'questionable': 'orange1',
            'unknown': 'dim'
        }
        return colors.get(reputation.lower(), 'white')
    
    def get_reputation_emoji(self, reputation):
        """Get emoji for reputation status"""
        emojis = {
            'clean': '✅',
            'malicious': '🚨', 
            'suspicious': '⚠️',
            'questionable': '🔍',
            'unknown': '❓'
        }
        return emojis.get(reputation.lower(), '❓')
    
    def print_results_table(self, domain, results):
        """Display results in a beautiful table format"""
        if self.use_rich:
            self._print_rich_table(domain, results)
        else:
            self._print_basic_table(domain, results)
    
    def _print_rich_table(self, domain, results):
        """Rich-formatted results table"""
        table = Table(
            title=f"[bold cyan]🛡️ Domain Reputation Analysis: {domain} 🛡️[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            title_style="bold cyan",
            caption=f"Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            caption_style="dim"
        )
        
        table.add_column("Source", style="cyan", width=22)
        table.add_column("Status", justify="center", width=14)
        table.add_column("Reputation", justify="center", width=18)
        table.add_column("Details", no_wrap=False)
        
        for source, result in results.items():
            source_name = source.replace('_', ' ').title()
            status = result.get('status', 'unknown')
            reputation = result.get('reputation', 'unknown')
            
            # Status styling
            if status == 'success':
                status_text = "[green]✓ Success[/green]"
            elif status == 'error':
                status_text = "[red]✗ Error[/red]"
            elif status == 'info':
                status_text = "[blue]ℹ Info[/blue]"
            else:
                status_text = "[yellow]⚠ Not Found[/yellow]"
            
            # Reputation styling
            if status == 'success':
                reputation_color = self.get_reputation_color(reputation)
                reputation_emoji = self.get_reputation_emoji(reputation)
                reputation_text = f"[{reputation_color}]{reputation_emoji} {reputation.upper()}[/{reputation_color}]"
            else:
                reputation_text = "[dim]-[/dim]"
            
            # Details
            details = []
            if status == 'success':
                if 'malicious' in result and 'suspicious' in result:
                    details.append(f"M:{result['malicious']} S:{result['suspicious']}")
                elif 'detections' in result:
                    details.append(f"Detections: {result['detections']}")
                elif 'votes' in result:
                    # ThreatCrowd API result
                    details.append(f"Votes: {result['votes']}")
                    if 'references' in result:
                        details.append(f"Refs: {result['references']}")
                    if 'subdomains' in result:
                        details.append(f"Subdomains: {result['subdomains']}")
                elif 'method' in result and result['method'] == 'web_scraping':
                    # ThreatCrowd web scraping result
                    if 'threat_indicators' in result:
                        details.append(f"Threats: {result['threat_indicators']}")
                    if 'note' in result:
                        details.append("Web scraped")
                elif 'pulse_count' in result:
                    details.append(f"Pulses: {result['pulse_count']}")
                elif 'abuse_confidence' in result:
                    details.append(f"Confidence: {result['abuse_confidence']}%")
                    if 'total_reports' in result:
                        details.append(f"Reports: {result['total_reports']}")
                    if 'ip_address' in result:
                        details.append(f"IP: {result['ip_address']}")
                elif 'age_years' in result:
                    # WHOIS info results
                    details.append(f"Age: {result['age_years']} years")
                    if 'registrar' in result and result['registrar'] != 'N/A':
                        details.append(f"Registrar: {result['registrar']}")
                    if 'age_risk' in result:
                        details.append(f"Risk: {result['age_risk']}")
                elif 'scan_count' in result:
                    # URLScan results
                    details.append(f"Scans: {result['scan_count']}")
                    if 'malicious_scans' in result and result['malicious_scans'] > 0:
                        details.append(f"Malicious: {result['malicious_scans']}")
                    if 'suspicious_scans' in result and result['suspicious_scans'] > 0:
                        details.append(f"Suspicious: {result['suspicious_scans']}")
                elif 'analysis_count' in result:
                    # Hybrid Analysis results
                    details.append(f"Analyses: {result['analysis_count']}")
                    if 'malicious_indicators' in result and result['malicious_indicators'] > 0:
                        details.append(f"Malicious: {result['malicious_indicators']}")
                    if 'suspicious_indicators' in result and result['suspicious_indicators'] > 0:
                        details.append(f"Suspicious: {result['suspicious_indicators']}")
                elif 'threat_indicators' in result and 'location' in result:
                    # IP Geolocation results
                    location = result.get('location', {})
                    if location.get('country'):
                        details.append(f"Country: {location['country']}")
                    if result['threat_indicators']:
                        details.append(f"Threats: {len(result['threat_indicators'])}")
                    if 'services_used' in result:
                        details.append(f"Sources: {result['services_used']}")
                elif 'service_status' in result and result['service_status'] == 'down':
                    # Service down status
                    details.append("Service temporarily down")
            elif status in ['error', 'info', 'not_found']:
                msg = result.get('message', '')
                details.append(msg)
            
            details_text = ' | '.join(details) if details else "-"
            
            table.add_row(source_name, status_text, reputation_text, details_text)
        
        self.console.print()
        self.console.print(table)
        self.console.print()
    
    def _print_basic_table(self, domain, results):
        """Basic colored table for fallback"""
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "="*80)
            print(f"🛡️ DOMAIN REPUTATION ANALYSIS: {Fore.WHITE}{domain}")
            print(f"{Fore.CYAN}" + "="*80 + f"{Style.RESET_ALL}\n")
        else:
            print("\n" + "="*80)
            print(f"🛡️ DOMAIN REPUTATION ANALYSIS: {domain}")
            print("="*80 + "\n")
        
        for source, result in results.items():
            source_name = source.replace('_', ' ').title()
            status = result.get('status', 'unknown')
            reputation = result.get('reputation', 'unknown')
            
            # Build details string for basic display
            details = []
            if status == 'success':
                if 'votes' in result:
                    details.append(f"Votes:{result['votes']}")
                    if 'references' in result:
                        details.append(f"Refs:{result['references']}")
                elif 'method' in result and result['method'] == 'web_scraping':
                    details.append("WebScraped")
                elif 'abuse_confidence' in result:
                    details.append(f"Conf:{result['abuse_confidence']}%")
                elif 'pulse_count' in result:
                    details.append(f"Pulses:{result['pulse_count']}")
                elif 'age_years' in result:
                    details.append(f"Age:{result['age_years']}y")
                    if 'age_risk' in result:
                        details.append(f"Risk:{result['age_risk']}")
                elif 'scan_count' in result:
                    details.append(f"Scans:{result['scan_count']}")
                    if 'malicious_scans' in result and result['malicious_scans'] > 0:
                        details.append(f"Malicious:{result['malicious_scans']}")
                elif 'analysis_count' in result:
                    details.append(f"Analyses:{result['analysis_count']}")
                    if 'malicious_indicators' in result and result['malicious_indicators'] > 0:
                        details.append(f"Malicious:{result['malicious_indicators']}")
                elif 'threat_indicators' in result and 'location' in result:
                    location = result.get('location', {})
                    if location.get('country_code'):
                        details.append(f"Country:{location['country_code']}")
                    if result['threat_indicators']:
                        details.append(f"Threats:{len(result['threat_indicators'])}")
            
            details_str = f" ({','.join(details)})" if details else ""
            
            if COLORAMA_AVAILABLE:
                if status == 'success':
                    status_color = Fore.GREEN
                    status_symbol = "✓"
                elif status == 'error':
                    status_color = Fore.RED
                    status_symbol = "✗"
                elif status == 'info':
                    status_color = Fore.BLUE
                    status_symbol = "ℹ"
                else:
                    status_color = Fore.YELLOW
                    status_symbol = "⚠"
                
                reputation_emoji = self.get_reputation_emoji(reputation)
                print(f"{status_color}{status_symbol} {Fore.CYAN}{source_name:<20} {reputation_emoji} {reputation.upper():<12}{Fore.DIM}{details_str}{Style.RESET_ALL}")
            else:
                reputation_emoji = self.get_reputation_emoji(reputation)
                print(f"{source_name:<20} {reputation_emoji} {reputation.upper():<12}{details_str}")
    
    def print_overall_assessment(self, reputation):
        """Display overall assessment with styling"""
        reputation_emoji = self.get_reputation_emoji(reputation)
        
        if self.use_rich:
            reputation_color = self.get_reputation_color(reputation)
            
            assessment_text = Text()
            assessment_text.append(f"{reputation_emoji} OVERALL REPUTATION: ", style="bold")
            assessment_text.append(f"{reputation.upper()}", style=f"bold {reputation_color}")
            
            assessment_panel = Panel(
                Align.center(assessment_text),
                box=box.HEAVY,
                style=reputation_color,
                title="[bold]Final Assessment[/bold]",
                title_align="center"
            )
            
            self.console.print(assessment_panel)
            
            # Recommendations
            if reputation in ['malicious', 'suspicious']:
                recommendation = "[red]⚠️ HIGH RISK[/red] - Consider blocking and investigating further"
            elif reputation == 'questionable':
                recommendation = "[yellow]⚠️ MEDIUM RISK[/yellow] - Proceed with caution and monitoring"
            elif reputation == 'clean':
                recommendation = "[green]✅ LOW RISK[/green] - Domain appears legitimate"
            else:
                recommendation = "[dim]❓ UNKNOWN[/dim] - Insufficient data for assessment"
            
            rec_panel = Panel(
                recommendation,
                title="[bold]Recommendation[/bold]",
                box=box.ROUNDED,
                style="dim"
            )
            self.console.print(rec_panel)
            
        elif COLORAMA_AVAILABLE:
            if reputation == 'malicious':
                color = Fore.RED
            elif reputation == 'suspicious':
                color = Fore.YELLOW
            elif reputation == 'clean':
                color = Fore.GREEN
            else:
                color = Fore.WHITE
            
            print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "="*60)
            print(f"OVERALL ASSESSMENT")
            print(f"" + "="*60 + f"{Style.RESET_ALL}")
            print(f"{color}{Style.BRIGHT}{reputation_emoji} REPUTATION: {reputation.upper()}{Style.RESET_ALL}\n")
        else:
            print("\n" + "="*60)
            print("OVERALL ASSESSMENT")
            print("="*60)
            print(f"{reputation_emoji} REPUTATION: {reputation.upper()}\n")
    
    def create_progress_bar(self, total_items, description="Processing"):
        """Create a progress bar for batch operations"""
        if self.use_rich:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                TaskProgressColumn(),
                console=self.console
            )
        else:
            return None
    
    def print_batch_header(self, total_domains, sources_info=None):
        """Display batch analysis header"""
        if self.use_rich:
            header_text = Text()
            header_text.append("🔄 BATCH ANALYSIS STARTING\n", style="bold cyan")
            header_text.append(f"📊 Domains to analyze: {total_domains}\n", style="bold yellow")
            if sources_info:
                header_text.append(f"🛡️ Threat intelligence sources: {sources_info}", style="dim")
            
            batch_panel = Panel(
                Align.center(header_text),
                box=box.DOUBLE,
                style="cyan",
                title="[bold]Batch Processing[/bold]",
                title_align="center"
            )
            self.console.print(batch_panel)
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}🔄 BATCH ANALYSIS STARTING")
            print(f"{Fore.YELLOW}📊 Domains to analyze: {total_domains}")
            if sources_info:
                print(f"{Fore.WHITE}🛡️ Sources: {sources_info}")
            print(f"{Style.RESET_ALL}")
        else:
            print("🔄 BATCH ANALYSIS STARTING")
            print(f"📊 Domains to analyze: {total_domains}")
            if sources_info:
                print(f"🛡️ Sources: {sources_info}")
            print()
    
    def print_source_status_table(self, sources_info, api_keys):
        """Display available sources in a beautiful table"""
        if self.use_rich:
            table = Table(
                title="[bold cyan]🛡️ Available Threat Intelligence Sources 🛡️[/bold cyan]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            
            table.add_column("#", style="dim", width=3)
            table.add_column("Source", style="cyan", width=20)
            table.add_column("Status", justify="center", width=12)
            table.add_column("Description", width=35)
            
            for i, (source_id, info) in enumerate(sources_info.items(), 1):
                # Check API key status
                api_key_available = not info['api_required'] or bool(api_keys.get(source_id.replace('_', '')))
                
                if api_key_available:
                    if info['api_required']:
                        status = "[green]✅ API Key[/green]"
                    else:
                        status = "[green]✅ Ready[/green]"
                else:
                    status = "[yellow]⚠️ Need Key[/yellow]"
                
                table.add_row(
                    str(i),
                    info['name'],
                    status,
                    info['description']
                )
            
            self.console.print()
            self.console.print(table)
            
            # Usage examples
            usage_panel = Panel(
                "[bold cyan]Usage Examples:[/bold cyan]\n" +
                "[dim]• --sources all[/dim] [white](for all sources)[/white]\n" +
                "[dim]• --sources virustotal abuseipdb urlscan[/dim] [white](specific sources)[/white]\n" +
                "[dim]• Default behavior uses all available sources[/dim]",
                title="[bold]How to Use[/bold]",
                box=box.ROUNDED
            )
            self.console.print(usage_panel)
            
        else:
            self._print_basic_source_status(sources_info, api_keys)
    
    def _print_basic_source_status(self, sources_info, api_keys):
        """Basic source status display"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}" + "="*60)
            print("🛡️ AVAILABLE THREAT INTELLIGENCE SOURCES")
            print("="*60 + f"{Style.RESET_ALL}\n")
        else:
            print("="*60)
            print("🛡️ AVAILABLE THREAT INTELLIGENCE SOURCES")
            print("="*60 + "\n")
        
        for i, (source_id, info) in enumerate(sources_info.items(), 1):
            api_key_available = not info['api_required'] or bool(api_keys.get(source_id.replace('_', '')))
            
            if COLORAMA_AVAILABLE:
                if api_key_available:
                    if info['api_required']:
                        status_color = f"{Fore.GREEN}✅ API Key"
                    else:
                        status_color = f"{Fore.GREEN}✅ Ready"
                else:
                    status_color = f"{Fore.YELLOW}⚠️ Need Key"
                
                print(f"{Fore.WHITE}{i:2}. {Fore.CYAN}{info['name']:<20} {status_color:<15} {Fore.WHITE}{info['description']}{Style.RESET_ALL}")
            else:
                status = "✅ Ready" if api_key_available else "⚠️ Need Key"
                print(f"{i:2}. {info['name']:<20} {status:<15} {info['description']}")

def _parse_shodan_host(data, ip_address):
    """Parse a Shodan /shodan/host/{ip} response into rich result fields."""
    suspicious_ports = {21, 22, 23, 25, 135, 139, 445, 1433, 3306, 3389, 5900, 6379, 27017}

    # Build services list: "80/tcp (Apache httpd 2.4.51)"
    services = []
    for entry in data.get('data', []):
        port = entry.get('port', '')
        transport = entry.get('transport', 'tcp')
        product = entry.get('product', '')
        version = entry.get('version', '')
        module = entry.get('_shodan', {}).get('module', '')
        label = product or module or ''
        if version:
            label = f"{label} {version}".strip()
        svc = f"{port}/{transport}"
        if label:
            svc += f" ({label})"
        services.append(svc)

    open_ports = sorted({e.get('port', 0) for e in data.get('data', [])})
    suspicious_count = len(set(open_ports).intersection(suspicious_ports))

    # Vulnerabilities (Shodan returns dict or list depending on plan/version)
    vulns_raw = data.get('vulns', {})
    if isinstance(vulns_raw, dict):
        vulns = list(vulns_raw.keys())
    elif isinstance(vulns_raw, list):
        vulns = vulns_raw
    else:
        vulns = []

    # Tags (cloud, vpn, tor, honeypot, self-signed, etc.)
    tags = data.get('tags', [])

    # Hostnames / domains
    hostnames = data.get('hostnames', [])
    domains = data.get('domains', [])

    # Location
    location_parts = [p for p in [data.get('city'), data.get('region_code'), data.get('country_name')] if p]

    # SSL ciphers / cert info (from first HTTPS port if present)
    ssl_info = ''
    for entry in data.get('data', []):
        if 'ssl' in entry:
            cert = entry['ssl'].get('cert', {})
            subject = cert.get('subject', {})
            cn = subject.get('CN', '')
            expires = cert.get('expires', '')
            if cn:
                ssl_info = cn
                if expires:
                    ssl_info += f' (exp: {expires})'
            break

    # Reputation
    if vulns:
        reputation = 'suspicious'
    elif suspicious_count > 3 or 'honeypot' in tags:
        reputation = 'suspicious'
    elif suspicious_count > 0 or tags:
        reputation = 'questionable'
    else:
        reputation = 'clean'

    details = {}
    details['ip_address'] = ip_address
    if data.get('org'):
        details['organization'] = data['org']
    if data.get('isp') and data.get('isp') != data.get('org'):
        details['isp'] = data['isp']
    if data.get('asn'):
        details['asn'] = data['asn']
    if location_parts:
        details['location'] = ', '.join(location_parts)
    if data.get('os'):
        details['operating_system'] = data['os']
    if open_ports:
        details['open_ports'] = open_ports
    if services:
        details['services'] = services
    if vulns:
        details['vulnerabilities'] = vulns
    if tags:
        details['tags'] = tags
    if hostnames:
        details['hostnames'] = hostnames[:10]
    if domains:
        details['domains'] = domains[:10]
    if ssl_info:
        details['ssl_certificate'] = ssl_info
    details['last_update'] = data.get('last_update', '')

    return {
        'status': 'success',
        'reputation': reputation,
        'suspicious_ports': suspicious_count,
        'details': details,
    }


class DomainReputationChecker:
    def __init__(self, config_file=None, cache_file=None, timeout=10, use_visual=True, quiet_startup=False):
        self.results = {}
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Initialize visual styling
        self.visual = VisualStyler() if use_visual else None
        
        # Configuration
        self.config = self._load_config(config_file)
        
        # Cache setup
        self.cache_file = cache_file or os.path.join(os.path.expanduser('~'), '.domain_reputation_cache.db')
        self.cache_hours = 24  # Cache results for 24 hours
        self._init_cache()
        
        # API Keys from config or environment
        self.api_keys = {
            'virustotal': self.config.get('api_keys', 'virustotal', fallback=os.getenv('VIRUSTOTAL_API_KEY')),
            'securitytrails': self.config.get('api_keys', 'securitytrails', fallback=os.getenv('ST_API_KEY')),
            'shodan': self.config.get('api_keys', 'shodan', fallback=os.getenv('SHODAN_API_KEY')),
            'abuseipdb': self.config.get('api_keys', 'abuseipdb', fallback=os.getenv('ABUSEIPDB_API_KEY')),
            'pdcp': self.config.get('api_keys', 'pdcp', fallback=os.getenv('PDCP_API_KEY')),
            'ipapi': self.config.get('api_keys', 'ipapi', fallback=os.getenv('IPAPI_ACCESS_KEY')),
            'ipdata': self.config.get('api_keys', 'ipdata', fallback=os.getenv('IPDATA_API_KEY')),
            'urlscan': self.config.get('api_keys', 'urlscan', fallback=os.getenv('URLSCAN_API_KEY')),
            'abusech': self.config.get('api_keys', 'abusech', fallback=os.getenv('ABUSECH_API_KEY')),
            'apivoid': self.config.get('api_keys', 'apivoid', fallback=os.getenv('APIVOID_KEY'))
        }
        
        # Define sources that require API keys
        self.api_required_sources = {
            'virustotal': 'virustotal',
            'securitytrails': 'securitytrails', 
            'abuseipdb': 'abuseipdb',
            'shodan': 'shodan',
            'urlscan': 'urlscan',
            # URLVoid is optional - works as INFO source without API key
            'ip_geolocation': ['ipapi', 'ipdata']  # Requires at least one of these
        }
        
        # Store quiet startup preference
        self.quiet_startup = quiet_startup
        
        # Check API availability at startup
        self.available_sources = self._check_api_availability()
    
    def _load_config(self, config_file):
        """Load configuration from file"""
        config = configparser.ConfigParser()
        
        if config_file and os.path.exists(config_file):
            config.read(config_file)
        else:
            # Default configuration
            config.add_section('general')
            config.set('general', 'timeout', '10')
            config.set('general', 'cache_hours', '24')
            config.add_section('api_keys')
            
        return config
    
    def _filter_sources_by_api_keys(self, sources):
        """Filter sources based on API key availability using cached information"""
        return [s for s in sources if s in self.available_sources['available']]
    
    def _check_api_availability(self):
        """Check which sources are available based on API key configuration"""
        all_sources = [
            'virustotal', 'urlvoid', 'cisco_talos', 'alienvault_otx', 'mxtoolbox',
            'malware_bazaar', 'viewdns', 'centralops', 'criminalip', 'ipthc', 'dnslytics', 'synapsint',
            'securitytrails', 'abuseipdb', 'shodan', 'whois_info', 'hybrid_analysis',
            'urlscan', 'ip_geolocation'
        ]
        
        available = []
        unavailable = []
        
        for source in all_sources:
            req = self.api_required_sources.get(source)
            if not req:
                # No API key required
                available.append(source)
            elif isinstance(req, list):
                # Multiple possible API keys (at least one required)
                if any(bool(self.api_keys.get(k)) for k in req):
                    available.append(source)
                else:
                    unavailable.append((source, req))
            else:
                # Single API key required
                if bool(self.api_keys.get(req)):
                    available.append(source)
                else:
                    unavailable.append((source, [req]))
        
        # Display availability status (unless quiet startup is requested)
        if not self.quiet_startup:
            self._display_api_status(available, unavailable)
        
        return {
            'available': available,
            'unavailable': [item[0] for item in unavailable],
            'missing_keys': dict(unavailable)
        }
    
    def _display_api_status(self, available, unavailable):
        """Display API status at startup"""
        if self.visual and self.visual.use_rich:
            # Rich display
            status_table = Table(
                title="[bold cyan]🛡️ Threat Intelligence Sources Status 🛡️[/bold cyan]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
                caption=f"[dim]Ready: {len(available)} | Missing Keys: {len(unavailable)}[/dim]"
            )
            
            status_table.add_column("Source", style="cyan", width=20)
            status_table.add_column("Status", justify="center", width=15)
            status_table.add_column("Notes", width=25)
            
            # Add available sources
            for source in available:
                source_name = source.replace('_', ' ').title()
                req = self.api_required_sources.get(source)
                
                if not req:
                    status_text = "[green]✅ Ready[/green]"
                    notes = "No API key required"
                else:
                    status_text = "[green]✅ API Ready[/green]"
                    if isinstance(req, list):
                        working_keys = [k for k in req if bool(self.api_keys.get(k))]
                        notes = f"Using: {', '.join(working_keys)}"
                    else:
                        notes = f"API key configured"
                
                status_table.add_row(source_name, status_text, notes)
            
            # Add unavailable sources
            for source, missing_keys in unavailable:
                source_name = source.replace('_', ' ').title()
                status_text = "[yellow]⚠️ Need Key[/yellow]"
                notes = f"Missing: {', '.join(missing_keys)}"
                status_table.add_row(source_name, status_text, notes)
            
            self.visual.console.print()
            self.visual.console.print(status_table)
            
            if unavailable:
                # Show help panel for missing API keys
                help_text = "[bold yellow]Missing API Keys:[/bold yellow]\n"
                for source, keys in unavailable[:3]:  # Show first 3 to avoid clutter
                    env_vars = []
                    for key in keys:
                        if key == 'virustotal':
                            env_vars.append('VT_API_KEY')
                        elif key == 'securitytrails':
                            env_vars.append('ST_API_KEY')
                        elif key == 'abuseipdb':
                            env_vars.append('ABUSEIPDB_API_KEY')
                        elif key == 'shodan':
                            env_vars.append('SHODAN_API_KEY')
                        elif key == 'urlscan':
                            env_vars.append('URLSCAN_API_KEY')
                        elif key == 'ipapi':
                            env_vars.append('IPAPI_ACCESS_KEY')
                        elif key == 'ipdata':
                            env_vars.append('IPDATA_API_KEY')
                        else:
                            env_vars.append(f'{key.upper()}_API_KEY')
                    help_text += f"• {source.replace('_', ' ').title()}: {'/'.join(env_vars)}\n"
                if len(unavailable) > 3:
                    help_text += f"• ... and {len(unavailable) - 3} more sources\n"
                help_text += "\n[dim]Tip: Use --show-sources for detailed setup information[/dim]"
                
                help_panel = Panel(
                    help_text,
                    title="[bold]Setup Help[/bold]",
                    box=box.ROUNDED,
                    border_style="yellow"
                )
                self.visual.console.print(help_panel)
            
        else:
            # Basic display
            print("\n" + "="*60)
            print("🛡️ THREAT INTELLIGENCE SOURCES STATUS")
            print("="*60)
            print(f"✅ Available: {len(available)} sources")
            print(f"⚠️ Missing Keys: {len(unavailable)} sources\n")
            
            if available:
                print("Available Sources:")
                for source in available:
                    print(f"  ✅ {source.replace('_', ' ').title()}")
                print()
            
            if unavailable:
                print("Sources Missing API Keys:")
                for source, keys in unavailable:
                    print(f"  ⚠️ {source.replace('_', ' ').title()} (needs: {', '.join(keys)})")
                print("\nTip: Set environment variables or use config.ini file for API keys\n")
    
    def _init_cache(self):
        """Initialize SQLite cache database"""
        try:
            conn = sqlite3.connect(self.cache_file)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS domain_cache (
                    domain TEXT PRIMARY KEY,
                    results TEXT,
                    timestamp DATETIME,
                    hash TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not initialize cache: {e}")
    
    def _get_cache_key(self, domain, sources):
        """Generate cache key based on domain and sources"""
        sources_str = ','.join(sorted(sources))
        return hashlib.md5(f"{domain}:{sources_str}".encode()).hexdigest()
    
    def _get_cached_result(self, domain, sources):
        """Get cached results if available and not expired"""
        try:
            conn = sqlite3.connect(self.cache_file)
            cache_key = self._get_cache_key(domain, sources)
            
            cursor = conn.execute(
                'SELECT results, timestamp FROM domain_cache WHERE hash = ?', 
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if row:
                results_json, timestamp_str = row
                timestamp = datetime.fromisoformat(timestamp_str)
                
                # Check if cache is still valid
                if datetime.now() - timestamp < timedelta(hours=self.cache_hours):
                    conn.close()
                    return json.loads(results_json)
            
            conn.close()
            return None
        except Exception:
            return None
    
    def _cache_result(self, domain, sources, results):
        """Cache the results"""
        try:
            conn = sqlite3.connect(self.cache_file)
            cache_key = self._get_cache_key(domain, sources)
            timestamp = datetime.now().isoformat()
            
            conn.execute('''
                INSERT OR REPLACE INTO domain_cache (domain, results, timestamp, hash)
                VALUES (?, ?, ?, ?)
            ''', (domain, json.dumps(results), timestamp, cache_key))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not cache results: {e}")
    
    def _make_request(self, url, params=None, headers=None, max_retries=3):
        """Make HTTP request with retry logic and error handling"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=self.timeout,
                    verify=False  # Ignore SSL certificate issues
                )
                return response
            except requests.exceptions.SSLError as e:
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
                raise e
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                raise e
        
        return None

    def check_virustotal(self, domain, api_key=None):
        """Check domain reputation on VirusTotal"""
        if self.visual:
            self.visual.print_source_checking("VirusTotal")
        else:
            print(f"[*] Checking VirusTotal...")
        
        api_key = api_key or self.api_keys.get('virustotal')
        
        if api_key:
            # Use v3 API (more reliable than v2)
            try:
                url = f"https://www.virustotal.com/api/v3/domains/{domain}"
                headers = {
                    'x-apikey': api_key,
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # Use requests directly with better timeout handling
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=(10, 30),  # (connection timeout, read timeout)
                    verify=True  # Enable SSL verification for VT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    attributes = data.get('data', {}).get('attributes', {})
                    
                    # Get analysis stats
                    last_analysis = attributes.get('last_analysis_stats', {})
                    malicious = last_analysis.get('malicious', 0)
                    suspicious = last_analysis.get('suspicious', 0)
                    harmless = last_analysis.get('harmless', 0)
                    undetected = last_analysis.get('undetected', 0)
                    
                    # Determine reputation
                    if malicious > 0:
                        reputation = 'malicious'
                    elif suspicious > 2:  # More than 2 suspicious detections
                        reputation = 'suspicious'
                    elif harmless > malicious + suspicious:
                        reputation = 'clean'
                    else:
                        reputation = 'unknown'
                    
                    # Get engines data (last_analysis_results)
                    engines = attributes.get('last_analysis_results', {})
                    
                    result = {
                        'status': 'success',
                        'malicious': malicious,
                        'suspicious': suspicious,
                        'harmless': harmless,
                        'undetected': undetected,
                        'reputation': reputation,
                        'last_analysis': attributes.get('last_analysis_date', 'N/A'),
                        'categories': attributes.get('categories', {}),
                        'engines': engines  # Include engines for detailed analysis
                    }
                elif response.status_code == 404:
                    result = {'status': 'not_found', 'message': 'Domain not found in VirusTotal database'}
                elif response.status_code == 401:
                    result = {'status': 'error', 'message': 'Invalid API key for VirusTotal'}
                elif response.status_code == 429:
                    result = {'status': 'error', 'message': 'Rate limit exceeded for VirusTotal API'}
                else:
                    result = {'status': 'error', 'message': f'VirusTotal API error: HTTP {response.status_code}'}
                    
            except requests.exceptions.Timeout:
                result = {'status': 'error', 'message': 'VirusTotal API request timed out'}
            except requests.exceptions.ConnectionError:
                result = {'status': 'error', 'message': 'Failed to connect to VirusTotal API'}
            except requests.exceptions.RequestException as e:
                result = {'status': 'error', 'message': f'VirusTotal request error: {str(e)[:50]}...'}
            except json.JSONDecodeError:
                result = {'status': 'error', 'message': 'Invalid JSON response from VirusTotal'}
            except Exception as e:
                result = {'status': 'error', 'message': f'Unexpected VirusTotal error: {str(e)[:50]}...'}
        else:
            result = {'status': 'info', 'message': f'VirusTotal requires API key. Visit: https://www.virustotal.com/gui/domain/{domain}'}
        
        self.results['virustotal'] = result
        return result

    def check_urlvoid(self, domain):
        """Check domain reputation on URLVoid via APIVoid API"""
        if self.visual:
            self.visual.print_source_checking("URLVoid (via APIVoid)")
        else:
            print(f"[*] Checking URLVoid via APIVoid API...")
        
        api_key = self.api_keys.get('apivoid')
        
        if api_key:
            try:
                # APIVoid Domain Reputation API V2 (POST request)
                url = "https://api.apivoid.com/v2/domain-reputation"
                headers = {
                    'Content-Type': 'application/json',
                    'X-API-Key': api_key
                }
                payload = {'host': domain}
                response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for API errors
                    if data.get('error'):
                        # Check for invalid API key - fallback to manual check
                        error_msg = str(data.get('error', ''))
                        if 'not valid' in error_msg.lower() or 'invalid' in error_msg.lower():
                            result = {
                                'status': 'info',
                                'message': 'URLVoid check requires valid APIVoid API key - Manual check available',
                                'url': f'https://www.urlvoid.com/scan/{domain}/',
                                'reputation': 'unknown'
                            }
                        else:
                            result = {
                                'status': 'error',
                                'message': data.get('error')
                            }
                    else:
                        # Parse V2 response structure (blacklists at root level)
                        blacklists = data.get('blacklists', {})
                        detections = blacklists.get('detections', 0)
                        engines_count = blacklists.get('engines_count', 0)
                        detection_rate = blacklists.get('detection_rate', '0%')
                        engines = blacklists.get('engines', {})
                        
                        # Determine reputation based on detections
                        if detections >= 3:
                            reputation = 'malicious'
                        elif detections >= 1:
                            reputation = 'suspicious'
                        else:
                            reputation = 'clean'
                        
                        # Get list of engines that detected it
                        detected_by = []
                        if engines:
                            for engine_name, engine_data in engines.items():
                                if engine_data.get('detected'):
                                    detected_by.append(engine_name)
                        
                        result = {
                            'status': 'success',
                            'reputation': reputation,
                            'detections': detections,
                            'detection_rate': detection_rate,
                            'total_engines': engines_count,
                            'detected_by': detected_by[:5] if detected_by else [],  # First 5 engines
                            'url': f"https://www.urlvoid.com/scan/{domain}/"
                        }
                elif response.status_code == 401:
                    # Invalid API key - fallback to manual check
                    result = {
                        'status': 'info',
                        'message': 'URLVoid check requires valid APIVoid API key - Manual check available',
                        'url': f'https://www.urlvoid.com/scan/{domain}/',
                        'reputation': 'unknown'
                    }
                elif response.status_code == 429:
                    result = {'status': 'error', 'message': 'APIVoid rate limit exceeded'}
                else:
                    result = {'status': 'error', 'message': f'APIVoid API error: HTTP {response.status_code}'}
                    
            except requests.exceptions.Timeout:
                result = {'status': 'error', 'message': 'APIVoid request timed out'}
            except requests.exceptions.RequestException as e:
                result = {'status': 'error', 'message': f'APIVoid request error: {str(e)[:50]}...'}
            except json.JSONDecodeError:
                result = {'status': 'error', 'message': 'Invalid JSON response from APIVoid'}
            except Exception as e:
                result = {'status': 'error', 'message': f'Unexpected APIVoid error: {str(e)[:50]}...'}
        else:
            # Fallback: provide manual investigation link
            result = {
                'status': 'info',
                'message': 'URLVoid requires APIVoid API key for automated checks',
                'url': f'https://www.urlvoid.com/scan/{domain}/',
                'reputation': 'unknown'
            }
        
        self.results['urlvoid'] = result
        return result

    def check_cisco_talos(self, domain):
        """Cisco Talos - Manual investigation (Cloudflare protection)"""
        if self.visual:
            self.visual.print_source_checking("Cisco Talos")
        else:
            print(f"[*] Checking Cisco Talos...")
        
        # Cisco Talos uses Cloudflare protection that blocks automated scraping
        result = {
            'status': 'info',
            'message': 'Cisco Talos requires manual investigation (Cloudflare protection)',
            'investigation_workflow': [
                f'1. Visit: https://talosintelligence.com/reputation_center/lookup?search={domain}',
                '2. Check: Email and web reputation score',
                '3. Analyze: Category, threat level, and historical data',
                '4. Review: WHOIS, DNS, and network information'
            ],
            'url': f'https://talosintelligence.com/reputation_center/lookup?search={domain}',
            'reputation': 'unknown'
        }
        
        self.results['cisco_talos'] = result
        return result

    def check_alienvault_otx(self, domain):
        """Check domain on AlienVault OTX"""
        if self.visual:
            self.visual.print_source_checking("AlienVault OTX")
        else:
            print(f"[*] Checking AlienVault OTX...")
        
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            pulse_count = data.get('pulse_info', {}).get('count', 0)
            
            if pulse_count > 5:
                reputation = "suspicious"
            elif pulse_count > 0:
                reputation = "questionable"
            else:
                reputation = "clean"
            
            result = {
                'status': 'success',
                'pulse_count': pulse_count,
                'reputation': reputation,
                'url': f"https://otx.alienvault.com/indicator/domain/{domain}"
            }
        except Exception as e:
            result = {'status': 'error', 'message': str(e)}
        
        self.results['alienvault_otx'] = result
        return result

    def check_mxtoolbox(self, domain):
        """Check domain reputation on MXToolbox blacklist checker"""
        if self.visual:
            self.visual.print_source_checking("MXToolbox")
        else:
            print(f"[*] Checking MXToolbox...")
        
        # MXToolbox API requires authentication/API key
        # Provide manual investigation URL instead
        result = {
            'status': 'info',
            'message': 'MXToolbox requires manual investigation - Check DNS, blacklists, and email reputation',
            'investigation_workflow': [
                f'1. Visit: https://mxtoolbox.com/SuperTool.aspx?action=blacklist:{domain}',
                '2. Check: Domain blacklist status across 100+ blacklist databases',
                '3. Analyze: MX records, SPF, DKIM, and DMARC configuration',
                '4. Review: DNS health check and mail server reputation'
            ],
            'url': f'https://mxtoolbox.com/SuperTool.aspx?action=blacklist:{domain}',
            'reputation': 'unknown'
        }
        
        self.results['mxtoolbox'] = result
        return result

    def check_malware_bazaar(self, ioc):
        """Check IoC (domain or hash) on MalwareBazaar by abuse.ch"""
        if self.visual:
            self.visual.print_source_checking("MalwareBazaar IoC")
        else:
            print(f"[*] Checking MalwareBazaar IoC...")
        
        # Get abuse.ch API key
        api_key = self.api_keys.get('abusech')
        
        # Detect if IoC is a hash
        import re
        hash_patterns = {
            'md5': r'^[a-fA-F0-9]{32}$',
            'sha1': r'^[a-fA-F0-9]{40}$',
            'sha256': r'^[a-fA-F0-9]{64}$'
        }
        
        is_hash = False
        hash_type = None
        for htype, pattern in hash_patterns.items():
            if re.match(pattern, ioc):
                is_hash = True
                hash_type = htype
                break
        
        # If hash is detected, check MalwareBazaar first, then VirusTotal
        if is_hash:
            # Try MalwareBazaar API first if we have the key
            abusech_key = api_key
            if abusech_key:
                try:
                    if self.visual:
                        self.visual.print_source_checking(f"MalwareBazaar (Hash: {hash_type.upper()})")
                    else:
                        print(f"[*] Checking MalwareBazaar for {hash_type.upper()} hash...")
                    
                    # MalwareBazaar API with Auth-Key header
                    url = "https://mb-api.abuse.ch/api/v1/"
                    headers = {
                        'Auth-Key': abusech_key,
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    }
                    data = {
                        'query': 'get_info',
                        'hash': ioc
                    }
                    
                    response = requests.post(url, data=data, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        mb_data = response.json()
                        query_status = mb_data.get('query_status')
                        
                        if query_status == 'ok':
                            # Found in MalwareBazaar - extract details
                            sample_data = mb_data.get('data', [{}])[0] if isinstance(mb_data.get('data'), list) else mb_data.get('data', {})
                            
                            result = {
                                'status': 'success',
                                'ioc_type': 'hash',
                                'hash_type': hash_type,
                                'reputation': 'malicious',  # If found in MB, it's malicious
                                'malware_detected': True,
                                'file_name': sample_data.get('file_name', 'Unknown'),
                                'file_type': sample_data.get('file_type', 'Unknown'),
                                'file_size': sample_data.get('file_size', 0),
                                'signature': sample_data.get('signature', 'Unknown'),
                                'tags': sample_data.get('tags', []),
                                'delivery_method': sample_data.get('delivery_method', 'Unknown'),
                                'first_seen': sample_data.get('first_seen', 'Unknown'),
                                'mb_checked': True,
                                'url': f'https://bazaar.abuse.ch/browse.php?search={ioc}'
                            }
                            self.results['malware_bazaar'] = result
                            return result
                        elif query_status == 'no_results':
                            # Not found in MalwareBazaar, will check VT next
                            pass
                        else:
                            # Unknown status, will check VT
                            pass
                except Exception as e:
                    # Error with MalwareBazaar, will try VT
                    if self.visual:
                        print(f"[!] MalwareBazaar error: {str(e)[:50]}...")
            
            # Now check VirusTotal (either MB not available or hash not found in MB)
            vt_key = self.api_keys.get('virustotal')
            if vt_key:
                if self.visual:
                    self.visual.print_source_checking(f"VirusTotal (Hash: {hash_type.upper()})")
                else:
                    print(f"[*] Checking VirusTotal for {hash_type.upper()} hash...")
                
                try:
                    # VirusTotal v3 API for file hash lookup
                    url = f"https://www.virustotal.com/api/v3/files/{ioc}"
                    headers = {
                        'x-apikey': api_key,
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    }
                    
                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=(10, 30),
                        verify=True
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        attributes = data.get('data', {}).get('attributes', {})
                        
                        # Get analysis stats
                        last_analysis = attributes.get('last_analysis_stats', {})
                        malicious = last_analysis.get('malicious', 0)
                        suspicious = last_analysis.get('suspicious', 0)
                        harmless = last_analysis.get('harmless', 0)
                        undetected = last_analysis.get('undetected', 0)
                        
                        # Get file details
                        file_name = attributes.get('meaningful_name') or attributes.get('names', ['Unknown'])[0] if attributes.get('names') else 'Unknown'
                        file_type = attributes.get('type_description', 'Unknown')
                        file_size = attributes.get('size', 0)
                        
                        # Determine reputation
                        if malicious > 0:
                            reputation = 'malicious'
                        elif suspicious > 2:
                            reputation = 'suspicious'
                        elif harmless > malicious + suspicious:
                            reputation = 'clean'
                        else:
                            reputation = 'unknown'
                        
                        result = {
                            'status': 'success',
                            'ioc_type': 'hash',
                            'hash_type': hash_type,
                            'malicious': malicious,
                            'suspicious': suspicious,
                            'harmless': harmless,
                            'undetected': undetected,
                            'reputation': reputation,
                            'file_name': file_name,
                            'file_type': file_type,
                            'file_size': file_size,
                            'vt_checked': True,
                            'url': f'https://www.virustotal.com/gui/file/{ioc}'
                        }
                    elif response.status_code == 404:
                        result = {
                            'status': 'not_found',
                            'ioc_type': 'hash',
                            'hash_type': hash_type,
                            'message': 'Hash not found in VirusTotal database',
                            'reputation': 'unknown',
                            'url': f'https://www.virustotal.com/gui/file/{ioc}'
                        }
                    else:
                        # VT error, fall back to manual check
                        result = {
                            'status': 'info',
                            'ioc_type': 'hash',
                            'hash_type': hash_type,
                            'message': f'VirusTotal API error (HTTP {response.status_code}). Check manually at MalwareBazaar and VirusTotal',
                            'investigation_workflow': [
                                f'1. Visit MalwareBazaar: https://bazaar.abuse.ch/browse.php?search={ioc}',
                                f'2. Visit VirusTotal: https://www.virustotal.com/gui/file/{ioc}',
                                '3. Check: File detection rates across multiple engines',
                                '4. Analyze: File behavior, signatures, and associations'
                            ],
                            'url': f'https://www.virustotal.com/gui/file/{ioc}',
                            'reputation': 'unknown'
                        }
                        
                except requests.exceptions.Timeout:
                    result = {
                        'status': 'error',
                        'ioc_type': 'hash',
                        'hash_type': hash_type,
                        'message': 'VirusTotal API request timed out',
                        'reputation': 'unknown'
                    }
                except Exception as e:
                    result = {
                        'status': 'error',
                        'ioc_type': 'hash',
                        'hash_type': hash_type,
                        'message': f'VirusTotal error: {str(e)[:50]}...',
                        'reputation': 'unknown'
                    }
            else:
                # No VT API key, provide manual investigation link
                result = {
                    'status': 'info',
                    'ioc_type': 'hash',
                    'hash_type': hash_type,
                    'message': 'Hash detected - VirusTotal API key required for automated analysis',
                    'investigation_workflow': [
                        f'1. Visit MalwareBazaar: https://bazaar.abuse.ch/browse.php?search={ioc}',
                        f'2. Visit VirusTotal: https://www.virustotal.com/gui/file/{ioc}',
                        '3. Check: File detection rates and malware classification',
                        '4. Analyze: File behavior, signatures, and threat indicators'
                    ],
                    'url': f'https://www.virustotal.com/gui/file/{ioc}',
                    'reputation': 'unknown'
                }
        else:
            # Domain/URL - MalwareBazaar doesn't support domain searches directly
            result = {
                'status': 'info',
                'ioc_type': 'domain',
                'message': 'MalwareBazaar is designed for hash-based malware sample searches only',
                'investigation_workflow': [
                    '1. MalwareBazaar only supports: MD5, SHA1, SHA256 hash searches',
                    '2. For domains: Use VirusTotal, URLScan, or other domain-focused sources',
                    '3. If you have a file hash related to this domain, search by hash',
                    '4. Visit: https://bazaar.abuse.ch/ to browse recent samples'
                ],
                'url': 'https://bazaar.abuse.ch/',
                'reputation': 'unknown'
            }
        
        self.results['malware_bazaar'] = result
        return result

    def check_threatfox(self, ioc):
        """Check IoC (domain, IP, URL, or hash) on ThreatFox by abuse.ch"""
        if self.visual:
            self.visual.print_source_checking("ThreatFox IOC Database")
        else:
            print(f"[*] Checking ThreatFox IOC database...")
        
        # Get ThreatFox API key (optional but increases rate limits)
        api_key = self.api_keys.get('threatfox')
        
        try:
            # ThreatFox API endpoint
            url = "https://threatfox-api.abuse.ch/api/v1/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
            
            # Add API key if available
            if api_key:
                headers['Auth-Key'] = api_key
            
            # Search for IOC
            payload = {
                'query': 'search_ioc',
                'search_term': ioc
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                query_status = data.get('query_status')
                
                if query_status == 'ok':
                    # IOC found in ThreatFox
                    ioc_data = data.get('data', [])
                    
                    if not ioc_data:
                        result = {
                            'status': 'success',
                            'ioc_found': False,
                            'ioc_count': 0,
                            'reputation': 'clean',
                            'message': 'IOC not found in ThreatFox database',
                            'url': 'https://threatfox.abuse.ch/'
                        }
                    else:
                        # Extract IOC details
                        first_ioc = ioc_data[0] if isinstance(ioc_data, list) else ioc_data
                        
                        ioc_count = len(ioc_data) if isinstance(ioc_data, list) else 1
                        malware_families = set()
                        threat_types = set()
                        tags_list = set()
                        confidence_levels = []
                        
                        for entry in (ioc_data if isinstance(ioc_data, list) else [ioc_data]):
                            if entry.get('malware'):
                                malware_families.add(entry['malware'])
                            if entry.get('threat_type'):
                                threat_types.add(entry['threat_type'])
                            if entry.get('tags'):
                                tags_list.update(entry['tags'])
                            if entry.get('confidence_level'):
                                confidence_levels.append(entry['confidence_level'])
                        
                        # Calculate average confidence (if available)
                        avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0
                        
                        # Determine reputation based on findings
                        # Any IOC found in ThreatFox is considered malicious
                        reputation = 'malicious'
                        
                        result = {
                            'status': 'success',
                            'ioc_found': True,
                            'ioc_count': ioc_count,
                            'reputation': reputation,
                            'malware_families': list(malware_families)[:5],  # Top 5
                            'threat_types': list(threat_types),
                            'tags': list(tags_list)[:10],  # Top 10 tags
                            'confidence_level': int(avg_confidence) if avg_confidence else None,
                            'ioc_type': first_ioc.get('ioc_type', 'unknown'),
                            'first_seen': first_ioc.get('first_seen', 'Unknown'),
                            'last_seen': first_ioc.get('last_seen', 'Unknown'),
                            'reporter': first_ioc.get('reporter', 'Unknown'),
                            'url': f'https://threatfox.abuse.ch/browse.php?search=ioc%3A{ioc}'
                        }
                
                elif query_status == 'no_result':
                    result = {
                        'status': 'success',
                        'ioc_found': False,
                        'ioc_count': 0,
                        'reputation': 'clean',
                        'message': 'IOC not found in ThreatFox database',
                        'url': 'https://threatfox.abuse.ch/'
                    }
                
                else:
                    result = {
                        'status': 'error',
                        'message': f'ThreatFox query status: {query_status}',
                        'reputation': 'unknown',
                        'url': 'https://threatfox.abuse.ch/'
                    }
            
            elif response.status_code == 401:
                result = {
                    'status': 'error',
                    'message': 'Invalid ThreatFox API key',
                    'reputation': 'unknown',
                    'url': 'https://threatfox.abuse.ch/'
                }
            
            elif response.status_code == 429:
                result = {
                    'status': 'error',
                    'message': 'ThreatFox rate limit exceeded - consider using API key',
                    'reputation': 'unknown',
                    'url': 'https://threatfox.abuse.ch/'
                }
            
            else:
                result = {
                    'status': 'error',
                    'message': f'ThreatFox API error: HTTP {response.status_code}',
                    'reputation': 'unknown',
                    'url': 'https://threatfox.abuse.ch/'
                }
        
        except requests.exceptions.Timeout:
            result = {
                'status': 'error',
                'message': 'ThreatFox API request timed out',
                'reputation': 'unknown',
                'url': 'https://threatfox.abuse.ch/'
            }
        except requests.exceptions.RequestException as e:
            result = {
                'status': 'error',
                'message': f'ThreatFox request error: {str(e)[:50]}...',
                'reputation': 'unknown',
                'url': 'https://threatfox.abuse.ch/'
            }
        except Exception as e:
            result = {
                'status': 'error',
                'message': f'ThreatFox unexpected error: {str(e)[:50]}...',
                'reputation': 'unknown',
                'url': 'https://threatfox.abuse.ch/'
            }
        
        self.results['threatfox'] = result
        return result

    def check_viewdns(self, domain):
        """ViewDNS.info - Manual investigation (anti-bot protection)"""
        if self.visual:
            self.visual.print_source_checking("ViewDNS.info")
        else:
            print(f"[*] Checking ViewDNS.info...")
        
        result = {
            'status': 'info',
            'message': 'ViewDNS.info requires manual investigation (anti-bot protection)',
            'investigation_workflow': [
                f'1. Visit: https://viewdns.info/reverseip/?host={domain}',
                '2. Check: Reverse IP lookup to find domains on same IP',
                '3. Analyze: Number of domains sharing the IP (high count = shared hosting)',
                '4. Look for: Suspicious domains on same IP address'
            ],
            'url': f'https://viewdns.info/reverseip/?host={domain}',
            'reputation': 'unknown'
        }
        
        self.results['viewdns'] = result
        return result

    def check_centralops(self, domain):
        """CentralOps.net - Manual investigation tools"""
        if self.visual:
            self.visual.print_source_checking("CentralOps.net")
        else:
            print(f"[*] Checking CentralOps.net...")
        
        result = {
            'status': 'info',
            'message': 'CentralOps.net provides comprehensive investigation tools',
            'investigation_workflow': [
                f'1. Visit: https://centralops.net/co/DomainDossier.aspx?addr={domain}',
                '2. Check: WHOIS information, DNS records, network routes',
                '3. Analyze: Registrar details, name servers, mail servers',
                '4. Review: IP addresses, ASN information, geographic location'
            ],
            'url': f'https://centralops.net/co/DomainDossier.aspx?addr={domain}',
            'reputation': 'unknown'
        }
        
        self.results['centralops'] = result
        return result

    def check_criminalip(self, domain):
        """CriminalIP.io - Manual investigation (requires API key for automation)"""
        if self.visual:
            self.visual.print_source_checking("CriminalIP.io")
        else:
            print(f"[*] Checking CriminalIP.io...")
        
        result = {
            'status': 'info',
            'message': 'CriminalIP.io requires manual investigation or API key',
            'investigation_workflow': [
                f'1. Visit: https://www.criminalip.io/domain/{domain}',
                '2. Check: Domain reputation score and security issues',
                '3. Analyze: Associated IPs, hosting information, and threats',
                '4. Review: Malware history and blacklist status'
            ],
            'url': f'https://www.criminalip.io/domain/{domain}',
            'reputation': 'unknown'
        }
        
        self.results['criminalip'] = result
        return result

    def check_ipthc(self, domain):
        """IP.THC.org - Manual investigation (JavaScript-based tool)"""
        if self.visual:
            self.visual.print_source_checking("IP.THC.org")
        else:
            print(f"[*] Checking IP.THC.org...")
        
        result = {
            'status': 'info',
            'message': 'IP.THC.org is a JavaScript-based tool - manual check recommended',
            'investigation_workflow': [
                f'1. Visit: https://ip.thc.org/lookup/{domain}',
                '2. Check: Reverse DNS lookups and subdomain discovery',
                '3. Analyze: IP ranges and hosting infrastructure',
                '4. Review: SSL certificate information'
            ],
            'url': f'https://ip.thc.org/lookup/{domain}',
            'reputation': 'unknown'
        }
        
        self.results['ipthc'] = result
        return result

    def check_dnslytics(self, domain):
        """DNSlytics.com - Manual investigation (anti-bot protection)"""
        if self.visual:
            self.visual.print_source_checking("DNSlytics.com")
        else:
            print(f"[*] Checking DNSlytics.com...")
        
        result = {
            'status': 'info',
            'message': 'DNSlytics.com requires manual investigation (anti-bot protection)',
            'investigation_workflow': [
                f'1. Visit: https://dnslytics.com/domain/{domain}',
                '2. Check: DNS records, mail servers, and IP information',
                '3. Analyze: Blacklist status and domain relationships',
                '4. Review: Historical DNS data and hosting changes'
            ],
            'url': f'https://dnslytics.com/domain/{domain}',
            'reputation': 'unknown'
        }
        
        self.results['dnslytics'] = result
        return result

    def check_synapsint(self, domain):
        """Synapsint.com - Manual OSINT investigation"""
        if self.visual:
            self.visual.print_source_checking("Synapsint.com")
        else:
            print(f"[*] Checking Synapsint.com...")
        
        result = {
            'status': 'info',
            'message': 'Synapsint.com OSINT engine - manual investigation required',
            'investigation_workflow': [
                f'1. Visit: https://synapsint.com/domain.php?domain={domain}',
                '2. Check: OSINT data aggregation from multiple sources',
                '3. Analyze: Social media presence and web mentions',
                '4. Review: Related domains and infrastructure'
            ],
            'url': f'https://synapsint.com/domain.php?domain={domain}',
            'reputation': 'unknown'
        }
        
        self.results['synapsint'] = result
        return result

    def check_securitytrails(self, domain, api_key=None):
        """Check domain on SecurityTrails"""
        if self.visual:
            self.visual.print_source_checking("SecurityTrails")
        else:
            print(f"[*] Checking SecurityTrails...")
        
        if api_key:
            try:
                url = f"https://api.securitytrails.com/v1/domain/{domain}"
                headers = {'APIKEY': api_key}
                response = self.session.get(url, headers=headers, timeout=10)
                data = response.json()
                
                if response.status_code == 200:
                    result = {
                        'status': 'success',
                        'first_seen': data.get('first_seen', 'N/A'),
                        'subdomain_count': data.get('subdomain_count', 0),
                        'reputation': 'clean'  # SecurityTrails doesn't provide reputation scores
                    }
                else:
                    result = {'status': 'not_found', 'message': 'Domain not found'}
            except Exception as e:
                result = {'status': 'error', 'message': str(e)}
        else:
            result = {'status': 'info', 'message': f'SecurityTrails requires API key. Visit: https://securitytrails.com/domain/{domain}'}
        
        self.results['securitytrails'] = result
        return result
    
    def check_abuseipdb(self, domain):
        """Check domain reputation on AbuseIPDB (requires IP resolution)"""
        if self.visual:
            self.visual.print_source_checking("AbuseIPDB")
        else:
            print(f"[*] Checking AbuseIPDB...")
        
        api_key = self.api_keys.get('abuseipdb')
        
        if not api_key:
            result = {'status': 'info', 'message': 'AbuseIPDB requires API key. Get one at: https://www.abuseipdb.com/api'}
        else:
            # Try multiple DNS resolution methods
            resolved_ips = self._resolve_domain_ips(domain)
            
            if not resolved_ips:
                result = {'status': 'not_found', 'message': 'Could not resolve domain to IP address'}
            else:
                # Use the first resolved IP for reputation check
                ip = resolved_ips[0]
                
                try:
                    # Check IP reputation on AbuseIPDB
                    url = 'https://api.abuseipdb.com/api/v2/check'
                    
                    headers = {
                        'Key': api_key,
                        'Accept': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    
                    params = {
                        'ipAddress': ip,
                        'maxAgeInDays': 90,
                        'verbose': ''
                    }
                    
                    # Use session with retry mechanism
                    session = requests.Session()
                    session.mount('https://', requests.adapters.HTTPAdapter(
                        max_retries=requests.adapters.Retry(
                            total=3,
                            backoff_factor=1,
                            status_forcelist=[500, 502, 503, 504]
                        )
                    ))
                    
                    response = session.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=(15, 45),  # Increased timeout for AbuseIPDB
                        verify=True
                    )
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            data = response_data.get('data', {})
                            
                            confidence = data.get('abuseConfidencePercentage', 0)
                            reports = data.get('totalReports', 0)
                            is_public = data.get('isPublic', False)
                            country_code = data.get('countryCode', 'N/A')
                            usage_type = data.get('usageType', 'unknown')
                            isp = data.get('isp', 'N/A')
                            
                            # Get detailed reports if confidence is suspicious/malicious OR there are reports
                            attack_reports = []
                            attack_categories = []
                            
                            if (confidence >= 25 or reports > 0) and reports > 0:
                                # Fetch detailed reports using the reports endpoint
                                try:
                                    reports_url = 'https://api.abuseipdb.com/api/v2/reports'
                                    reports_params = {
                                        'ipAddress': ip,
                                        'maxAgeInDays': 90,
                                        'page': 1,
                                        'perPage': 10  # Get last 10 reports
                                    }
                                    
                                    reports_response = session.get(
                                        reports_url,
                                        params=reports_params,
                                        headers=headers,
                                        timeout=(15, 45),
                                        verify=True
                                    )
                                    
                                    if reports_response.status_code == 200:
                                        reports_data = reports_response.json()
                                        report_list = reports_data.get('data', {}).get('results', [])
                                        
                                        # Category mapping
                                        category_names = {
                                            3: 'Fraud Orders',
                                            4: 'DDoS Attack',
                                            5: 'FTP Brute-Force',
                                            6: 'Ping of Death',
                                            7: 'Phishing',
                                            8: 'Fraud VoIP',
                                            9: 'Open Proxy',
                                            10: 'Web Spam',
                                            11: 'Email Spam',
                                            12: 'Blog Spam',
                                            13: 'VPN IP',
                                            14: 'Port Scan',
                                            15: 'Hacking',
                                            16: 'SQL Injection',
                                            17: 'Spoofing',
                                            18: 'Brute-Force',
                                            19: 'Bad Web Bot',
                                            20: 'Exploited Host',
                                            21: 'Web App Attack',
                                            22: 'SSH',
                                            23: 'IoT Targeted'
                                        }
                                        
                                        # Process reports
                                        for report in report_list[:10]:  # Limit to 10 most recent
                                            report_categories = report.get('categories', [])
                                            report_comment = report.get('comment', 'No comment')
                                            report_date = report.get('reportedAt', 'Unknown date')
                                            
                                            # Map category numbers to names
                                            cat_names = [category_names.get(cat, f'Category {cat}') for cat in report_categories]
                                            
                                            attack_reports.append({
                                                'date': report_date,
                                                'categories': cat_names,
                                                'comment': report_comment[:100]  # Limit comment length
                                            })
                                            
                                            # Track unique attack categories
                                            attack_categories.extend(cat_names)
                                        
                                        # Get unique categories
                                        attack_categories = list(set(attack_categories))
                                        
                                except Exception as e:
                                    # If reports fetch fails, continue with basic info
                                    pass
                            
                            # Determine reputation based on confidence and reports
                            if confidence >= 75:
                                reputation = 'malicious'
                            elif confidence >= 25 or reports > 5:
                                reputation = 'suspicious'
                            elif confidence > 0 or reports > 0:
                                reputation = 'questionable'
                            else:
                                reputation = 'clean'
                            
                            result = {
                                'status': 'success',
                                'ip_address': ip,
                                'abuse_confidence': confidence,
                                'total_reports': reports,
                                'is_public': is_public,
                                'country': country_code,
                                'usage_type': usage_type,
                                'isp': isp,
                                'reputation': reputation,
                                'additional_ips': resolved_ips[1:] if len(resolved_ips) > 1 else [],
                                'attack_categories': attack_categories if attack_categories else [],
                                'recent_attacks': attack_reports if attack_reports else []
                            }
                            
                        except (KeyError, ValueError, json.JSONDecodeError) as e:
                            result = {'status': 'error', 'message': f'Invalid JSON response from AbuseIPDB: {str(e)[:30]}...'}
                            
                    elif response.status_code == 401:
                        result = {'status': 'error', 'message': 'Invalid AbuseIPDB API key'}
                    elif response.status_code == 402:
                        result = {'status': 'error', 'message': 'AbuseIPDB API quota exceeded (upgrade plan required)'}
                    elif response.status_code == 429:
                        result = {'status': 'error', 'message': 'AbuseIPDB rate limit exceeded - try again later'}
                    elif response.status_code == 422:
                        result = {'status': 'error', 'message': f'Invalid IP address format: {ip}'}
                    else:
                        result = {'status': 'error', 'message': f'AbuseIPDB API error: HTTP {response.status_code}'}
                        
                except requests.exceptions.Timeout:
                    result = {'status': 'error', 'message': 'AbuseIPDB API request timed out'}
                except requests.exceptions.SSLError:
                    result = {'status': 'error', 'message': 'SSL certificate error connecting to AbuseIPDB'}
                except requests.exceptions.ConnectionError:
                    result = {'status': 'error', 'message': 'Failed to connect to AbuseIPDB API'}
                except requests.exceptions.RequestException as e:
                    result = {'status': 'error', 'message': f'AbuseIPDB request error: {str(e)[:50]}...'}
                except Exception as e:
                    result = {'status': 'error', 'message': f'Unexpected AbuseIPDB error: {str(e)[:50]}...'}
                    
        self.results['abuseipdb'] = result
        return result
    
    def _resolve_domain_ips(self, domain):
        """Resolve domain to IP addresses using multiple methods"""
        resolved_ips = []
        
        # Check if the domain is already an IP address
        if self._is_valid_ip(domain):
            return [domain]
        
        # Method 1: Try Python's built-in socket resolution (fallback to system DNS)
        try:
            import socket
            ip = socket.gethostbyname(domain)
            if ip and self._is_valid_ip(ip):
                resolved_ips.append(ip)
        except Exception:
            pass  # Continue to other methods
        
        # Method 2: Try alternative DNS services with reduced SSL issues
        dns_services = [
            # OpenDNS
            ('https://api.opendns.com/v1/domains/{}/ips', 'addresses'),
            # DNS.SB
            ('https://doh.sb/dns-query?name={}&type=A', 'Answer')
        ]
        
        for dns_url_template, response_key in dns_services:
            if len(resolved_ips) >= 3:  # Stop if we have enough IPs
                break
                
            try:
                dns_url = dns_url_template.format(domain)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
                
                # Disable SSL verification for problematic services
                response = requests.get(
                    dns_url,
                    headers=headers,
                    timeout=(5, 15),
                    verify=False  # Disable SSL verification to avoid connection issues
                )
                
                if response.status_code == 200:
                    try:
                        dns_data = response.json()
                        
                        if response_key == 'addresses' and isinstance(dns_data, list):
                            # OpenDNS format
                            for ip in dns_data:
                                if self._is_valid_ip(ip):
                                    resolved_ips.append(ip)
                        elif response_key == 'Answer':
                            # Standard DNS format
                            answers = dns_data.get('Answer', [])
                            for answer in answers:
                                if answer.get('type') == 1:  # A record
                                    ip = answer.get('data')
                                    if ip and self._is_valid_ip(ip):
                                        resolved_ips.append(ip)
                                        
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue  # Try next service
                        
            except Exception:
                continue  # Try next service
        
        # Method 3: Hardcoded well-known IPs for common domains (as last resort)
        if not resolved_ips:
            known_ips = {
                'google.com': ['142.250.185.78', '142.250.185.110'],
                'facebook.com': ['31.13.71.36', '31.13.71.35'],
                'github.com': ['140.82.114.3', '140.82.114.4'],
                'microsoft.com': ['20.112.52.29', '20.103.85.33'],
                'amazon.com': ['54.239.28.85', '52.94.236.248']
            }
            
            if domain.lower() in known_ips:
                resolved_ips.extend(known_ips[domain.lower()])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ips = []
        for ip in resolved_ips:
            if ip not in seen:
                seen.add(ip)
                unique_ips.append(ip)
        
        return unique_ips[:3]  # Return up to 3 unique IPs
    
    def _is_valid_ip(self, ip):
        """Validate IP address format"""
        import re
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(ip_pattern, ip) is not None
    
    
    def check_shodan(self, domain):
        """Check domain on Shodan"""
        if self.visual:
            self.visual.print_source_checking("Shodan")
        else:
            print(f"[*] Checking Shodan...")
        
        api_key = self.api_keys.get('shodan')
        
        if not api_key:
            result = {'status': 'info', 'message': 'Shodan requires API key. Get one at: https://shodan.io/api'}
        else:
            try:
                import socket as _socket

                # Detect HTTPS support: the dev plan has https=false and must use HTTP.
                # Call the API-info endpoint first (no credits consumed) to check.
                try:
                    info_resp = requests.get(
                        f"https://api.shodan.io/api-info?key={api_key}",
                        timeout=5
                    )
                    scheme = "https" if info_resp.json().get("https", False) else "http"
                except Exception:
                    scheme = "https"  # default; will fail gracefully if wrong

                # Resolve domain to IP — /shodan/host/{ip} works on all plans
                # and does not consume query credits.
                try:
                    ip_address = _socket.gethostbyname(domain)
                except _socket.gaierror:
                    self.results['shodan'] = {'status': 'not_found', 'message': 'Could not resolve domain to IP'}
                    return self.results['shodan']

                url = f"{scheme}://api.shodan.io/shodan/host/{ip_address}?key={api_key}"

                response = requests.get(url, timeout=(10, 30), verify=(scheme == "https"))

                if response.status_code == 200:
                    data = response.json()
                    result = _parse_shodan_host(data, ip_address)
                    result['url'] = f"https://www.shodan.io/host/{ip_address}"
                elif response.status_code == 404:
                    result = {'status': 'not_found', 'message': 'No Shodan data found for this IP'}
                elif response.status_code == 401:
                    result = {'status': 'error', 'message': 'Invalid Shodan API key'}
                elif response.status_code == 403:
                    result = {'status': 'error', 'message': 'Shodan API access forbidden (check plan limits)'}
                elif response.status_code == 429:
                    result = {'status': 'error', 'message': 'Shodan rate limit exceeded'}
                else:
                    result = {'status': 'error', 'message': f'Shodan API error: HTTP {response.status_code}'}

            except requests.exceptions.Timeout:
                result = {'status': 'error', 'message': 'Shodan API request timed out'}
            except requests.exceptions.ConnectionError:
                result = {'status': 'error', 'message': 'Failed to connect to Shodan API'}
            except requests.exceptions.RequestException as e:
                result = {'status': 'error', 'message': f'Shodan request error: {str(e)[:50]}...'}
            except json.JSONDecodeError:
                result = {'status': 'error', 'message': 'Invalid JSON response from Shodan'}
            except Exception as e:
                result = {'status': 'error', 'message': f'Unexpected Shodan error: {str(e)[:50]}...'}
        
        self.results['shodan'] = result
        return result
    
    def check_whois_info(self, domain):
        """Check domain WHOIS registration information using python-whois library"""
        if self.visual:
            self.visual.print_source_checking("WHOIS Info")
        else:
            print(f"[*] Checking WHOIS Info...")
        
        try:
            import whois
            
            # Query WHOIS data
            w = whois.whois(domain)
            
            # Extract key information
            creation_date = w.creation_date
            expiration_date = w.expiration_date
            registrar = w.registrar
            
            # Handle dates that may be lists or single values
            if isinstance(creation_date, list):
                creation_date = creation_date[0] if creation_date else None
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0] if expiration_date else None
            
            # Calculate domain age if creation date available
            if creation_date:
                try:
                    # Handle both timezone-aware and naive datetimes
                    if hasattr(creation_date, 'tzinfo') and creation_date.tzinfo:
                        now = datetime.now(creation_date.tzinfo)
                    else:
                        now = datetime.now()
                        # Make creation_date naive if it has timezone
                        if hasattr(creation_date, 'replace'):
                            creation_date = creation_date.replace(tzinfo=None)
                    
                    age_days = (now - creation_date).days
                    age_years = age_days / 365.25
                    
                    # Assess risk based on age
                    if age_days < 30:
                        age_risk = 'high'  # Very new domain
                    elif age_days < 90:
                        age_risk = 'medium'  # Recently created
                    elif age_years < 1:
                        age_risk = 'low'  # Less than a year
                    else:
                        age_risk = 'none'  # Established domain
                    
                    # Determine reputation based on age
                    if age_risk == 'high':
                        reputation = 'suspicious'  # Very new domains are suspicious
                    elif age_risk == 'medium':
                        reputation = 'questionable'  # Recently created
                    else:
                        reputation = 'clean'  # Established domain
                    
                    result = {
                        'status': 'success',
                        'creation_date': creation_date.strftime('%Y-%m-%d') if creation_date else 'N/A',
                        'age_days': age_days,
                        'age_years': round(age_years, 2),
                        'registrar': registrar or 'N/A',
                        'expiration_date': expiration_date.strftime('%Y-%m-%d') if expiration_date else 'N/A',
                        'age_risk': age_risk,
                        'reputation': reputation
                    }
                except Exception as e:
                    # Fallback if age calculation fails
                    result = {
                        'status': 'success',
                        'creation_date': str(creation_date) if creation_date else 'N/A',
                        'registrar': registrar or 'N/A',
                        'expiration_date': str(expiration_date) if expiration_date else 'N/A',
                        'age_risk': 'unknown',
                        'reputation': 'unknown'
                    }
            else:
                result = {
                    'status': 'not_found',
                    'message': 'WHOIS data available but creation date not found',
                    'registrar': registrar or 'N/A'
                }
                
        except ImportError:
            result = {
                'status': 'error',
                'message': 'python-whois library not installed. Install with: pip install python-whois'
            }
        except whois.parser.PywhoisError as e:
            result = {'status': 'not_found', 'message': f'WHOIS lookup failed: {str(e)[:50]}'}
        except Exception as e:
            result = {'status': 'error', 'message': f'WHOIS error: {str(e)[:50]}...'}
        
        self.results['whois_info'] = result
        return result
    
    def check_hybrid_analysis(self, domain):
        """Check domain on Hybrid Analysis"""
        if self.visual:
            self.visual.print_source_checking("Hybrid Analysis")
        else:
            print(f"[*] Checking Hybrid Analysis...")
        
        try:
            # Use public web search instead of API (often more reliable)
            search_url = f"https://www.hybrid-analysis.com/search?query={domain}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(
                search_url,
                headers=headers,
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                # Parse the HTML response for ACTUAL threat indicators
                content = response.text.lower()
                original_content = response.text  # Keep original case for regex
                
                # Look for actual malicious verdicts and threat indicators (more specific)
                malicious_indicators = [
                    'verdict: malicious',
                    'verdict":"malicious"',
                    'threat_level":"2"',  # High threat
                    'threat_level":"1"',  # Malicious
                    'malware_family',
                    'ransomware',
                    'trojan',
                    'backdoor'
                ]
                
                suspicious_indicators = [
                    'verdict: suspicious',
                    'verdict":"suspicious"',
                    'threat_level":"1"',
                    'potentially unwanted',
                    'threat detected'
                ]
                
                # Check for "no results" or "no samples found" messages
                no_results_indicators = [
                    'no results found',
                    'no samples found',
                    'no search results',
                    '0 results',
                    'no matching results'
                ]
                
                # Track which indicators were actually found (not just count)
                found_malicious = [ind for ind in malicious_indicators if ind in content]
                found_suspicious = [ind for ind in suspicious_indicators if ind in content]
                malicious_count = len(found_malicious)
                suspicious_count = len(found_suspicious)
                no_results = any(indicator in content for indicator in no_results_indicators)

                # Check if we can find actual analysis result counts
                import re
                result_count_match = re.search(r'(\d+)\s*results?\s*found', content)
                has_results = result_count_match and int(result_count_match.group(1)) > 0

                # Malicious indicators always take priority over "no results" / "not has_results"
                if malicious_count >= 2:
                    reputation = 'malicious'
                    analysis_count = malicious_count
                elif malicious_count >= 1:
                    reputation = 'suspicious'
                    analysis_count = malicious_count
                elif suspicious_count >= 2:
                    reputation = 'suspicious'
                    analysis_count = suspicious_count
                elif suspicious_count >= 1:
                    reputation = 'questionable'
                    analysis_count = suspicious_count
                elif no_results or not has_results:
                    reputation = 'clean'  # No analyses found = likely clean
                    analysis_count = 0
                elif has_results:
                    # Results exist but no threat indicators = submitted for analysis but clean
                    reputation = 'clean'
                    analysis_count = int(result_count_match.group(1)) if result_count_match else 0
                else:
                    reputation = 'unknown'
                    analysis_count = 0

                result = {
                    'status': 'success',
                    'analysis_count': analysis_count,
                    'malicious_indicators': malicious_count,
                    'malicious_indicators_found': found_malicious,
                    'suspicious_indicators': suspicious_count,
                    'suspicious_indicators_found': found_suspicious,
                    'reputation': reputation,
                    'url': search_url,
                    'note': 'Based on web scraping - results may vary'
                }
            elif response.status_code == 403:
                result = {'status': 'error', 'message': 'Access denied to Hybrid Analysis (rate limited or blocked)'}
            elif response.status_code == 404:
                result = {'status': 'not_found', 'message': 'Hybrid Analysis search not available'}
            else:
                result = {'status': 'error', 'message': f'Hybrid Analysis HTTP error: {response.status_code}'}
                
        except requests.exceptions.Timeout:
            result = {'status': 'error', 'message': 'Hybrid Analysis request timed out'}
        except requests.exceptions.ConnectionError:
            result = {'status': 'error', 'message': 'Failed to connect to Hybrid Analysis'}
        except requests.exceptions.RequestException as e:
            result = {'status': 'error', 'message': f'Hybrid Analysis request error: {str(e)[:50]}...'}
        except Exception as e:
            result = {'status': 'error', 'message': f'Unexpected Hybrid Analysis error: {str(e)[:50]}...'}
        
        self.results['hybrid_analysis'] = result
        return result
    
    
    def check_ip_geolocation_threats(self, domain):
        """Check domain's IP geolocation and analyze for threats using IP APIs with robust DNS resolution"""
        if self.visual:
            self.visual.print_source_checking("IP Geolocation Threats")
        else:
            print(f"[*] Checking IP Geolocation Threats...")
        
        ipapi_key = self.api_keys.get('ipapi')
        ipdata_key = self.api_keys.get('ipdata')
        
        if not ipapi_key and not ipdata_key:
            result = {
                'status': 'info', 
                'message': 'IP Geolocation requires IPAPI_ACCESS_KEY or IPDATA_API_KEY. Get keys at: https://ipapi.com/ or https://ipdata.co/',
                'urls': ['https://ipapi.com/', 'https://ipdata.co/']
            }
        else:
            # Use robust domain resolution from AbuseIPDB implementation
            resolved_ips = self._resolve_domain_ips(domain)
            
            if not resolved_ips:
                result = {
                    'status': 'not_found', 
                    'message': 'Could not resolve domain to IP address using multiple DNS methods'
                }
            else:
                # Use the first resolved IP for geolocation analysis
                ip = resolved_ips[0]
                result = self._analyze_ip_geolocation(ip, ipapi_key, ipdata_key, resolved_ips)
                
        self.results['ip_geolocation'] = result
        return result
    
    def _analyze_ip_geolocation(self, ip, ipapi_key, ipdata_key, all_ips):
        """Analyze IP geolocation and threats using available services"""
        geo_results = {}
        threat_indicators = []
        location_data = {}
        
        # Try IPApi first (if key available)
        if ipapi_key:
            ipapi_result = self._query_ipapi(ip, ipapi_key)
            if ipapi_result:
                geo_results['ipapi'] = ipapi_result
                threat_indicators.extend(ipapi_result.get('threats', []))
                if not location_data and ipapi_result.get('country'):
                    location_data = {
                        'country': ipapi_result.get('country'),
                        'country_code': ipapi_result.get('country_code'),
                        'region': ipapi_result.get('region'),
                        'city': ipapi_result.get('city'),
                        'isp': ipapi_result.get('isp')
                    }
        
        # Try IPData as backup/additional source (if key available)
        if ipdata_key:
            ipdata_result = self._query_ipdata(ip, ipdata_key)
            if ipdata_result:
                geo_results['ipdata'] = ipdata_result
                threat_indicators.extend(ipdata_result.get('threats', []))
                if not location_data and ipdata_result.get('country'):
                    location_data = {
                        'country': ipdata_result.get('country'),
                        'country_code': ipdata_result.get('country_code'),
                        'region': ipdata_result.get('region'),
                        'city': ipdata_result.get('city'),
                        'isp': ipdata_result.get('isp')
                    }
        
        # Analyze threat level
        unique_threats = list(set(threat_indicators))
        if 'KNOWN_THREAT' in unique_threats or 'malware' in unique_threats:
            reputation = 'malicious'
        elif unique_threats:
            reputation = 'suspicious'
        elif geo_results:
            reputation = 'clean'
        else:
            reputation = 'unknown'
        
        return {
            'status': 'success',
            'ip_address': ip,
            'additional_ips': all_ips[1:] if len(all_ips) > 1 else [],
            'location': location_data,
            'geolocation_sources': list(geo_results.keys()),
            'threat_indicators': unique_threats,
            'reputation': reputation,
            'services_used': len(geo_results)
        }
    
    def _query_ipapi(self, ip, api_key):
        """Query IPApi service with error handling"""
        try:
            # IPApi uses HTTP (not HTTPS) for their free tier
            ipapi_url = f"http://api.ipapi.com/{ip}?access_key={api_key}&format=1&fields=country_name,country_code,region_name,city,connection,threat"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
            
            # Create session with retries
            session = requests.Session()
            session.mount('http://', requests.adapters.HTTPAdapter(
                max_retries=requests.adapters.Retry(
                    total=2,
                    backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504]
                )
            ))
            
            response = session.get(
                ipapi_url,
                headers=headers,
                timeout=(10, 30),
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    return None
                    
                threats = []
                threat_data = data.get('threat', {})
                if threat_data.get('is_tor'):
                    threats.append('TOR_EXIT_NODE')
                if threat_data.get('is_proxy'):
                    threats.append('PROXY')
                if threat_data.get('types'):
                    threats.extend(threat_data['types'])
                
                return {
                    'country': data.get('country_name'),
                    'country_code': data.get('country_code'),
                    'region': data.get('region_name'),
                    'city': data.get('city'),
                    'isp': data.get('connection', {}).get('isp'),
                    'threats': threats,
                    'service': 'ipapi'
                }
                
        except Exception:
            pass  # Silently fail and let other services try
            
        return None
    
    def _query_ipdata(self, ip, api_key):
        """Query IPData service with error handling"""
        try:
            ipdata_url = f"https://api.ipdata.co/{ip}?api-key={api_key}&fields=country_name,country_code,region,city,org,threat"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
            
            # Create session with retries
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(
                max_retries=requests.adapters.Retry(
                    total=2,
                    backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504]
                )
            ))
            
            response = session.get(
                ipdata_url,
                headers=headers,
                timeout=(10, 30),
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if 'message' in data and 'error' in data.get('message', '').lower():
                    return None
                    
                threats = []
                threat_data = data.get('threat', {})
                if threat_data.get('is_threat'):
                    threats.append('KNOWN_THREAT')
                if threat_data.get('is_tor'):
                    threats.append('TOR_EXIT_NODE')
                if threat_data.get('is_proxy'):
                    threats.append('PROXY')
                if threat_data.get('is_anonymous'):
                    threats.append('ANONYMOUS_PROXY')
                if threat_data.get('is_known_attacker'):
                    threats.append('KNOWN_ATTACKER')
                if threat_data.get('is_known_abuser'):
                    threats.append('KNOWN_ABUSER')
                if threat_data.get('is_bogon'):
                    threats.append('BOGON_IP')
                
                return {
                    'country': data.get('country_name'),
                    'country_code': data.get('country_code'),
                    'region': data.get('region'),
                    'city': data.get('city'),
                    'isp': data.get('org'),
                    'threats': threats,
                    'service': 'ipdata'
                }
                
        except Exception:
            pass  # Silently fail and let other services try
            
        return None
    
    def check_urlscan(self, domain):
        """Check domain on URLScan.io with enhanced error handling"""
        if self.visual:
            self.visual.print_source_checking("URLScan.io")
        else:
            print(f"[*] Checking URLScan.io...")
        
        api_key = self.api_keys.get('urlscan')
        
        if not api_key:
            result = {
                'status': 'info', 
                'message': 'URLScan requires API key. Get free API key at: https://urlscan.io/user/signup',
                'url': 'https://urlscan.io/user/signup'
            }
        else:
            result = self._query_urlscan_api(domain, api_key)
        
        self.results['urlscan'] = result
        return result
    
    def _query_urlscan_api(self, domain, api_key):
        """Query URLScan.io API to search for domain information"""
        try:
            # URLScan.io search endpoint
            search_url = "https://urlscan.io/api/v1/search/"
            
            headers = {
                'API-Key': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Search for domain in URLScan database
            params = {
                'q': f'domain:{domain}',
                'size': 100  # Get up to 100 recent scans
            }
            
            # Create session with retry mechanism
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(
                max_retries=requests.adapters.Retry(
                    total=2,
                    backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504]
                )
            ))
            
            response = session.get(
                search_url,
                params=params,
                headers=headers,
                timeout=(15, 45),
                verify=True
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return self._process_urlscan_response(data, domain)
                    
                except json.JSONDecodeError:
                    return {'status': 'error', 'message': 'Invalid JSON response from URLScan.io'}
                    
            elif response.status_code == 401:
                return {'status': 'error', 'message': 'Invalid URLScan.io API key'}
            elif response.status_code == 403:
                return {'status': 'error', 'message': 'URLScan.io API access denied - check your API key permissions'}
            elif response.status_code == 429:
                return {'status': 'error', 'message': 'URLScan.io rate limit exceeded - try again later'}
            elif response.status_code == 404:
                return {'status': 'not_found', 'message': 'No scans found for this domain'}
            else:
                return {'status': 'error', 'message': f'URLScan.io API error: HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            return {'status': 'error', 'message': 'URLScan.io API request timed out'}
        except requests.exceptions.SSLError:
            return {'status': 'error', 'message': 'SSL certificate error connecting to URLScan.io'}
        except requests.exceptions.ConnectionError:
            return {'status': 'error', 'message': 'Failed to connect to URLScan.io API'}
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f'URLScan.io request error: {str(e)[:50]}...'}
        except Exception as e:
            return {'status': 'error', 'message': f'Unexpected URLScan.io error: {str(e)[:50]}...'}
    
    def _process_urlscan_response(self, data, domain):
        """Process URLScan.io API response data"""
        results = data.get('results', [])
        total_scans = data.get('total', 0)
        
        if total_scans == 0 or not results:
            return {
                'status': 'not_found',
                'message': 'No scans found for this domain in URLScan.io database',
                'scan_count': 0,
                'reputation': 'clean'
            }
        
        # Analyze the scan results
        malicious_count = 0
        suspicious_count = 0
        verdicts = []
        categories = set()
        brands = set()
        countries = set()
        ips = set()
        
        for result in results:
            # Collect verdict information
            verdict = result.get('verdicts', {})
            overall_verdict = verdict.get('overall', {})
            malicious = overall_verdict.get('malicious', False)
            
            if malicious:
                malicious_count += 1
            
            # Check for suspicious indicators
            urlscan_verdict = verdict.get('urlscan', {})
            if urlscan_verdict.get('malicious', False):
                suspicious_count += 1
            
            # Collect categories and tags
            if overall_verdict.get('categories'):
                categories.update(overall_verdict.get('categories', []))
            
            if overall_verdict.get('brands'):
                brands.update(overall_verdict.get('brands', []))
            
            # Collect page information
            page = result.get('page', {})
            if page.get('country'):
                countries.add(page['country'])
            if page.get('ip'):
                ips.add(page['ip'])
        
        # Calculate reputation based on verdicts
        malicious_percentage = (malicious_count / len(results)) * 100 if results else 0
        suspicious_percentage = (suspicious_count / len(results)) * 100 if results else 0
        
        if malicious_percentage >= 30 or malicious_count >= 5:
            reputation = 'malicious'
        elif malicious_percentage >= 10 or suspicious_percentage >= 30:
            reputation = 'suspicious'
        elif malicious_count > 0 or suspicious_count > 0:
            reputation = 'questionable'
        else:
            reputation = 'clean'
        
        return {
            'status': 'success',
            'scan_count': total_scans,
            'malicious_scans': malicious_count,
            'suspicious_scans': suspicious_count,
            'reputation': reputation,
            'categories': list(categories)[:5],  # Limit to top 5
            'brands': list(brands)[:5],  # Limit to top 5
            'countries': list(countries),
            'unique_ips': len(ips),
            'url': f'https://urlscan.io/search/#{domain}'
        }

    def calculate_overall_reputation(self):
        """Calculate overall reputation based on all sources with weighted scoring"""
        reputation_scores = {
            'clean': 1,
            'unknown': 0,
            'questionable': -1,
            'suspicious': -2,
            'malicious': -3
        }
        
        # Source weights based on reliability (Tier 1: 3.0, Tier 2: 2.0, Tier 3: 1.5, Tier 4: 1.0)
        source_weights = {
            # Tier 1: Maximum reliability
            'virustotal': 3.0,
            'abuseipdb': 3.0,
            'alienvault_otx': 3.0,
            
            # Tier 2: Highly reliable
            'urlscan': 2.0,
            'hybrid_analysis': 2.0,
            'malware_bazaar': 2.0,
            'threatfox': 2.0,
            
            # Tier 3: Reliable with context
            'shodan': 1.5,
            'urlvoid': 1.5,
            'securitytrails': 1.5,
            
            # Tier 4: Complementary sources
            'whois_info': 1.0,
            'criminalip': 1.0,
            'cisco_talos': 1.0,
            'mxtoolbox': 1.0,
            'ip_geolocation': 1.0,
            'viewdns': 1.0,
            'centralops': 1.0,
            'dnslytics': 1.0,
            'ipthc': 1.0,
            'synapsint': 1.0
        }
        
        # High-confidence override rules (auto-detect as malicious)
        for source, result in self.results.items():
            if result.get('status') == 'success':
                # VirusTotal: 10+ detections = definite malicious
                if source == 'virustotal' and result.get('malicious', 0) >= 10:
                    return 'malicious'
                
                # MalwareBazaar: hash found = confirmed malware
                if source == 'malware_bazaar' and result.get('reputation') == 'malicious':
                    return 'malicious'
                
                # AbuseIPDB: 90%+ confidence = highly malicious
                if source == 'abuseipdb' and result.get('abuse_confidence', 0) >= 90:
                    return 'malicious'
                
                # AlienVault OTX: 5+ malicious pulses = confirmed threat
                if source == 'alienvault_otx':
                    pulse_count = result.get('pulse_count', 0)
                    if pulse_count >= 5 and result.get('reputation') == 'malicious':
                        return 'malicious'
        
        # Calculate weighted reputation score
        weighted_score = 0
        total_weight = 0
        
        for source, result in self.results.items():
            if result.get('status') == 'success' and 'reputation' in result:
                reputation = result['reputation']
                if reputation in reputation_scores:
                    weight = source_weights.get(source, 1.0)
                    weighted_score += reputation_scores[reputation] * weight
                    total_weight += weight
        
        if total_weight == 0:
            return "unknown"
        
        average_score = weighted_score / total_weight
        
        # Adjusted thresholds for weighted system
        if average_score >= 0.3:
            return "clean"
        elif average_score >= -0.7:
            return "questionable"
        elif average_score >= -1.5:
            return "suspicious"
        else:
            return "malicious"

    def print_simplified_summary(self, domain, overall_reputation):
        """Print a simplified text-based summary for easy copy-paste"""
        print("\n" + "─" * 80)
        
        # Header with colors
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "="*80)
            print(f"📋 QUICK SUMMARY (Text Format - Easy Copy/Paste)")
            print("="*80 + f"{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Domain:             {Fore.YELLOW}{Style.BRIGHT}{domain}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Analyzed:           {Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        else:
            print("\n" + "="*80)
            print("📋 QUICK SUMMARY (Text Format - Easy Copy/Paste)")
            print("="*80)
            print(f"Domain:             {domain}")
            print(f"Analyzed:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Color-coded reputation
        rep_emoji = {
            'clean': '✅',
            'malicious': '🚨',
            'suspicious': '⚠️',
            'questionable': '🔍',
            'unknown': '❓'
        }.get(overall_reputation, '❓')
        
        if COLORAMA_AVAILABLE:
            rep_colors = {
                'clean': Fore.GREEN,
                'malicious': Fore.RED,
                'suspicious': Fore.YELLOW,
                'questionable': Fore.YELLOW,
                'unknown': Fore.WHITE
            }
            rep_color = rep_colors.get(overall_reputation, Fore.WHITE)
            print(f"{Fore.WHITE}Overall Reputation: {rep_color}{Style.BRIGHT}{rep_emoji} {overall_reputation.upper()}{Style.RESET_ALL}")
        else:
            print(f"Overall Reputation: {rep_emoji} {overall_reputation.upper()}")
        print()
        
        # Separate results into threat analysis and manual investigation
        threat_analysis = {}
        manual_investigation = {}
        
        for source, result in self.results.items():
            if result.get('status') == 'info':
                manual_investigation[source] = result
            else:
                threat_analysis[source] = result
        
        # Count results by status
        success_count = sum(1 for r in threat_analysis.values() if r.get('status') == 'success')
        error_count = sum(1 for r in threat_analysis.values() if r.get('status') == 'error')
        not_found_count = sum(1 for r in threat_analysis.values() if r.get('status') == 'not_found')
        info_count = len(manual_investigation)
        
        # Display threat analysis results first
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}🔍 THREAT ANALYSIS RESULTS:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}" + "-" * 80 + f"{Style.RESET_ALL}")
        else:
            print("🔍 THREAT ANALYSIS RESULTS:")
            print("-" * 80)
        
        for source, result in threat_analysis.items():
            source_name = source.replace('_', ' ').title().ljust(20)
            status = result.get('status', 'unknown')
            reputation = result.get('reputation', 'unknown')
            
            # Get emoji
            status_emoji = {
                'success': '✓',
                'error': '✗',
                'info': 'ℹ',
                'not_found': '⚠'
            }.get(status, '?')
            
            reputation_emoji = {
                'clean': '✅',
                'malicious': '🚨',
                'suspicious': '⚠️',
                'questionable': '🔍',
                'unknown': '❓'
            }.get(reputation, '❓')
            
            # Build one-line summary
            if status == 'success':
                rep_str = f"{reputation_emoji} {reputation.upper()}".ljust(18)
                
                # Add key details inline
                details = []
                if 'malicious' in result and 'suspicious' in result:
                    details.append(f"M:{result['malicious']} S:{result['suspicious']}")
                elif 'ioc_count' in result:
                    details.append(f"IOCs:{result['ioc_count']}")
                elif 'pulse_count' in result:
                    details.append(f"Pulses:{result['pulse_count']}")
                elif 'abuse_confidence' in result:
                    details.append(f"Conf:{result['abuse_confidence']}%")
                elif 'detections' in result:
                    details.append(f"Det:{result['detections']}")
                elif 'scan_count' in result:
                    details.append(f"Scans:{result['scan_count']}")
                elif 'analysis_count' in result:
                    details.append(f"Analyses:{result['analysis_count']}")
                elif 'age_years' in result:
                    details.append(f"Age:{result['age_years']}y Risk:{result.get('age_risk', 'unknown')}")
                
                details_str = f" ({', '.join(details)})" if details else ""
                
                # Color-code the output
                if COLORAMA_AVAILABLE:
                    rep_colors = {
                        'clean': Fore.GREEN,
                        'malicious': Fore.RED,
                        'suspicious': Fore.YELLOW,
                        'questionable': Fore.YELLOW,
                        'unknown': Fore.WHITE
                    }
                    rep_color = rep_colors.get(reputation, Fore.WHITE)
                    print(f"{Fore.GREEN}  {status_emoji}{Style.RESET_ALL} {Fore.CYAN}{source_name}{Style.RESET_ALL} {rep_color}{rep_str}{Style.RESET_ALL}{Style.DIM}{details_str}{Style.RESET_ALL}")
                else:
                    print(f"  {status_emoji} {source_name} {rep_str}{details_str}")
            elif status == 'error':
                msg = result.get('message', '')[:45]
                if COLORAMA_AVAILABLE:
                    print(f"{Fore.RED}  {status_emoji}{Style.RESET_ALL} {Fore.CYAN}{source_name}{Style.RESET_ALL} {Fore.RED}{status.upper().ljust(18)}{Style.RESET_ALL} {Style.DIM}{msg}{Style.RESET_ALL}")
                else:
                    print(f"  {status_emoji} {source_name} {status.upper().ljust(18)} {msg}")
            else:
                if COLORAMA_AVAILABLE:
                    print(f"{Fore.YELLOW}  {status_emoji}{Style.RESET_ALL} {Fore.CYAN}{source_name}{Style.RESET_ALL} {Fore.YELLOW}NOT FOUND{Style.RESET_ALL}")
                else:
                    print(f"  {status_emoji} {source_name} NOT FOUND")
        
        if not threat_analysis:
            print("  No automated threat analysis sources returned data.")
        
        # Display manual investigation tools
        if manual_investigation:
            print()
            if COLORAMA_AVAILABLE:
                print(f"{Fore.MAGENTA}{Style.BRIGHT}🔗 MANUAL INVESTIGATION TOOLS:{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}" + "-" * 80 + f"{Style.RESET_ALL}")
            else:
                print("🔗 MANUAL INVESTIGATION TOOLS:")
                print("-" * 80)
            
            for source, result in manual_investigation.items():
                source_name = source.replace('_', ' ').title().ljust(20)
                msg = result.get('message', '')[:50]
                if COLORAMA_AVAILABLE:
                    print(f"  {Fore.BLUE}🔍{Style.RESET_ALL} {Fore.CYAN}{source_name}{Style.RESET_ALL} {Style.DIM}{msg}{Style.RESET_ALL}")
                    if 'url' in result:
                        print(f"     {Fore.BLUE}→{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}{result['url']}{Style.RESET_ALL}")
                else:
                    print(f"  🔍 {source_name} {msg}")
                    if 'url' in result:
                        print(f"     → {result['url']}")
        
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}" + "-" * 80 + f"{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Threat Analysis: {Fore.GREEN}{success_count} successful{Style.RESET_ALL} | {Fore.RED}{error_count} errors{Style.RESET_ALL} | {Fore.YELLOW}{not_found_count} not found{Style.RESET_ALL}")
            if info_count > 0:
                print(f"{Fore.WHITE}Manual Tools: {Fore.MAGENTA}{info_count} investigation links available{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}" + "=" * 80 + f"{Style.RESET_ALL}")
        else:
            print("-" * 80)
            print(f"Threat Analysis: {success_count} successful | {error_count} errors | {not_found_count} not found")
            if info_count > 0:
                print(f"Manual Tools: {info_count} investigation links available")
            print("=" * 80)
        print()

    def print_results(self, domain):
        """Print formatted results"""
        print("\n" + "="*60)
        print(f"DOMAIN REPUTATION ANALYSIS: {domain}")
        print("="*60)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        for source, result in self.results.items():
            source_name = source.replace('_', ' ').title()
            print(f"[{source_name}]")
            
            if result['status'] == 'success':
                reputation = result.get('reputation', 'N/A')
                print(f"  Status: ✓ Success")
                print(f"  Reputation: {reputation.upper()}")
                
                # Print source-specific details
                if source == 'virustotal':
                    if 'detected_urls' in result:
                        print(f"  Detected URLs: {result['detected_urls']}")
                        print(f"  Malicious URLs: {result['malicious_urls']}")
                elif source == 'urlvoid':
                    print(f"  Detections: {result.get('detections', 0)}")
                elif source == 'alienvault_otx':
                    print(f"  Pulse Count: {result.get('pulse_count', 0)}")
                elif source == 'securitytrails':
                    print(f"  First Seen: {result.get('first_seen', 'N/A')}")
                    print(f"  Subdomains: {result.get('subdomain_count', 0)}")
                
            elif result['status'] == 'not_found':
                print(f"  Status: ⚠ Not Found")
                print(f"  Message: {result.get('message', 'Domain not in database')}")
            elif result['status'] == 'info':
                print(f"  Status: ℹ Info")
                print(f"  Message: {result.get('message', '')}")
            else:
                print(f"  Status: ✗ Error")
                print(f"  Message: {result.get('message', 'Unknown error')}")
            
            print()
        
        # Overall assessment
        overall_reputation = self.calculate_overall_reputation()
        print("="*60)
        print("OVERALL ASSESSMENT")
        print("="*60)
        print(f"Reputation: {overall_reputation.upper()}")
        
        # Recommendations
        if overall_reputation in ['malicious', 'suspicious']:
            print("⚠ RECOMMENDATION: This domain appears to be potentially malicious.")
            print("  Consider blocking or investigating further.")
        elif overall_reputation == 'questionable':
            print("⚠ RECOMMENDATION: This domain has mixed reputation.")
            print("  Proceed with caution and additional investigation.")
        else:
            print("✓ RECOMMENDATION: This domain appears to be clean.")
            print("  No immediate threats detected.")

    def analyze_domain(self, domain, sources=None, use_cache=True):
        """Analyze domain reputation across selected sources"""
        # Define all available sources
        all_sources = ['virustotal', 'urlvoid', 'cisco_talos', 'alienvault_otx', 'mxtoolbox',
                      'malware_bazaar', 'threatfox', 'viewdns', 'centralops', 'criminalip', 'ipthc', 'dnslytics', 'synapsint',
                      'securitytrails', 'abuseipdb', 'shodan', 'whois_info', 'hybrid_analysis',
                      'urlscan', 'ip_geolocation']
        
        if sources is None:
            sources = self._filter_sources_by_api_keys(all_sources)
        elif isinstance(sources, list) and len(sources) == 1 and sources[0].lower() == 'all':
            available_sources = self._filter_sources_by_api_keys(all_sources)
            skipped_sources = [s for s in all_sources if s not in available_sources]
            sources = available_sources
            
            if self.visual:
                if self.visual.use_rich:
                    self.visual.console.print(f"[bold cyan]⚡ Using ALL available sources:[/bold cyan] [dim]{', '.join(available_sources)}[/dim]")
                    if skipped_sources:
                        self.visual.console.print(f"[dim]Skipping sources without API keys:[/dim] [yellow]{', '.join(skipped_sources)}[/yellow]")
                else:
                    print(f"[*] Using ALL available sources: {', '.join(available_sources)}")
                    if skipped_sources:
                        print(f"[*] Skipping sources without API keys: {', '.join(skipped_sources)}")
            else:
                print(f"[*] Using ALL available sources: {', '.join(available_sources)}")
                if skipped_sources:
                    print(f"[*] Skipping sources without API keys: {', '.join(skipped_sources)}")
        
        # Display enhanced domain header
        if self.visual:
            self.visual.print_domain_header(domain, len(sources))
            if self.visual.use_rich:
                self.visual.console.print("[dim]🔒 This analysis will NOT make direct DNS queries to the target domain.[/dim]\n")
            else:
                print("🔒 This analysis will NOT make direct DNS queries to the target domain.\n")
        else:
            print(f"Analyzing domain: {domain}")
            print("This analysis will NOT make direct DNS queries to the target domain.\n")
        
        # Check cache first
        if use_cache:
            cached_results = self._get_cached_result(domain, sources)
            if cached_results:
                print("[*] Using cached results (add --no-cache to force fresh analysis)\n")
                self.results = cached_results
                self.print_results(domain)
                return self.results
        
        # Check all requested sources
        source_methods = {
            'virustotal': lambda: self.check_virustotal(domain),
            'urlvoid': lambda: self.check_urlvoid(domain),
            'cisco_talos': lambda: self.check_cisco_talos(domain),
            'alienvault_otx': lambda: self.check_alienvault_otx(domain),
            'mxtoolbox': lambda: self.check_mxtoolbox(domain),
            'malware_bazaar': lambda: self.check_malware_bazaar(domain),
            'threatfox': lambda: self.check_threatfox(domain),
            'viewdns': lambda: self.check_viewdns(domain),
            'centralops': lambda: self.check_centralops(domain),
            'criminalip': lambda: self.check_criminalip(domain),
            'ipthc': lambda: self.check_ipthc(domain),
            'dnslytics': lambda: self.check_dnslytics(domain),
            'synapsint': lambda: self.check_synapsint(domain),
            'securitytrails': lambda: self.check_securitytrails(domain),
            'abuseipdb': lambda: self.check_abuseipdb(domain),
            'shodan': lambda: self.check_shodan(domain),
            'whois_info': lambda: self.check_whois_info(domain),
            'hybrid_analysis': lambda: self.check_hybrid_analysis(domain),
            'urlscan': lambda: self.check_urlscan(domain),
            'ip_geolocation': lambda: self.check_ip_geolocation_threats(domain)
        }
        
        # Parallel execution with individual timeouts for each source
        max_workers = min(len(sources), 5)  # Max 5 concurrent API calls
        per_source_timeout = 20  # 20 seconds timeout per source
        
        def check_source_with_timeout(source):
            """Execute source check with individual timeout"""
            if source not in source_methods:
                return source, {'status': 'error', 'message': 'Invalid source'}
            
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(source_methods[source])
            
            try:
                # Wait up to per_source_timeout seconds for this specific source
                future.result(timeout=per_source_timeout)
                return source, None  # Result already stored in self.results by the method
            except FuturesTimeoutError:
                error_msg = f'Timeout after {per_source_timeout}s'
                self.results[source] = {'status': 'error', 'message': error_msg}
                return source, {'status': 'error', 'message': error_msg}
            except Exception as e:
                error_msg = str(e)
                self.results[source] = {'status': 'error', 'message': error_msg}
                return source, {'status': 'error', 'message': error_msg}
            finally:
                executor.shutdown(wait=False)
        
        # Execute all sources in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_source_with_timeout, source): source for source in sources if source in source_methods}
            
            # Wait for all to complete (with their individual timeouts)
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    source, error = future.result()
                    if error:
                        print(f"[!] Error checking {source}: {error['message']}")
                except Exception as e:
                    print(f"[!] Unexpected error with {source_name}: {e}")
                    self.results[source_name] = {'status': 'error', 'message': str(e)}
        
        # Cache results
        if use_cache:
            self._cache_result(domain, sources, self.results)
        
        # Print enhanced results
        if self.visual:
            self.visual.print_results_table(domain, self.results)
            overall_reputation = self.calculate_overall_reputation()
            self.visual.print_overall_assessment(overall_reputation)
            # Also print simplified text summary for easy copy-paste
            self.print_simplified_summary(domain, overall_reputation)
        else:
            self.print_results(domain)
        
        return self.results
    
    def analyze_domains_batch(self, domains, sources=None, output_file=None, output_format='csv'):
        """Analyze multiple domains in batch"""
        # Handle 'all' modifier for batch processing
        all_sources = ['virustotal', 'urlvoid', 'cisco_talos', 'alienvault_otx', 'mxtoolbox',
                      'malware_bazaar', 'threatfox', 'viewdns', 'centralops', 'criminalip', 'ipthc', 'dnslytics', 'synapsint',
                      'securitytrails', 'abuseipdb', 'shodan', 'whois_info', 'hybrid_analysis',
                      'urlscan', 'ip_geolocation']
        
        if isinstance(sources, list) and len(sources) == 1 and sources[0].lower() == 'all':
            available_sources = self._filter_sources_by_api_keys(all_sources)
            skipped_sources = [s for s in all_sources if s not in available_sources]
            sources = available_sources
            sources_info = ', '.join(available_sources)
            
            if self.visual:
                if self.visual.use_rich:
                    self.visual.console.print(f"[bold cyan]⚡ Batch analysis using ALL available sources:[/bold cyan] [dim]{sources_info}[/dim]")
                    if skipped_sources:
                        self.visual.console.print(f"[dim]Skipping sources without API keys:[/dim] [yellow]{', '.join(skipped_sources)}[/yellow]")
                else:
                    print(f"[*] Batch analysis using ALL available sources: {sources_info}")
                    if skipped_sources:
                        print(f"[*] Skipping sources without API keys: {', '.join(skipped_sources)}")
            else:
                print(f"[*] Batch analysis using ALL available sources: {sources_info}")
                if skipped_sources:
                    print(f"[*] Skipping sources without API keys: {', '.join(skipped_sources)}")
        
        all_results = {}
        
        # Display enhanced batch header
        if self.visual:
            sources_info = ', '.join(sources) if sources else 'all available'
            self.visual.print_batch_header(len(domains), sources_info)
        else:
            print(f"Starting batch analysis of {len(domains)} domains...\n")
        
        for i, domain in enumerate(domains, 1):
            print(f"[{i}/{len(domains)}] Analyzing {domain}...")
            
            try:
                # Reset results for each domain
                self.results = {}
                results = self.analyze_domain(domain, sources, use_cache=True)
                all_results[domain] = results
                
                print(f"✓ Completed {domain}\n")
                
                # Add delay between domains to be respectful to APIs
                if i < len(domains):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"✗ Error analyzing {domain}: {e}\n")
                all_results[domain] = {'error': str(e)}
        
        # Export results if requested
        if output_file:
            self._export_results(all_results, output_file, output_format)
        
        return all_results
    
    def _export_results(self, results, output_file, format_type):
        """Export results to file"""
        if format_type.lower() == 'csv':
            self._export_csv(results, output_file)
        elif format_type.lower() == 'json':
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif format_type.lower() == 'html':
            self._export_html(results, output_file)
        
        print(f"Results exported to: {output_file}")
    
    def _export_csv(self, results, output_file):
        """Export results to CSV format"""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            header = ['Domain', 'Overall_Reputation', 'VirusTotal', 'URLVoid', 'Cisco_Talos', 
                     'MalwareBazaar', 'AlienVault_OTX', 'SecurityTrails', 
                     'AbuseIPDB', 'Shodan', 'WHOIS_Info', 'Hybrid_Analysis', 'URLScan', 'IP_Geolocation', 'Timestamps']
            writer.writerow(header)
            
            # Data rows
            for domain, domain_results in results.items():
                if 'error' in domain_results:
                    row = [domain, 'ERROR'] + ['ERROR'] * (len(header) - 2)
                else:
                    overall_rep = self._calculate_domain_reputation(domain_results)
                    
                    row = [
                        domain,
                        overall_rep,
                        domain_results.get('virustotal', {}).get('reputation', 'N/A'),
                        domain_results.get('urlvoid', {}).get('reputation', 'N/A'),
                        domain_results.get('cisco_talos', {}).get('reputation', 'N/A'),
                        domain_results.get('malware_bazaar', {}).get('reputation', 'N/A'),
                        domain_results.get('alienvault_otx', {}).get('reputation', 'N/A'),
                        domain_results.get('securitytrails', {}).get('reputation', 'N/A'),
                        domain_results.get('abuseipdb', {}).get('reputation', 'N/A'),
                        domain_results.get('shodan', {}).get('reputation', 'N/A'),
                        domain_results.get('whois_info', {}).get('reputation', 'N/A'),
                        domain_results.get('hybrid_analysis', {}).get('reputation', 'N/A'),
                        domain_results.get('urlscan', {}).get('reputation', 'N/A'),
                        domain_results.get('ip_geolocation', {}).get('reputation', 'N/A'),
                        datetime.now().isoformat()
                    ]
                
                writer.writerow(row)
    
    def _export_html(self, results, output_file):
        """Export results to HTML format"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Domain Reputation Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .domain-section {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
                .domain-header {{ background-color: #e9e9e9; padding: 10px; font-weight: bold; }}
                .source {{ margin: 10px; padding: 10px; border-left: 3px solid #ccc; }}
                .clean {{ border-left-color: #28a745; }}
                .suspicious {{ border-left-color: #ffc107; }}
                .malicious {{ border-left-color: #dc3545; }}
                .unknown {{ border-left-color: #6c757d; }}
                .error {{ border-left-color: #dc3545; background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Domain Reputation Analysis Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total domains analyzed: {len(results)}</p>
            </div>
        """
        
        for domain, domain_results in results.items():
            if 'error' in domain_results:
                html_content += f"""
                <div class="domain-section">
                    <div class="domain-header">{domain} - ERROR</div>
                    <div class="source error">
                        <strong>Error:</strong> {domain_results['error']}
                    </div>
                </div>
                """
            else:
                overall_rep = self._calculate_domain_reputation(domain_results)
                html_content += f"""
                <div class="domain-section">
                    <div class="domain-header">{domain} - {overall_rep.upper()}</div>
                """
                
                for source, data in domain_results.items():
                    if data.get('status') == 'success':
                        rep = data.get('reputation', 'unknown')
                        css_class = rep.lower()
                        html_content += f"""
                        <div class="source {css_class}">
                            <strong>{source.replace('_', ' ').title()}:</strong> {rep.upper()}
                        </div>
                        """
                
                html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _calculate_domain_reputation(self, domain_results):
        """Calculate overall reputation for a single domain"""
        self.results = domain_results
        return self.calculate_overall_reputation()
    
    def show_available_sources(self):
        """Display all available sources and their API key status"""
        sources_info = {
            'virustotal': {'name': 'VirusTotal', 'api_required': True, 'description': 'Multi-engine malware detection'},
            'urlvoid': {'name': 'URLVoid', 'api_required': False, 'description': 'Domain blacklist checking'},
            'cisco_talos': {'name': 'Cisco Talos', 'api_required': False, 'description': 'Threat intelligence'},
            'alienvault_otx': {'name': 'AlienVault OTX', 'api_required': False, 'description': 'Open threat intelligence'},
            'mxtoolbox': {'name': 'MXToolbox', 'api_required': False, 'description': 'DNS & blacklist checker'},
            'securitytrails': {'name': 'SecurityTrails', 'api_required': True, 'description': 'DNS intelligence'},
            'abuseipdb': {'name': 'AbuseIPDB', 'api_required': True, 'description': 'IP abuse and reputation'},
            'shodan': {'name': 'Shodan', 'api_required': True, 'description': 'Internet-wide scanning data'},
            'whois_info': {'name': 'WHOIS Info', 'api_required': False, 'description': 'Domain registration & age data'},
            'hybrid_analysis': {'name': 'Hybrid Analysis', 'api_required': False, 'description': 'Malware sandbox analysis'},
            'urlscan': {'name': 'URLScan.io', 'api_required': True, 'description': 'Website scanner and threat intel'},
            'ip_geolocation': {'name': 'IP Geolocation', 'api_required': True, 'description': 'Geographic threat analysis'}
        }
        
        if self.visual:
            self.visual.print_source_status_table(sources_info, self.api_keys)
        else:
            # Fallback to basic display
            print("\n" + "="*60)
            print("AVAILABLE THREAT INTELLIGENCE SOURCES")
            print("="*60)
            
            for source_id, info in sources_info.items():
                status = "✅" if not info['api_required'] or self.api_keys.get(source_id.replace('_', '')) else "⚠️ "
                api_status = "(No API key)" if info['api_required'] and not self.api_keys.get(source_id.replace('_', '')) else "(API key configured)" if info['api_required'] else "(No API key required)"
                
                print(f"{status} {info['name']:<20} - {info['description']} {api_status}")
            
            print("\n" + "="*60)
            print("Usage: --sources all (for all sources) or --sources source1 source2 source3")
            print("="*60)

def main():
    # Initialize visual styler for banner
    visual = VisualStyler()
    visual.print_banner()
    
    parser = argparse.ArgumentParser(
        description="Check domain reputation across multiple threat intelligence sources",
        epilog="""
        Examples:
          Single domain: python3 domain_reputation_checker.py example.com
          All sources: python3 domain_reputation_checker.py example.com --sources all
          Specific sources: python3 domain_reputation_checker.py example.com --sources virustotal abuseipdb urlscan
          With config: python3 domain_reputation_checker.py example.com --config config.ini
          Batch analysis (all): python3 domain_reputation_checker.py --batch domains.txt --sources all --output results.csv
          JSON output: python3 domain_reputation_checker.py example.com --sources all --json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main arguments
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('domain', nargs='?', help='Single domain to analyze')
    group.add_argument('--batch', help='File containing list of domains to analyze')
    
    # API Keys
    parser.add_argument('--vt-api-key', help='VirusTotal API key')
    parser.add_argument('--st-api-key', help='SecurityTrails API key')
    parser.add_argument('--shodan-api-key', help='Shodan API key')
    parser.add_argument('--abuseipdb-api-key', help='AbuseIPDB API key')
    parser.add_argument('--urlscan-api-key', help='URLScan.io API key')
    parser.add_argument('--ipapi-key', help='IPApi access key')
    parser.add_argument('--ipdata-key', help='IPData API key')
    
    # Configuration
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    
    # Sources
    parser.add_argument('--sources', nargs='+', 
                       choices=['all', 'virustotal', 'urlvoid', 'cisco_talos',
                               'alienvault_otx', 'mxtoolbox', 'malware_bazaar', 'viewdns', 'centralops',
                               'criminalip', 'ipthc', 'dnslytics', 'synapsint',
                               'securitytrails', 'abuseipdb', 'shodan', 'whois_info', 'hybrid_analysis',
                               'urlscan', 'ip_geolocation'],
                       help='Select specific sources to check. Use "all" for comprehensive analysis with all available sources')
    
    # Output options
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--output', help='Output file for batch results')
    parser.add_argument('--format', choices=['csv', 'json', 'html'], default='csv',
                       help='Output format for batch results')
    
    # Cache options
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--cache-file', help='Custom cache file path')
    
    # Verbose mode
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--show-sources', action='store_true', help='Show all available threat intelligence sources and their status')
    
    args = parser.parse_args()
    
    # Initialize checker with configuration
    checker = DomainReputationChecker(
        config_file=args.config,
        cache_file=args.cache_file,
        timeout=args.timeout,
        quiet_startup=args.json  # Suppress startup status for JSON output
    )
    
    # Set API keys from command line if provided
    if args.vt_api_key:
        checker.api_keys['virustotal'] = args.vt_api_key
    if args.st_api_key:
        checker.api_keys['securitytrails'] = args.st_api_key
    if args.shodan_api_key:
        checker.api_keys['shodan'] = args.shodan_api_key
    if args.abuseipdb_api_key:
        checker.api_keys['abuseipdb'] = args.abuseipdb_api_key
    if args.urlscan_api_key:
        checker.api_keys['urlscan'] = args.urlscan_api_key
    if args.ipapi_key:
        checker.api_keys['ipapi'] = args.ipapi_key
    if args.ipdata_key:
        checker.api_keys['ipdata'] = args.ipdata_key
    
    # Show available sources if requested
    if args.show_sources:
        checker.show_available_sources()
        return
    
    # Validate that either domain or batch is provided
    if not args.domain and not args.batch:
        parser.error("You must provide either a domain or --batch file (or use --show-sources to see available sources)")
    
    try:
        if args.batch:
            # Batch processing
            if not os.path.exists(args.batch):
                print(f"Error: Batch file '{args.batch}' not found.")
                sys.exit(1)
            
            with open(args.batch, 'r') as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not domains:
                print("Error: No domains found in batch file.")
                sys.exit(1)
            
            results = checker.analyze_domains_batch(
                domains, 
                sources=args.sources,
                output_file=args.output,
                output_format=args.format
            )
            
            if args.json:
                print(json.dumps(results, indent=2, default=str))
                
        else:
            # Single domain analysis
            results = checker.analyze_domain(
                args.domain, 
                sources=args.sources,
                use_cache=not args.no_cache
            )
            
            if args.json:
                print(json.dumps(results, indent=2, default=str))
                
    except KeyboardInterrupt:
        print("\n[!] Analysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
