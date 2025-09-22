#!/bin/bash

echo "🔧 Maintenance Agent Launcher"
echo "=============================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Make sure we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Run the test script
echo "🚀 Starting agent test..."
python3 test_agent.py

echo ""
echo "📝 To run the agent directly without tests:"
echo "   python3 main.py"
echo ""
echo "📁 Project structure:"
echo "   main.py              - Main agent logic"
echo "   test_agent.py        - Test and launch script"
echo "   data/rooms.json      - Room monitoring data"
echo "   data/maintenance_schedule.json - Maintenance tracking"
echo "   shared/instructions.txt - Agent instructions"
echo "   .env                 - Configuration (keep private!)"
