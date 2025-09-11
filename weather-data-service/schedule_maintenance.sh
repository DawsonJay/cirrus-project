#!/bin/bash
# schedule_maintenance.sh - Schedule automated maintenance tasks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Weather Data Collection - Maintenance Scheduler${NC}"
echo "========================================================"

# Get the absolute path to the backend directory
BACKEND_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MAINTENANCE_SCRIPT="$BACKEND_DIR/automated_maintenance.py"
MAIN_SCRIPT="$BACKEND_DIR/main.py"

echo -e "${YELLOW}📁 Backend directory: $BACKEND_DIR${NC}"
echo -e "${YELLOW}🔧 Maintenance script: $MAINTENANCE_SCRIPT${NC}"
echo -e "${YELLOW}🐍 Main script: $MAIN_SCRIPT${NC}"

# Check if scripts exist
if [ ! -f "$MAINTENANCE_SCRIPT" ]; then
    echo -e "${RED}❌ Error: automated_maintenance.py not found${NC}"
    exit 1
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}❌ Error: main.py not found${NC}"
    exit 1
fi

# Check for required environment variables
if [ -z "$NOAA_CDO_TOKEN" ]; then
    echo -e "${RED}❌ Error: NOAA_CDO_TOKEN environment variable is not set${NC}"
    echo -e "${YELLOW}   Set it with: export NOAA_CDO_TOKEN=your_token_here${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment check passed${NC}"

# Create maintenance cron jobs
echo -e "${BLUE}📅 Setting up maintenance schedule...${NC}"

# Daily maintenance (runs before data collection)
DAILY_MAINTENANCE="0 1 * * * cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type daily >> logs/maintenance.log 2>&1"

# Weekly maintenance (Sundays at 3 AM)
WEEKLY_MAINTENANCE="0 3 * * 0 cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type weekly >> logs/maintenance.log 2>&1"

# Health check every 6 hours
HEALTH_CHECK="0 */6 * * * cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type check >> logs/health.log 2>&1"

# Data collection (runs after daily maintenance)
DATA_COLLECTION="0 2 * * * cd $BACKEND_DIR && python3 $MAIN_SCRIPT >> logs/collection.log 2>&1"

echo -e "${YELLOW}📋 Proposed maintenance schedule:${NC}"
echo -e "${YELLOW}   Daily maintenance: 1:00 AM${NC}"
echo -e "${YELLOW}   Data collection: 2:00 AM${NC}"
echo -e "${YELLOW}   Health checks: Every 6 hours${NC}"
echo -e "${YELLOW}   Weekly maintenance: Sundays 3:00 AM${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to add these maintenance cron jobs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add the cron jobs
    (crontab -l 2>/dev/null; echo "$DAILY_MAINTENANCE") | crontab -
    (crontab -l 2>/dev/null; echo "$DATA_COLLECTION") | crontab -
    (crontab -l 2>/dev/null; echo "$WEEKLY_MAINTENANCE") | crontab -
    (crontab -l 2>/dev/null; echo "$HEALTH_CHECK") | crontab -
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Maintenance cron jobs added successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Current cron jobs:${NC}"
        crontab -l | grep -E "(maintenance|collection|health)" || echo "   (No maintenance-related cron jobs found)"
        echo ""
        echo -e "${YELLOW}💡 To remove maintenance jobs later, run: crontab -e${NC}"
        echo -e "${YELLOW}💡 To view maintenance logs: tail -f logs/maintenance.log${NC}"
        echo -e "${YELLOW}💡 To view health logs: tail -f logs/health.log${NC}"
        echo -e "${YELLOW}💡 To view collection logs: tail -f logs/collection.log${NC}"
    else
        echo -e "${RED}❌ Failed to add maintenance cron jobs${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  Maintenance cron jobs not added. You can add them manually later with:${NC}"
    echo -e "${YELLOW}   crontab -e${NC}"
    echo -e "${YELLOW}   Then add:${NC}"
    echo -e "${YELLOW}   $DAILY_MAINTENANCE${NC}"
    echo -e "${YELLOW}   $DATA_COLLECTION${NC}"
    echo -e "${YELLOW}   $WEEKLY_MAINTENANCE${NC}"
    echo -e "${YELLOW}   $HEALTH_CHECK${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Manual maintenance commands:${NC}"
echo "1. Run daily maintenance:"
echo "   cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type daily"
echo ""
echo "2. Run weekly maintenance:"
echo "   cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type weekly"
echo ""
echo "3. Check system health:"
echo "   cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type check"
echo ""
echo "4. Run emergency maintenance:"
echo "   cd $BACKEND_DIR && python3 $MAINTENANCE_SCRIPT --type emergency"
echo ""
echo "5. Test data collection:"
echo "   cd $BACKEND_DIR && python3 $MAIN_SCRIPT --test"
echo ""
echo -e "${GREEN}🎉 Maintenance scheduler setup complete!${NC}"
