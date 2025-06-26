#!/usr/bin/env python3
"""
Stock Evaluator Pro - Monitoring and Security Dashboard
Monitors application health, security events, and usage patterns
"""

import json
import time
import requests
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityMonitor:
    def __init__(self, web_app_url="http://localhost:5000", api_url="http://localhost:8000"):
        self.web_app_url = web_app_url
        self.api_url = api_url
        self.security_events = []
        self.usage_stats = defaultdict(int)
        self.error_counts = defaultdict(int)
        
    def check_health(self):
        """Check health of all services"""
        health_status = {
            'web_app': False,
            'api': False,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.get(f"{self.web_app_url}/health", timeout=5)
            health_status['web_app'] = response.status_code == 200
        except Exception as e:
            logger.error(f"Web app health check failed: {e}")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            health_status['api'] = response.status_code == 200
        except Exception as e:
            logger.error(f"API health check failed: {e}")
        
        return health_status
    
    def get_security_dashboard(self):
        """Get security monitoring data"""
        try:
            response = requests.get(f"{self.web_app_url}/admin/security", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get security dashboard: {e}")
        
        return {}
    
    def analyze_logs(self, log_file='logs/web_app.log', hours=24):
        """Analyze log files for patterns and threats"""
        if not os.path.exists(log_file):
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        analysis = {
            'total_requests': 0,
            'security_events': 0,
            'error_events': 0,
            'top_ips': Counter(),
            'top_user_agents': Counter(),
            'suspicious_patterns': [],
            'rate_limit_violations': 0,
            'api_errors': 0
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if 'SECURITY_EVENT' in line:
                        analysis['security_events'] += 1
                        # Extract IP from security events
                        if 'ip_address' in line:
                            try:
                                event_data = json.loads(line.split('SECURITY_EVENT: ')[1])
                                analysis['top_ips'][event_data.get('ip_address', 'unknown')] += 1
                            except:
                                pass
                    
                    elif 'ERROR' in line or 'WARNING' in line:
                        analysis['error_events'] += 1
                        if '429' in line or 'rate_limit' in line:
                            analysis['rate_limit_violations'] += 1
                        if 'API_ERROR' in line:
                            analysis['api_errors'] += 1
                    
                    elif 'INFO' in line and 'API_REQUEST' in line:
                        analysis['total_requests'] += 1
                        
        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
        
        return analysis
    
    def generate_report(self):
        """Generate comprehensive monitoring report"""
        health = self.check_health()
        security = self.get_security_dashboard()
        logs = self.analyze_logs()
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'health_status': health,
            'security_summary': {
                'suspicious_ips_count': security.get('total_suspicious_events', 0),
                'failed_attempts_count': security.get('total_failed_attempts', 0),
                'suspicious_ips': list(security.get('suspicious_ips', {}).keys())[:10]
            },
            'usage_summary': {
                'total_requests': logs.get('total_requests', 0),
                'security_events': logs.get('security_events', 0),
                'error_events': logs.get('error_events', 0),
                'rate_limit_violations': logs.get('rate_limit_violations', 0),
                'api_errors': logs.get('api_errors', 0)
            },
            'alerts': []
        }
        
        # Generate alerts
        if not health['web_app']:
            report['alerts'].append('CRITICAL: Web application is down')
        
        if not health['api']:
            report['alerts'].append('CRITICAL: API backend is down')
        
        if logs.get('security_events', 0) > 10:
            report['alerts'].append('WARNING: High number of security events detected')
        
        if logs.get('rate_limit_violations', 0) > 5:
            report['alerts'].append('WARNING: Multiple rate limit violations detected')
        
        if logs.get('api_errors', 0) > 10:
            report['alerts'].append('WARNING: High number of API errors detected')
        
        return report
    
    def print_report(self, report):
        """Print formatted monitoring report"""
        print("\n" + "="*60)
        print("STOCK EVALUATOR PRO - MONITORING REPORT")
        print("="*60)
        print(f"Generated: {report['timestamp']}")
        
        # Health Status
        print("\n🏥 HEALTH STATUS:")
        health = report['health_status']
        print(f"  Web App: {'✅ Healthy' if health['web_app'] else '❌ Down'}")
        print(f"  API: {'✅ Healthy' if health['api'] else '❌ Down'}")
        
        # Security Summary
        print("\n🛡️ SECURITY SUMMARY:")
        security = report['security_summary']
        print(f"  Suspicious IPs: {security['suspicious_ips_count']}")
        print(f"  Failed Attempts: {security['failed_attempts_count']}")
        if security['suspicious_ips']:
            print(f"  Top Suspicious IPs: {', '.join(security['suspicious_ips'])}")
        
        # Usage Summary
        print("\n📊 USAGE SUMMARY:")
        usage = report['usage_summary']
        print(f"  Total Requests: {usage['total_requests']}")
        print(f"  Security Events: {usage['security_events']}")
        print(f"  Error Events: {usage['error_events']}")
        print(f"  Rate Limit Violations: {usage['rate_limit_violations']}")
        print(f"  API Errors: {usage['api_errors']}")
        
        # Alerts
        if report['alerts']:
            print("\n🚨 ALERTS:")
            for alert in report['alerts']:
                print(f"  {alert}")
        else:
            print("\n✅ No alerts - All systems operational")
        
        print("\n" + "="*60)

def main():
    """Main monitoring function"""
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    monitor = SecurityMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Continuous monitoring mode
        print("Starting continuous monitoring... Press Ctrl+C to stop")
        try:
            while True:
                report = monitor.generate_report()
                monitor.print_report(report)
                time.sleep(300)  # Check every 5 minutes
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        # Single report
        report = monitor.generate_report()
        monitor.print_report(report)
        
        # Save report to file
        report_file = f"logs/monitor_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_file}")

if __name__ == "__main__":
    main() 