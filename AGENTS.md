# AGENTS.md — Project Instructions for Autonomous Agents

## Project Overview
- **Project**: WeAreDevelopers x BAND: Dark Factory AI Hackathon
- **Platform**: lablab.ai
- **Objective**: Build an autonomous Software Dark Factory inside BAND Desktop: a band of coding agents that plans work, implements it, hands off evidence, and independently checks its own results to ship a clean-room clone of a product everyone knows (`pocketful` or `tablekeeper`).
- **Core Knowledge Base**: See [hackathon_docs/band_dark_factory/README.md](file:///c:/Users/HP/dev/WeAreDevelopers%20x%20BAND/hackathon_docs/band_dark_factory/README.md).

## Critical Non-Negotiables & Rules
1. **Mandates Must Be 100% Generic**:
   - Mandate files (`mandates/*.md`) must NEVER contain domain-specific or track-specific details (no endpoint names, field names, or business error codes). Track details belong solely in the task dispatched to the room. Violating this is an automatic disqualifier.
2. **Video Must Include BAND Desktop Room Recording**:
   - The submission video must include screen recording of the BAND Desktop room actively generating the solution.
3. **Clean Container with Zero Outbound Network**:
   - The service for each stage must build and start inside an isolated container with zero network access (`docker run --network none`). Services that fail to boot receive a zero score.
4. **Autonomous Execution & Agent Teamwork**:
   - Human interaction is strictly limited to dispatching the stage task prompt. No manual code editing or micro-steering during the run.

## Repository Structure Standards
- `mandates/`: 3+ generic agent mandates (`architect.md`, `developer.md`, `auditor.md`).
- `FACTORY.md`: Comprehensive engineering report detailing seat setup, design rationale, cost metrics, and self-healing recovery.
- `room-export.json`: Exported room log via `harness export-room`.
- `stage-1/` through `stage-4/`: Buildable stage services.
- `hackathon_docs/`: Internal reference files (ignored by Git).
