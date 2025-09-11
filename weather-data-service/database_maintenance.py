#!/usr/bin/env python3
"""
database_maintenance.py - Automated Database Maintenance

This module provides automated database maintenance functions including:
- Database optimization and vacuum
- Disk space monitoring
- Data integrity checks
- Log rotation and cleanup
- Health monitoring and alerts
"""

import os
import sqlite3
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMaintenance:
    """Handles automated database maintenance tasks"""
    
    def __init__(self, db_path: str = "data/weather_pool.db", logs_dir: str = "logs"):
        self.db_path = Path(db_path)
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
    def vacuum_database(self) -> Dict[str, any]:
        """Optimize database by vacuuming and analyzing"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Get database size before
                size_before = self.db_path.stat().st_size
                
                # Vacuum the database
                conn.execute("VACUUM")
                
                # Analyze tables for better query performance
                conn.execute("ANALYZE")
                
                # Get database size after
                size_after = self.db_path.stat().st_size
                
                # Get database statistics
                cursor = conn.cursor()
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                result = {
                    "success": True,
                    "size_before_mb": round(size_before / 1024 / 1024, 2),
                    "size_after_mb": round(size_after / 1024 / 1024, 2),
                    "space_saved_mb": round((size_before - size_after) / 1024 / 1024, 2),
                    "page_count": page_count,
                    "page_size": page_size,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Database vacuumed successfully. Space saved: {result['space_saved_mb']} MB")
                return result
                
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_disk_space(self) -> Dict[str, any]:
        """Check available disk space and database size"""
        try:
            # Get disk usage
            statvfs = os.statvfs(self.db_path.parent)
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_available
            used_space = total_space - free_space
            
            # Get database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Get logs directory size
            logs_size = sum(f.stat().st_size for f in self.logs_dir.rglob('*') if f.is_file())
            
            result = {
                "success": True,
                "total_space_gb": round(total_space / 1024 / 1024 / 1024, 2),
                "free_space_gb": round(free_space / 1024 / 1024 / 1024, 2),
                "used_space_gb": round(used_space / 1024 / 1024 / 1024, 2),
                "free_percentage": round((free_space / total_space) * 100, 2),
                "database_size_mb": round(db_size / 1024 / 1024, 2),
                "logs_size_mb": round(logs_size / 1024 / 1024, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add warnings
            warnings = []
            if result["free_percentage"] < 10:
                warnings.append("CRITICAL: Less than 10% disk space remaining")
            elif result["free_percentage"] < 20:
                warnings.append("WARNING: Less than 20% disk space remaining")
            
            if result["logs_size_mb"] > 1000:  # 1GB
                warnings.append("WARNING: Logs directory exceeds 1GB")
            
            result["warnings"] = warnings
            return result
            
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_data_integrity(self) -> Dict[str, any]:
        """Check database integrity and data consistency"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                # Get table statistics
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                table_stats = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_stats[table] = count
                
                # Check for orphaned records
                cursor.execute("""
                    SELECT COUNT(*) FROM daily_weather_data d
                    LEFT JOIN all_canadian_stations s ON d.station_id = s.station_id
                    WHERE s.station_id IS NULL
                """)
                orphaned_records = cursor.fetchone()[0]
                
                # Check date ranges
                cursor.execute("""
                    SELECT 
                        MIN(date) as min_date,
                        MAX(date) as max_date,
                        COUNT(DISTINCT station_id) as unique_stations
                    FROM daily_weather_data
                """)
                date_stats = cursor.fetchone()
                
                result = {
                    "success": True,
                    "integrity_check": integrity_result,
                    "table_counts": table_stats,
                    "orphaned_records": orphaned_records,
                    "date_range": {
                        "min_date": date_stats[0],
                        "max_date": date_stats[1],
                        "unique_stations": date_stats[2]
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add warnings
                warnings = []
                if integrity_result != "ok":
                    warnings.append(f"CRITICAL: Database integrity check failed: {integrity_result}")
                
                if orphaned_records > 0:
                    warnings.append(f"WARNING: {orphaned_records} orphaned records found")
                
                result["warnings"] = warnings
                return result
                
        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def rotate_logs(self, keep_days: int = 30) -> Dict[str, any]:
        """Rotate old log files to save disk space"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_files = []
            total_size_freed = 0
            
            for log_file in self.logs_dir.rglob("*.log"):
                if log_file.is_file():
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        deleted_files.append(str(log_file))
                        total_size_freed += file_size
            
            result = {
                "success": True,
                "files_deleted": len(deleted_files),
                "size_freed_mb": round(total_size_freed / 1024 / 1024, 2),
                "deleted_files": deleted_files,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Log rotation completed. Deleted {len(deleted_files)} files, freed {result['size_freed_mb']} MB")
            return result
            
        except Exception as e:
            logger.error(f"Log rotation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_old_data(self, keep_years: int = 5) -> Dict[str, any]:
        """Remove old weather data to save space (optional)"""
        try:
            cutoff_year = datetime.now().year - keep_years
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Count records to be deleted
                cursor.execute("""
                    SELECT COUNT(*) FROM daily_weather_data 
                    WHERE strftime('%Y', date) < ?
                """, (str(cutoff_year),))
                records_to_delete = cursor.fetchone()[0]
                
                if records_to_delete > 0:
                    # Delete old records
                    cursor.execute("""
                        DELETE FROM daily_weather_data 
                        WHERE strftime('%Y', date) < ?
                    """, (str(cutoff_year),))
                    
                    # Vacuum to reclaim space
                    conn.execute("VACUUM")
                
                result = {
                    "success": True,
                    "records_deleted": records_to_delete,
                    "cutoff_year": cutoff_year,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Data cleanup completed. Deleted {records_to_delete} records older than {cutoff_year}")
                return result
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_full_maintenance(self) -> Dict[str, any]:
        """Run all maintenance tasks"""
        logger.info("Starting full database maintenance...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {}
        }
        
        # Run all maintenance tasks
        results["tasks"]["disk_space"] = self.check_disk_space()
        results["tasks"]["data_integrity"] = self.check_data_integrity()
        results["tasks"]["database_vacuum"] = self.vacuum_database()
        results["tasks"]["log_rotation"] = self.rotate_logs()
        
        # Only run data cleanup if disk space is low
        disk_result = results["tasks"]["disk_space"]
        if disk_result.get("success") and disk_result.get("free_percentage", 100) < 30:
            results["tasks"]["data_cleanup"] = self.cleanup_old_data()
        else:
            results["tasks"]["data_cleanup"] = {"skipped": "Sufficient disk space available"}
        
        # Calculate overall success
        failed_tasks = [name for name, result in results["tasks"].items() 
                       if not result.get("success", False) and "skipped" not in result]
        
        results["overall_success"] = len(failed_tasks) == 0
        results["failed_tasks"] = failed_tasks
        
        # Log summary
        if results["overall_success"]:
            logger.info("Full database maintenance completed successfully")
        else:
            logger.warning(f"Database maintenance completed with {len(failed_tasks)} failed tasks: {failed_tasks}")
        
        return results

def main():
    """Command line interface for database maintenance"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Maintenance Tool")
    parser.add_argument("--task", choices=[
        "vacuum", "disk-space", "integrity", "rotate-logs", "cleanup", "full"
    ], default="full", help="Maintenance task to run")
    parser.add_argument("--db-path", default="data/weather_pool.db", help="Database path")
    parser.add_argument("--logs-dir", default="logs", help="Logs directory")
    parser.add_argument("--keep-years", type=int, default=5, help="Years of data to keep")
    parser.add_argument("--keep-days", type=int, default=30, help="Days of logs to keep")
    
    args = parser.parse_args()
    
    maintenance = DatabaseMaintenance(args.db_path, args.logs_dir)
    
    if args.task == "vacuum":
        result = maintenance.vacuum_database()
    elif args.task == "disk-space":
        result = maintenance.check_disk_space()
    elif args.task == "integrity":
        result = maintenance.check_data_integrity()
    elif args.task == "rotate-logs":
        result = maintenance.rotate_logs(args.keep_days)
    elif args.task == "cleanup":
        result = maintenance.cleanup_old_data(args.keep_years)
    elif args.task == "full":
        result = maintenance.run_full_maintenance()
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
