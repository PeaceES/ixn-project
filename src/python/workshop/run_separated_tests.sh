#!/bin/bash

# Separated Test Runner for Unit vs Integration Testing Analysis
# Perfect for thesis work comparing testing methodologies

echo "🧪 Running Separated Test Suite for Thesis Analysis"
echo "=================================================="

# Create reports directories if they don't exist
mkdir -p reports/junit reports/coverage_html

echo ""
echo "📊 Step 1: Running Unit Tests (Fast, Isolated)"
echo "----------------------------------------------"
pytest -m unit \
    --html=reports/unit_tests.html \
    --self-contained-html \
    --junitxml=reports/junit/unit_tests.xml \
    --cov=services --cov=agent --cov=web_server \
    --cov-report=html:reports/coverage_html/unit_coverage \
    --cov-report=xml:reports/coverage_unit.xml \
    -v

echo ""
echo "🔗 Step 2: Running Integration Tests (Component Interactions)"
echo "------------------------------------------------------------"
pytest -m integration \
    --html=reports/integration_tests.html \
    --self-contained-html \
    --junitxml=reports/junit/integration_tests.xml \
    --cov=services --cov=agent --cov=web_server \
    --cov-report=html:reports/coverage_html/integration_coverage \
    --cov-report=xml:reports/coverage_integration.xml \
    -v

echo ""
echo "🎯 Step 3: Running All Tests Together (Complete Coverage)"
echo "---------------------------------------------------------"
pytest \
    --html=reports/all_tests.html \
    --self-contained-html \
    --junitxml=reports/junit/all_tests.xml \
    --cov=services --cov=agent --cov=web_server \
    --cov-report=html:reports/coverage_html/complete_coverage \
    --cov-report=xml:reports/coverage_complete.xml \
    -v

echo ""
echo "✅ Test Analysis Complete!"
echo "========================="
echo ""
echo "📈 Reports Generated:"
echo "  • Unit Tests:        reports/unit_tests.html"
echo "  • Integration Tests: reports/integration_tests.html"  
echo "  • All Tests:         reports/all_tests.html"
echo ""
echo "📊 Coverage Reports:"
echo "  • Unit Coverage:        reports/coverage_html/unit_coverage/index.html"
echo "  • Integration Coverage: reports/coverage_html/integration_coverage/index.html"
echo "  • Complete Coverage:    reports/coverage_html/complete_coverage/index.html"
echo ""
echo "📋 JUnit XML (for CI/thesis data):"
echo "  • reports/junit/unit_tests.xml"
echo "  • reports/junit/integration_tests.xml" 
echo "  • reports/junit/all_tests.xml"
echo ""
echo "🎓 Perfect for thesis analysis comparing:"
echo "  • Unit vs Integration test effectiveness"
echo "  • Coverage differences between test types"
echo "  • Test execution speed comparison"
echo "  • Bug detection capabilities"
echo ""
