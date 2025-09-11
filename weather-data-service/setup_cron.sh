#!/bin/bash
# setup_cron.sh - Setup daily cron job for weather data collection

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌤️  Weather Data Collection - Cron Job Setup${NC}"
echo "=================================================="

# Get the absolute path to the backend directory
BACKEND_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MAIN_SCRIPT="$BACKEND_DIR/main.py"
LOG_DIR="$BACKEND_DIR/logs"

echo -e "${YELLOW}📁 Backend directory: $BACKEND_DIR${NC}"
echo -e "${YELLOW}🐍 Main script: $MAIN_SCRIPT${NC}"
echo -e "${YELLOW}📝 Log directory: $LOG_DIR${NC}"

# Check if main.py exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}❌ Error: main.py not found at $MAIN_SCRIPT${NC}"
    exit 1
fi

# Check if logs directory exists, create if not
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}📁 Creating logs directory...${NC}"
    mkdir -p "$LOG_DIR"
fi

# Check for required environment variables
if [ -z "$NOAA_CDO_TOKEN" ]; then
    echo -e "${RED}❌ Error: NOAA_CDO_TOKEN environment variable is not set${NC}"
    echo -e "${YELLOW}   Set it with: export NOAA_CDO_TOKEN=your_token_here${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment check passed${NC}"

# Create the cron job entry
CRON_ENTRY="0 2 * * * cd $BACKEND_DIR && python3 $MAIN_SCRIPT >> $LOG_DIR/cron.log 2>&1"

echo -e "${BLUE}📅 Proposed cron job:${NC}"
echo -e "${YELLOW}   $CRON_ENTRY${NC}"
echo ""
echo -e "${BLUE}📋 This will run daily at 2:00 AM and log to: $LOG_DIR/cron.log${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to add this cron job? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Cron job added successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Current cron jobs:${NC}"
        crontab -l | grep -E "(main\.py|weather|collection)" || echo "   (No weather-related cron jobs found)"
        echo ""
        echo -e "${YELLOW}💡 To remove the cron job later, run: crontab -e${NC}"
        echo -e "${YELLOW}💡 To view logs: tail -f $LOG_DIR/cron.log${NC}"
    else
        echo -e "${RED}❌ Failed to add cron job${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  Cron job not added. You can add it manually later with:${NC}"
    echo -e "${YELLOW}   crontab -e${NC}"
    echo -e "${YELLOW}   Then add: $CRON_ENTRY${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Manual setup instructions:${NC}"
echo "1. Set environment variables:"
echo "   export NOAA_CDO_TOKEN=your_token_here"
echo "   export DATABASE_PATH=$BACKEND_DIR/data/weather_pool.db"
echo ""
echo "2. Test the collection:"
echo "   cd $BACKEND_DIR"
echo "   python3 main.py --test"
echo ""
echo "3. Run full collection:"
echo "   python3 main.py"
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
