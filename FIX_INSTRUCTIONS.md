# REPLIT PORT CONFIGURATION FIX

## THE PROBLEM
Your .replit file has DUPLICATE port configurations for external port 80:
- Line 33-35: localPort 5000 → externalPort 80 ✓ (CORRECT)
- Line 38-40: localPort 41273 → externalPort 80 ✗ (DUPLICATE - CAUSES ERROR)

## THE FIX

### Step 1: Open .replit file
Click on `.replit` in the file explorer

### Step 2: Find and DELETE these EXACT lines (lines 36-51):

```
DELETE THIS BLOCK:
──────────────────────────────────────
[[ports]]
localPort = 40103
externalPort = 3000

[[ports]]
localPort = 41273
externalPort = 80

[[ports]]
localPort = 43489
externalPort = 3001

[[ports]]
localPort = 44133
externalPort = 3003

[[ports]]
localPort = 46483
externalPort = 3002
──────────────────────────────────────
```

### Step 3: After deletion, lines 30-40 should look like this:

```
CORRECT RESULT:
──────────────────────────────────────
[workflows.workflow.metadata]
outputType = "webview"

[[ports]]
localPort = 5000
externalPort = 80

[userenv]

[userenv.shared]
LLM_MODEL = "gemini-2.5-flash"
──────────────────────────────────────
```

### Step 4: Save (Ctrl+S or Cmd+S)

### Step 5: IMPORTANT - Complete Repl Restart
- Click the 3-dot menu (⋮) at the very top right
- Select "Restart Repl" (NOT just restart workflow)
- Wait for complete restart

## WHY THIS FIXES IT
Replit's proxy sees TWO ports trying to use external port 80 and picks the WRONG one (41273) which isn't running, causing "repl unreachable" error.

## YOUR APP IS WORKING
Your app runs perfectly on port 5000 - this is ONLY a routing configuration issue.
