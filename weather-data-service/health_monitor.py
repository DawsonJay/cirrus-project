#!/usr/bin/env python3
"""
health_monitor.py - System Health Monitoring

This module provides comprehensive health monitoring for the weather data collection system:
- Service health checks
- Performance monitoring
- Alert generation
- System status reporting
"""

import os
import sqlite3
import psutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitors system health and performance"""
    
    def __init__(self, db_path: str = "data/weather_pool.db", logs_dir: str = "logs"):
        self.db_path = Path(db_path)
        self.logs_dir = Path(logs_dir)
        
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process information
            process = psutil.Process()
            process_memory = process.memory_info()
            
            result = {
                "success": True,
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                    "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                    "used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                    "usage_percent": memory.percent,
                    "swap_total_gb": round(swap.total / 1024 / 1024 / 1024, 2),
                    "swap_used_gb": round(swap.used / 1024 / 1024 / 1024, 2)
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2)
                },
                "process": {
                    "memory_mb": round(process_memory.rss / 1024 / 1024, 2),
                    "cpu_percent": process.cpu_percent(),
                    "status": process.status()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add warnings
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"HIGH CPU: {cpu_percent}% usage")
            if memory.percent > 80:
                warnings.append(f"HIGH MEMORY: {memory.percent}% usage")
            if disk.percent > 90:
                warnings.append(f"CRITICAL DISK: {disk.percent}% usage")
            elif disk.percent > 80:
                warnings.append(f"HIGH DISK: {disk.percent}% usage")
            
            result["warnings"] = warnings
            return result
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance"""
        try:
            if not self.db_path.exists():
                return {
                    "success": False,
                    "error": "Database file does not exist",
                    "timestamp": datetime.now().isoformat()
                }
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Check database size
                db_size = self.db_path.stat().st_size
                
                # Get table information
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                table_info = {}
                total_records = 0
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_info[table] = count
                    total_records += count
                
                # Check recent data
                cursor.execute("""
                    SELECT COUNT(*) FROM daily_weather_data 
                    WHERE date >= date('now', '-7 days')
                """)
                recent_records = cursor.fetchone()[0]
                
                # Check data freshness
                cursor.execute("""
                    SELECT MAX(date) FROM daily_weather_data
                """)
                latest_date = cursor.fetchone()[0]
                
                # Check for errors in logs
                error_count = self._count_recent_errors()
                
                result = {
                    "success": True,
                    "database_size_mb": round(db_size / 1024 / 1024, 2),
                    "table_counts": table_info,
                    "total_records": total_records,
                    "recent_records_7d": recent_records,
                    "latest_data_date": latest_date,
                    "recent_errors": error_count,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add warnings
                warnings = []
                if recent_records == 0:
                    warnings.append("WARNING: No data collected in the last 7 days")
                
                if error_count > 10:
                    warnings.append(f"HIGH ERROR RATE: {error_count} errors in last 24h")
                
                if db_size > 1024 * 1024 * 1024:  # 1GB
                    warnings.append(f"LARGE DATABASE: {result['database_size_mb']} MB")
                
                result["warnings"] = warnings
                return result
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_collection_status(self) -> Dict[str, Any]:
        """Check data collection status and recent activity"""
        try:
            # Check if main.py is running
            running_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'main.py' in cmdline or 'collection.py' in cmdline:
                            running_processes.append({
                                "pid": proc.info['pid'],
                                "cmdline": cmdline
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Check recent log files
            log_files = list(self.logs_dir.glob("*.log"))
            recent_logs = []
            
            for log_file in log_files:
                if log_file.is_file():
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime > datetime.now() - timedelta(hours=24):
                        recent_logs.append({
                            "file": str(log_file.name),
                            "size_mb": round(log_file.stat().st_size / 1024 / 1024, 2),
                            "modified": mtime.isoformat()
                        })
            
            # Check for collection errors
            error_patterns = ["ERROR", "CRITICAL", "FAILED", "Exception"]
            error_count = 0
            
            for log_file in recent_logs:
                try:
                    with open(self.logs_dir / log_file["file"], 'r') as f:
                        content = f.read()
                        for pattern in error_patterns:
                            error_count += content.count(pattern)
                except Exception:
                    pass
            
            result = {
                "success": True,
                "running_processes": running_processes,
                "recent_logs": recent_logs,
                "error_count_24h": error_count,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add warnings
            warnings = []
            if not running_processes:
                warnings.append("WARNING: No collection processes running")
            
            if error_count > 5:
                warnings.append(f"HIGH ERROR COUNT: {error_count} errors in logs")
            
            result["warnings"] = warnings
            return result
            
        except Exception as e:
            logger.error(f"Collection status check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health"""
        try:
            import requests
            
            # Check if API is running
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                api_status = {
                    "running": True,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except requests.exceptions.RequestException as e:
                api_status = {
                    "running": False,
                    "error": str(e)
                }
            
            result = {
                "success": True,
                "api": api_status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add warnings
            warnings = []
            if not api_status.get("running", False):
                warnings.append("API not responding")
            elif api_status.get("status_code") != 200:
                warnings.append(f"API returned status {api_status.get('status_code')}")
            
            result["warnings"] = warnings
            return result
            
        except ImportError:
            return {
                "success": False,
                "error": "requests library not available",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _count_recent_errors(self) -> int:
        """Count recent errors in log files"""
        error_count = 0
        error_patterns = ["ERROR", "CRITICAL", "FAILED", "Exception"]
        
        try:
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.is_file():
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime > datetime.now() - timedelta(hours=24):
                        with open(log_file, 'r') as f:
                            content = f.read()
                            for pattern in error_patterns:
                                error_count += content.count(pattern)
        except Exception:
            pass
        
        return error_count
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        logger.info("Generating health report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Run all health checks
        report["checks"]["system_resources"] = self.check_system_resources()
        report["checks"]["database_health"] = self.check_database_health()
        report["checks"]["collection_status"] = self.check_collection_status()
        report["checks"]["api_health"] = self.check_api_health()
        
        # Calculate overall health
        all_warnings = []
        failed_checks = []
        
        for check_name, check_result in report["checks"].items():
            if not check_result.get("success", False):
                failed_checks.append(check_name)
            if "warnings" in check_result:
                all_warnings.extend(check_result["warnings"])
        
        report["overall_health"] = {
            "status": "healthy" if len(failed_checks) == 0 else "unhealthy",
            "failed_checks": failed_checks,
            "total_warnings": len(all_warnings),
            "warnings": all_warnings
        }
        
        # Log summary
        if report["overall_health"]["status"] == "healthy":
            logger.info("System health check passed")
        else:
            logger.warning(f"System health check failed: {failed_checks}")
        
        return report

def main():
    """Command line interface for health monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health Monitoring Tool")
    parser.add_argument("--check", choices=[
        "system", "database", "collection", "api", "all"
    ], default="all", help="Health check to run")
    parser.add_argument("--db-path", default="data/weather_pool.db", help="Database path")
    parser.add_argument("--logs-dir", default="logs", help="Logs directory")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(args.db_path, args.logs_dir)
    
    if args.check == "system":
        result = monitor.check_system_resources()
    elif args.check == "database":
        result = monitor.check_database_health()
    elif args.check == "collection":
        result = monitor.check_collection_status()
    elif args.check == "api":
        result = monitor.check_api_health()
    elif args.check == "all":
        result = monitor.generate_health_report()
    
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        # Text output
        if "overall_health" in result:
            print(f"Overall Health: {result['overall_health']['status']}")
            if result['overall_health']['warnings']:
                print("Warnings:")
                for warning in result['overall_health']['warnings']:
                    print(f"  - {warning}")
        else:
            print(f"Check Result: {'SUCCESS' if result.get('success') else 'FAILED'}")
            if result.get('warnings'):
                print("Warnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")

if __name__ == "__main__":
    main()
