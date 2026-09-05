# PRD — ORCA: Marine EcOsystem Reasoning with Collaborative Agents
**Problem Statement ID:** 26176 | **Organization:** ISRO | **Theme:** Disaster Management | **Category:** Software
**Scope:** Smart India Hackathon MVP (hackathon build, not production system)

---

## 1. Problem Summary

Fishermen, coastal authorities, and maritime operators need fast, trustworthy answers to questions like "Is it safe to venture into the sea tomorrow?" or "Where is the nearest fishing zone?" — synthesized from scattered satellite, weather, and oceanographic data. ORCA is a conversational, multi-agent AI platform that turns natural-language queries into evidence-based, explainable marine safety and fishing recommendations.

## 2. Goals (MVP)

- Demonstrate genuine **agentic AI behavior**: a visible plan → task decomposition → multi-agent execution → synthesis trace, not a single-prompt chatbot.
- Answer 5 core query types reliably end-to-end using seeded/sample marine + weather + geospatial data.
- Show **explainability**: every recommendation traceable to the agent/data source that produced it.
- Show **multilingual output** (English + 1 Indian regional language, e.g. Hindi).
- Show **design awareness of at-sea connectivity constraints** via a pre-departure cache/briefing feature.

## 3. Non-Goals (explicitly out of scope for MVP)

- Live/real-time API integration with INCOIS, IMD, MOSDAC (use seeded sample datasets instead).
- Full offline app functionality at sea (only pre-departure caching, demoed as a designed feature).
- More than 2 languages.
- Production-grade authentication, multi-user accounts, persistence beyond session/demo.
- Full route optimization with live currents/fuel modeling (simplified cost-grid only, if time allows).
- ML model training / feedback flywheel (mention as future roadmap only).

## 4. Primary Users

1. **Fisherman** — low-to-moderate technical literacy, needs simple, safety-first answers, may prefer regional language, cares about "is it safe" and "where do I go."
2. **Coastal authority / disaster management officer** — needs broader situational view (zones, alerts, trends), may use English UI with more analytical depth.

(MVP can use a single unified UI with a persona toggle if time allows; not required for core demo.)

## 5. Core User Queries the MVP Must Handle

1. "Where is the nearest Potential Fishing Zone (PFZ) today?"
2. "Is it safe to venture into the sea tomorrow morning?"
3. "What are the tide, weather, and sea conditions near my location?"
4. "Are there any lightning or cyclone alerts in my area?"
5. "Which fishing zones should I avoid due to hazardous conditions or geofencing restrictions?"

(Stretch, if time allows: "What is the safest route considering weather and sea state?")

## 6. System Architecture — Agents

| Agent | Responsibility | MVP Priority |
|---|---|---|
| **Orchestrator / Planner** | Parses intent, decomposes query into sub-tasks, routes to specialist agents, merges results | Must-have |
| **Weather/Hazard Agent** | Wind, wave height, lightning, cyclone alerts for a given location/date | Must-have |
| **Marine Data Agent** | SST, chlorophyll concentration, derives PFZ proxy zones | Must-have |
| **Geospatial/Geofencing Agent** | Checks location against IMBL, MPAs, restricted zones | Must-have |
| **Risk Assessment Agent** | Fuses Weather + Marine + Geofencing outputs into a single safety verdict + confidence score | Must-have |
| **Synthesis / Explainability Agent** | Converts fused agent outputs into a natural-language answer with a visible reasoning trace (which agent contributed what) | Must-have |
| **Language Agent** | Translates final English output into selected target language (via Bhashini API, LLM fallback) | Must-have |
| **Visualization Agent** | Emits map layer data / chart specs for the frontend (SST, chlorophyll, wave height, geofence overlays) | Must-have |
| **Route Optimization Agent** | Simplified hazard-aware path between two points | Should-have |
| **Reporting Agent** | Packages a conversation + map snapshot into a shareable advisory summary | Should-have |
| **Sync/Cache Agent** | Generates a pre-departure offline briefing bundle (text + map snapshot) cached client-side | Should-have |

**Pipeline (per query):**
`User query (English input) → Orchestrator plans sub-tasks → Weather/Marine/Geofencing agents execute in parallel → Risk Assessment Agent fuses results → Synthesis Agent generates English answer + reasoning trace → Language Agent translates output if needed → Visualization Agent emits map layers → Response rendered to user`

## 7. Functional Requirements by Agent

### 7.1 Orchestrator/Planner
- Accepts free-text English query.
- Classifies intent into one of the 5 core query types (or a combination).
- Produces a visible task list/plan (this plan itself should be shown in the UI as proof of agentic decomposition).
- Dispatches parallel calls to relevant specialist agents based on the plan.
- Handles basic multi-turn context (e.g., "what about tomorrow evening?" referring to a previously stated location).

### 7.2 Weather/Hazard Agent
- Input: lat/lon (or named location), date/time window.
- Output: wind speed, wave height, lightning risk flag, cyclone alert flag, sourced from seeded IMD-style bulletin data.
- Returns a structured object, not free text, for downstream fusion.

### 7.3 Marine Data Agent
- Input: lat/lon or region, date.
- Output: SST value, chlorophyll concentration, derived PFZ likelihood (based on seeded MOSDAC/INCOIS-style sample data).
- Returns nearest/best-matching PFZ coordinates for "nearest PFZ" queries.

### 7.4 Geospatial/Geofencing Agent
- Input: lat/lon or route.
- Output: flags if location/route intersects IMBL, MPA, or other restricted zone (using WDPA shapefile data).
- Returns distance-to-boundary if near but not inside a restricted zone.

