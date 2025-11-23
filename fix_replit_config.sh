#!/bin/bash

echo "========================================="
echo "  REPLIT PORT CONFIGURATION FIX SCRIPT  "
echo "========================================="
echo ""

# Backup the original .replit file
if [ ! -f .replit.backup ]; then
    echo "Creating backup: .replit.backup"
    cp .replit .replit.backup
    echo "✓ Backup created"
else
    echo "⚠ Backup already exists at .replit.backup"
fi

echo ""
echo "Current port configuration issues:"
echo "-----------------------------------"
grep -A 2 "externalPort = 80" .replit

echo ""
echo "This will remove duplicate port configurations."
echo "Only port 5000 -> external port 80 will remain."
echo ""

# Create a temporary file with the fix
cat > .replit.tmp << 'EOF'
modules = ["python-3.11", "nodejs-20"]
[agent]
expertMode = true
integrations = ["python_openai:1.0.0"]

[nix]
channel = "stable-25_05"
packages = ["libxcrypt"]

[workflows]
runButton = "Project"

[[workflows.workflow]]
name = "Project"
mode = "parallel"
author = "agent"

[[workflows.workflow.tasks]]
task = "workflow.run"
args = "Start App"

[[workflows.workflow]]
name = "Start App"
author = "agent"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "bash start.sh"
waitForPort = 5000

[workflows.workflow.metadata]
outputType = "webview"

[[ports]]
localPort = 5000
externalPort = 80

[userenv]

[userenv.shared]
LLM_MODEL = "gemini-2.5-flash"
LLM_PROVIDER = "google"

[deployment]
deploymentTarget = "autoscale"
run = ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
build = ["npm", "run", "build", "--prefix", "frontend"]
EOF

# Show the diff
echo "Changes that will be made:"
echo "-----------------------------------"
diff .replit .replit.tmp | grep -E "^[<>].*port" || echo "Ready to apply fix"

echo ""
echo "To apply this fix:"
echo "1. Run: mv .replit.tmp .replit"
echo "2. Restart your Repl (click 3-dot menu → Restart Repl)"
echo ""
echo "Or simply run: bash fix_replit_config.sh && mv .replit.tmp .replit"
echo ""
echo "To restore backup: mv .replit.backup .replit"
echo "========================================="
