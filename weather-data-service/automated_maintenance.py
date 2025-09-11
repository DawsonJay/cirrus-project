#!/usr/bin/env python3
"""
automated_maintenance.py - Automated System Maintenance

This script runs comprehensive maintenance tasks including:
- Database optimization
- Log rotation
- Health monitoring
- Alert generation
- System cleanup
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database_maintenance import DatabaseMaintenance
from health_monitor import HealthMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedMaintenance:
    """Handles automated system maintenance"""
    
    def __init__(self, db_path: str = "data/weather_pool.db", logs_dir: str = "logs"):
        self.db_path = db_path
        self.logs_dir = logs_dir
        self.db_maintenance = DatabaseMaintenance(db_path, logs_dir)
        self.health_monitor = HealthMonitor(db_path, logs_dir)
        
        # Ensure logs directory exists
        Path(logs_dir).mkdir(exist_ok=True)
    
    def run_daily_maintenance(self) -> Dict[str, Any]:
        """Run daily maintenance tasks"""
        logger.info("Starting daily maintenance...")
        
        maintenance_log = {
            "timestamp": datetime.now().isoformat(),
            "type": "daily_maintenance",
            "tasks": {}
        }
        
        try:
            # 1. Health check
            logger.info("Running health check...")
            health_report = self.health_monitor.generate_health_report()
            maintenance_log["tasks"]["health_check"] = health_report
            
            # 2. Database maintenance
            logger.info("Running database maintenance...")
            db_maintenance = self.db_maintenance.run_full_maintenance()
            maintenance_log["tasks"]["database_maintenance"] = db_maintenance
            
            # 3. Log rotation (if needed)
            if health_report["checks"]["system_resources"].get("success", False):
                disk_usage = health_report["checks"]["system_resources"]["disk"]["usage_percent"]
                if disk_usage > 70:  # If disk usage > 70%
                    logger.info("High disk usage detected, running log rotation...")
                    log_rotation = self.db_maintenance.rotate_logs(keep_days=14)  # Keep only 14 days
                    maintenance_log["tasks"]["log_rotation"] = log_rotation
            
            # 4. Generate maintenance summary
            maintenance_log["summary"] = self._generate_maintenance_summary(maintenance_log)
            
            # 5. Save maintenance log
            self._save_maintenance_log(maintenance_log)
            
            logger.info("Daily maintenance completed successfully")
            return maintenance_log
            
        except Exception as e:
            logger.error(f"Daily maintenance failed: {e}")
            maintenance_log["error"] = str(e)
            maintenance_log["success"] = False
            return maintenance_log
    
    def run_weekly_maintenance(self) -> Dict[str, Any]:
        """Run weekly maintenance tasks"""
        logger.info("Starting weekly maintenance...")
        
        maintenance_log = {
            "timestamp": datetime.now().isoformat(),
            "type": "weekly_maintenance",
            "tasks": {}
        }
        
        try:
            # 1. Full health report
            logger.info("Generating comprehensive health report...")
            health_report = self.health_monitor.generate_health_report()
            maintenance_log["tasks"]["health_report"] = health_report
            
            # 2. Database optimization
            logger.info("Running database optimization...")
            db_optimization = self.db_maintenance.vacuum_database()
            maintenance_log["tasks"]["database_optimization"] = db_optimization
            
            # 3. Data integrity check
            logger.info("Running data integrity check...")
            integrity_check = self.db_maintenance.check_data_integrity()
            maintenance_log["tasks"]["data_integrity"] = integrity_check
            
            # 4. Log cleanup
            logger.info("Cleaning up old logs...")
            log_cleanup = self.db_maintenance.rotate_logs(keep_days=30)
            maintenance_log["tasks"]["log_cleanup"] = log_cleanup
            
            # 5. Generate weekly report
            maintenance_log["summary"] = self._generate_maintenance_summary(maintenance_log)
            
            # 6. Save maintenance log
            self._save_maintenance_log(maintenance_log)
            
            logger.info("Weekly maintenance completed successfully")
            return maintenance_log
            
        except Exception as e:
            logger.error(f"Weekly maintenance failed: {e}")
            maintenance_log["error"] = str(e)
            maintenance_log["success"] = False
            return maintenance_log
    
    def run_emergency_maintenance(self) -> Dict[str, Any]:
        """Run emergency maintenance when issues are detected"""
        logger.warning("Starting emergency maintenance...")
        
        maintenance_log = {
            "timestamp": datetime.now().isoformat(),
            "type": "emergency_maintenance",
            "tasks": {}
        }
        
        try:
            # 1. Immediate health check
            logger.info("Running emergency health check...")
            health_report = self.health_monitor.generate_health_report()
            maintenance_log["tasks"]["emergency_health_check"] = health_report
            
            # 2. Database integrity check
            logger.info("Checking database integrity...")
            integrity_check = self.db_maintenance.check_data_integrity()
            maintenance_log["tasks"]["integrity_check"] = integrity_check
            
            # 3. Disk space check
            logger.info("Checking disk space...")
            disk_check = self.db_maintenance.check_disk_space()
            maintenance_log["tasks"]["disk_check"] = disk_check
            
            # 4. Emergency cleanup if needed
            if disk_check.get("success") and disk_check.get("free_percentage", 100) < 20:
                logger.warning("Critical disk space, running emergency cleanup...")
                emergency_cleanup = self.db_maintenance.cleanup_old_data(keep_years=2)
                maintenance_log["tasks"]["emergency_cleanup"] = emergency_cleanup
            
            # 5. Log rotation
            logger.info("Running emergency log rotation...")
            log_rotation = self.db_maintenance.rotate_logs(keep_days=7)
            maintenance_log["tasks"]["emergency_log_rotation"] = log_rotation
            
            # 6. Generate emergency report
            maintenance_log["summary"] = self._generate_maintenance_summary(maintenance_log)
            
            # 7. Save maintenance log
            self._save_maintenance_log(maintenance_log)
            
            logger.warning("Emergency maintenance completed")
            return maintenance_log
            
        except Exception as e:
            logger.error(f"Emergency maintenance failed: {e}")
            maintenance_log["error"] = str(e)
            maintenance_log["success"] = False
            return maintenance_log
    
    def _generate_maintenance_summary(self, maintenance_log: Dict[str, Any]) -> Dict[str, Any]:
        """Generate maintenance summary"""
        summary = {
            "total_tasks": len(maintenance_log["tasks"]),
            "successful_tasks": 0,
            "failed_tasks": 0,
            "warnings": [],
            "recommendations": []
        }
        
        for task_name, task_result in maintenance_log["tasks"].items():
            if task_result.get("success", False):
                summary["successful_tasks"] += 1
            else:
                summary["failed_tasks"] += 1
            
            # Collect warnings
            if "warnings" in task_result:
                summary["warnings"].extend(task_result["warnings"])
        
        # Generate recommendations based on warnings
        if any("CRITICAL" in warning for warning in summary["warnings"]):
            summary["recommendations"].append("CRITICAL issues detected - immediate attention required")
        
        if any("HIGH" in warning for warning in summary["warnings"]):
            summary["recommendations"].append("High priority issues detected - monitor closely")
        
        if summary["failed_tasks"] > 0:
            summary["recommendations"].append(f"{summary['failed_tasks']} maintenance tasks failed - review logs")
        
        if len(summary["warnings"]) > 10:
            summary["recommendations"].append("High number of warnings - consider system review")
        
        return summary
    
    def _save_maintenance_log(self, maintenance_log: Dict[str, Any]):
        """Save maintenance log to file"""
        try:
            log_file = Path(self.logs_dir) / f"maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w') as f:
                json.dump(maintenance_log, f, indent=2)
            logger.info(f"Maintenance log saved to {log_file}")
        except Exception as e:
            logger.error(f"Failed to save maintenance log: {e}")
    
    def check_maintenance_needed(self) -> Dict[str, Any]:
        """Check if maintenance is needed based on system state"""
        try:
            health_report = self.health_monitor.generate_health_report()
            
            maintenance_needed = {
                "timestamp": datetime.now().isoformat(),
                "maintenance_required": False,
                "urgency": "low",
                "reasons": [],
                "recommended_actions": []
            }
            
            # Check system resources
            system_health = health_report["checks"]["system_resources"]
            if system_health.get("success"):
                if system_health["disk"]["usage_percent"] > 90:
                    maintenance_needed["maintenance_required"] = True
                    maintenance_needed["urgency"] = "critical"
                    maintenance_needed["reasons"].append("Critical disk space")
                    maintenance_needed["recommended_actions"].append("emergency_maintenance")
                elif system_health["disk"]["usage_percent"] > 80:
                    maintenance_needed["maintenance_required"] = True
                    maintenance_needed["urgency"] = "high"
                    maintenance_needed["reasons"].append("High disk usage")
                    maintenance_needed["recommended_actions"].append("daily_maintenance")
            
            # Check database health
            db_health = health_report["checks"]["database_health"]
            if db_health.get("success"):
                if db_health.get("recent_records_7d", 0) == 0:
                    maintenance_needed["maintenance_required"] = True
                    maintenance_needed["urgency"] = "high"
                    maintenance_needed["reasons"].append("No recent data collection")
                    maintenance_needed["recommended_actions"].append("check_collection_process")
            
            # Check error rates
            collection_status = health_report["checks"]["collection_status"]
            if collection_status.get("success"):
                if collection_status.get("error_count_24h", 0) > 10:
                    maintenance_needed["maintenance_required"] = True
                    maintenance_needed["urgency"] = "medium"
                    maintenance_needed["reasons"].append("High error rate")
                    maintenance_needed["recommended_actions"].append("review_logs")
            
            return maintenance_needed
            
        except Exception as e:
            logger.error(f"Maintenance check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "maintenance_required": True,
                "urgency": "high",
                "reasons": [f"Check failed: {e}"],
                "recommended_actions": ["emergency_maintenance"]
            }

def main():
    """Command line interface for automated maintenance"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Maintenance Tool")
    parser.add_argument("--type", choices=[
        "daily", "weekly", "emergency", "check"
    ], default="daily", help="Type of maintenance to run")
    parser.add_argument("--db-path", default="data/weather_pool.db", help="Database path")
    parser.add_argument("--logs-dir", default="logs", help="Logs directory")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    maintenance = AutomatedMaintenance(args.db_path, args.logs_dir)
    
    if args.type == "daily":
        result = maintenance.run_daily_maintenance()
    elif args.type == "weekly":
        result = maintenance.run_weekly_maintenance()
    elif args.type == "emergency":
        result = maintenance.run_emergency_maintenance()
    elif args.type == "check":
        result = maintenance.check_maintenance_needed()
    
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        # Text output
        print(f"Maintenance Type: {result.get('type', 'unknown')}")
        print(f"Timestamp: {result.get('timestamp', 'unknown')}")
        
        if "summary" in result:
            summary = result["summary"]
            print(f"Tasks: {summary.get('successful_tasks', 0)}/{summary.get('total_tasks', 0)} successful")
            if summary.get("warnings"):
                print("Warnings:")
                for warning in summary["warnings"]:
                    print(f"  - {warning}")
            if summary.get("recommendations"):
                print("Recommendations:")
                for rec in summary["recommendations"]:
                    print(f"  - {rec}")
        
        if result.get("error"):
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
