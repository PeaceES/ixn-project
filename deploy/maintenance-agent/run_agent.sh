#!/bin/bash
echo "🔧 Maintenance Agent - Activating Virtual Environment"
echo "===================================================="
source venv/bin/activate
echo "✅ Virtual environment activated"
echo "🚀 Starting maintenance agent test..."
python test_agent.py
