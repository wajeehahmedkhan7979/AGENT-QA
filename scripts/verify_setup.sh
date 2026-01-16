#!/bin/bash
# Quick verification script for the demo setup

set -e

echo "🔍 Verifying Autonomous QA Automation WebApp Demo Setup..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
echo "✅ Docker found"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✅ Docker Compose found"

# Check if services are running
echo ""
echo "📦 Checking running services..."
if docker ps | grep -q qa-backend; then
    echo "✅ Backend container running"
else
    echo "⚠️  Backend container not running. Start with: cd infra && docker-compose up -d"
fi

if docker ps | grep -q qa-sample-app; then
    echo "✅ Sample app container running"
else
    echo "⚠️  Sample app container not running"
fi

# Check health endpoint
echo ""
echo "🏥 Checking backend health..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ Backend health check passed"
else
    echo "⚠️  Backend health check failed. Is the backend running?"
fi

# Check sample app
echo ""
echo "🌐 Checking sample app..."
if curl -s http://localhost:3000/sample-app | grep -q "Sample App"; then
    echo "✅ Sample app accessible"
else
    echo "⚠️  Sample app not accessible. Is it running?"
fi

# Check web UI
echo ""
echo "🖥️  Checking web UI..."
if curl -s http://localhost:3100 | grep -q "html"; then
    echo "✅ Web UI accessible"
else
    echo "⚠️  Web UI not accessible. Is it running?"
fi

echo ""
echo "✨ Verification complete!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3100 in your browser"
echo "2. Submit a job for http://sample-app:3000/sample-app/login"
echo "3. Follow the flow: Extract → Generate → Run → View Report"
echo ""
echo "For detailed testing instructions, see docs/TESTING.md"
