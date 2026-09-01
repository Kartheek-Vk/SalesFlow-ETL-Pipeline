---
name: Streamlit headless runtime
description: Non-interactive Streamlit startup behavior in this workspace
---

The first Streamlit launch can pause for an email/usage prompt when started from a shell. For non-interactive verification or a managed service, start it with headless mode and disable usage-stat collection.

**Why:** A normal background launch exited at the onboarding prompt even though the dashboard itself was valid.

**How to apply:** Use the documented plain command for local interactive use; use `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` plus `--server.headless true` for automated or preview startup.