### 7.5 Risk Assessment Agent
- Input: outputs from Weather, Marine, Geofencing agents.
- Output: single safety verdict (Safe / Caution / Unsafe), confidence score, list of contributing factors with weights.
- Must expose **why** — e.g. "Unsafe: high wave (2.8m) + inside MPA buffer zone."

### 7.6 Synthesis / Explainability Agent
- Converts structured agent outputs into a natural-language English answer.
- Generates a parallel "reasoning trace" object: ordered list of {agent name, finding, contribution to final answer}.
- Trace must be renderable in UI as a distinct panel, not buried in the chat text.

### 7.7 Language Agent
- Input: English text (final answer only — not the user's query).
- User selects target language at session start (dropdown/toggle) — no automatic input-language detection in MVP.
- Calls Bhashini NMT API for translation; falls back to a general LLM translation call if Bhashini is unavailable/slow.
- Returns translated text for display (and optionally passes to TTS if voice-out is attempted as stretch).

### 7.8 Visualization Agent
- Emits GeoJSON/layer specs for: SST heatmap, chlorophyll heatmap, wave height overlay, geofence boundaries, PFZ markers.
- Frontend map (e.g., Leaflet/Mapbox) renders togglable layers from this output.

### 7.9 Route Optimization Agent (should-have)
- Input: start point, end point.
- Output: simplified path avoiding cells flagged unsafe by Risk Assessment Agent (wave height + geofence only, no currents/fuel modeling for MVP).

### 7.10 Reporting Agent (should-have)
- Packages latest conversation turn + map snapshot into a single formatted summary card (exportable as text/image, PDF not required for MVP).

### 7.11 Sync/Cache Agent (should-have)
- On explicit user action ("prepare for departure"), bundles current advisory (safety verdict, hazard alerts, geofence zones, forecast window) into a compact cached object viewable without a live connection.
- This is a **designed and demoed feature**, not a claim of full offline app functionality — see Section 9.

## 8. Data Sources (seeded/sample for MVP)

| Data | Source | Integration approach |
|---|---|---|
| PFZ advisories | INCOIS PFZ bulletins | Digitize a sample set into structured JSON |
| SST, chlorophyll | MOSDAC (ISRO) | Sample extracts as CSV/JSON, feed-agnostic interface for future live swap |
| Wave/wind/tide | INCOIS Ocean State Forecast | Sample bulletin data |
| Cyclone/lightning | IMD | Sample bulletin data |
| IMBL/MPA/restricted zones | WDPA (protectedplanet.net), Survey of India | Downloadable shapefiles, direct integration |
| Coastline/bathymetry base layers | GEBCO, Natural Earth | Direct integration for map base |
| Fallback SST/chlorophyll (if MOSDAC extraction is slow) | NASA Ocean Color, Copernicus Marine Service | Same schema as MOSDAC agent expects |

**Design rule:** every data agent must be built behind a clean interface (fixed input/output schema) so a live feed can be substituted later without touching the Orchestrator or other agents.

## 9. Language Requirements

- Input: English only in MVP (no auto-detection).
- Output: user-selected language (English or Hindi for MVP demo).
- Translation backend: Bhashini API (primary), generic LLM API (fallback if Bhashini unavailable).
- Rationale to state in demo: mirrors real deployment pattern (user selects language once, like UMANG/DigiLocker), avoids input-mistranslation risk to intent parsing.

## 10. Connectivity / Offline Positioning

- MVP does **not** claim full offline functionality.
- MVP **does** demonstrate: pre-departure briefing caching (Sync/Cache Agent) as a designed answer to "fishermen are at sea with no signal."
- Critical alerts (cyclone/lightning/geofence breach) are positioned as intended to integrate with existing SMS/radio channels already used by INCOIS/IMD — described in pitch, not built in MVP.

## 11. UI Requirements

- Conversational chat interface (text input, language toggle).
- Interactive map with togglable layers (SST, chlorophyll, wave height, PFZ markers, geofence boundaries).
- Alerts panel (lightning/cyclone/geofence breach, if simulated proactive loop is built).
- **Reasoning trace panel** — distinct visual area showing agent-by-agent contribution to the current answer. This is the single most important UI element for grading; do not treat as optional polish.
- Plan panel (optional but strong) — shows Orchestrator's task decomposition before/while agents execute.

## 12. Success Criteria for Demo

- All 5 core queries return correct, sourced answers live, in both languages.
- Reasoning trace panel visibly updates per query showing distinct agent contributions.
- At least one hazardous-condition query correctly returns "Unsafe" with a clear contributing-factor explanation.
- At least one geofence-boundary query correctly flags proximity/intersection.
- Map layers render and toggle correctly for at least 3 layers.
- Sync/Cache "prepare for departure" flow works as a live demo moment.
- No agent's output is faked/hardcoded per-query — must run through the actual pipeline for every demoed query.

## 13. Build Priority Order (suggested)

1. Seed datasets (structured JSON/CSV for weather, marine, geofence) — foundation for everything else.
2. Weather Agent, Marine Agent, Geofencing Agent (can be built in parallel, independent).
3. Risk Assessment Agent (depends on the three above).
4. Orchestrator/Planner (depends on specialist agents having working interfaces).
5. Synthesis/Explainability Agent + reasoning trace UI.
6. Visualization Agent + map UI.
7. Language Agent (Bhashini integration + fallback).
8. Should-have agents (Route Optimization, Reporting, Sync/Cache) if time remains.

## 14. Open Risks

- Bhashini API uptime/latency during live demo — mitigate with LLM fallback, same interface.
- MOSDAC/INCOIS data may require manual digitization from PDF bulletins — budget time for this early, not last-minute.
- Reasoning trace UI is easy to under-build and hard to retrofit — treat as core feature, not final polish.
- Judges may ask about live-feed autonomy and offline claims — team should rehearse the honest framing in Sections 8 and 9 before demo day.