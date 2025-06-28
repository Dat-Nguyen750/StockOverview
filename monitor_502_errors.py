#!/usr/bin/env python3
"""
Monitor script to track 502 errors and other API issues in real-time
"""

import time
import os
import re
from datetime import datetime
from pathlib import Path

def monitor_logs():
    """Monitor log files for 502 errors and other issues"""
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("Logs directory not found. Make sure you're running this from the project root.")
        return
    
    print("Monitoring logs for 502 errors and API issues...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    # Track file positions to only read new lines
    file_positions = {}
    
    try:
        while True:
            for log_file in log_dir.glob("*.log"):
                if log_file.name not in file_positions:
                    file_positions[log_file.name] = 0
                
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Seek to last known position
                        f.seek(file_positions[log_file.name])
                        
                        # Read new lines
                        new_lines = f.readlines()
                        file_positions[log_file.name] = f.tell()
                        
                        # Process new lines
                        for line in new_lines:
                            process_log_line(line.strip(), log_file.name)
                            
                except Exception as e:
                    print(f"Error reading {log_file}: {e}")
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def process_log_line(line, filename):
    """Process a single log line for errors and issues"""
    
    if not line:
        return
    
    # Look for 502 errors
    if "502" in line or "Bad Gateway" in line:
        timestamp = extract_timestamp(line)
        print(f"[{timestamp}] 🚨 502 ERROR in {filename}:")
        print(f"   {line}")
        print()
    
    # Look for API errors
    elif "API_ERROR" in line:
        timestamp = extract_timestamp(line)
        print(f"[{timestamp}] ⚠️  API ERROR in {filename}:")
        print(f"   {line}")
        print()
    
    # Look for rate limit issues
    elif "rate limit" in line.lower() or "429" in line:
        timestamp = extract_timestamp(line)
        print(f"[{timestamp}] 🐌 RATE LIMIT in {filename}:")
        print(f"   {line}")
        print()
    
    # Look for connection issues
    elif "connection" in line.lower() or "timeout" in line.lower():
        timestamp = extract_timestamp(line)
        print(f"[{timestamp}] 🔌 CONNECTION ISSUE in {filename}:")
        print(f"   {line}")
        print()
    
    # Look for successful evaluations
    elif "EVALUATION_SUCCESS" in line or "Successfully evaluated" in line:
        timestamp = extract_timestamp(line)
        print(f"[{timestamp}] ✅ SUCCESS in {filename}:")
        print(f"   {line}")
        print()

def extract_timestamp(line):
    """Extract timestamp from log line"""
    # Common timestamp patterns
    patterns = [
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})',  # 2025-06-28 17:23:24,726
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',       # 2025-06-28 17:23:24
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def analyze_recent_errors():
    """Analyze recent errors in log files"""
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("Logs directory not found.")
        return
    
    print("Analyzing recent errors in log files...")
    print("=" * 60)
    
    error_counts = {
        '502': 0,
        '503': 0,
        '401': 0,
        '429': 0,
        'timeout': 0,
        'connection': 0,
        'other': 0
    }
    
    for log_file in log_dir.glob("*.log"):
        print(f"\nAnalyzing {log_file.name}:")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines:
                    line_lower = line.lower()
                    
                    if "502" in line or "bad gateway" in line_lower:
                        error_counts['502'] += 1
                    elif "503" in line or "service unavailable" in line_lower:
                        error_counts['503'] += 1
                    elif "401" in line or "unauthorized" in line_lower:
                        error_counts['401'] += 1
                    elif "429" in line or "rate limit" in line_lower:
                        error_counts['429'] += 1
                    elif "timeout" in line_lower:
                        error_counts['timeout'] += 1
                    elif "connection" in line_lower:
                        error_counts['connection'] += 1
                    elif "error" in line_lower:
                        error_counts['other'] += 1
                
                # Show recent errors for this file
                recent_errors = [line.strip() for line in lines[-50:] if "error" in line.lower()]
                if recent_errors:
                    print(f"  Recent errors ({len(recent_errors)}):")
                    for error in recent_errors[-5:]:  # Show last 5 errors
                        print(f"    {error}")
                        
        except Exception as e:
            print(f"  Error reading {log_file}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("ERROR SUMMARY:")
    for error_type, count in error_counts.items():
        if count > 0:
            print(f"  {error_type.upper()}: {count}")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        analyze_recent_errors()
    else:
        print("Stock Evaluation API Error Monitor")
        print("Usage:")
        print("  python monitor_502_errors.py          # Monitor logs in real-time")
        print("  python monitor_502_errors.py analyze  # Analyze recent errors")
        print()
        
        choice = input("Enter 'monitor' to start real-time monitoring or 'analyze' to analyze recent errors: ").strip().lower()
        
        if choice == "analyze":
            analyze_recent_errors()
        else:
            monitor_logs()

if __name__ == "__main__":
    main() 