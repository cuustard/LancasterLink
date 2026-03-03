# LancasterLink – Software Requirements

## 2.1 Functional Requirements

| ID | Requirement | Priority | Category |
|----|-------------|----------|----------|
| FR-JP-01 | **Multi-Modal Routing:** Calculate routes involving Bus, Rail, and Tram between any two points in the target region (Lancaster, Preston, Blackpool, Fylde, Wyre) | MUST | Journey Planner |
| FR-JP-02 | **Fallback Routing:** System must default to scheduled timetable data if live data streams are unavailable | MUST | Journey Planner |
| FR-JP-03 | **Disruption Awareness:** Route calculations must penalise or avoid services flagged as "Cancelled" or "Significantly Delayed" in live feeds | MUST | Journey Planner |
| FR-JP-04 | **Future Planning:** Allow users to plan journeys up to 3 months in advance using static timetables | SHOULD | Journey Planner |
| FR-JP-05 | **Interchange Buffering:** Prioritise routes with "well-served transport hubs" and avoid fragile connections (e.g., <5 min transfer at a small stop) | SHOULD | Journey Planner |
| FR-JP-06 | **Recent Journeys:** Persist recent origins/destinations locally (e.g., via Local Storage/Cookies) for quick selection | SHOULD | Journey Planner |
| FR-JP-06 | **Multi-Platform Recent Journeys:** Persist recent origins/destinations for a user over multiple platforms by introducing user accounts | COULD | Journey Planner |
| FR-LM-01 | **Network Visualisation:** Display static routes for Bus, Rail, and Tram overlaid on a geographical map | MUST | Live Map |
| FR-LM-02 | **Live Vehicle Tracking:** Render current vehicle positions (interpolated or GPS) for supported operators (Stagecoach, Northern, etc.) | MUST | Live Map |
| FR-LM-03 | **Stop Inspection:** Clicking a stop/station must display upcoming departures (scheduled vs. expected) | MUST | Live Map |
| FR-LM-04 | **Filtering:** Allow users to toggle visibility of specific transport modes (e.g., hide buses, show only trains) | SHOULD | Live Map |

---

## 2.2 Non-Functional Requirements

| ID | Requirement | Priority | Category |
|----|-------------|----------|----------|
| NFR-PL-01 | **Response Time:** Route calculation for a typical journey (e.g., Lancaster → Blackpool) should complete within < 5 seconds | MUST | Performance and Latency |
| NFR-PL-02 | **Map Refresh Rate:** Live vehicle positions on the map must update at least every 30 seconds (subject to data availability) | SHOULD | Performance and Latency |
| NFR-PL-03 | **Load Handling:** The system must support concurrent use by the evaluation team (approx. 5–10 users) without degradation | MUST | Performance and Latency |
| NFR-RA-01 | **Graceful API Failure:** If the live data feed API fails, the system MUST automatically revert to displaying scheduled timetable data without crashing | MUST | Reliability and Availability |
| NFR-RA-02 | **Stale Data Handling:** Vehicle data older than 5 minutes must be discarded or visually flagged as "stale" to prevent misleading users | MUST | Reliability and Availability |
| NFR-SDP-01 | **No PII Storage:** The application MUST NOT store any Personally Identifiable Information (names, emails) or track user movements | MUST | Security and Data Privacy |
| NFR-SDP-02 | **No Payment Processing:** The application MUST NOT process or store any financial data | MUST | Security and Data Privacy |
| NFR-SDP-03 | **Input Sanitisation:** All user inputs (origin/destination text) must be sanitised to prevent injection attacks | MUST | Security and Data Privacy |
| NFR-SDP-04 | **Dependency Safety:** All third-party libraries must be audited for known vulnerabilities | MUST | Security and Data Privacy |
| NFR-UA-01 | **Mobile Compatibility:** The web interface must be responsive and functional on mobile viewports (min-width 320px) | MUST | Usability and Accessibility |
| NFR-UA-02 | **Interface Simplicity:** The UI must be "simple" and "consistent," minimising the number of clicks required to plan a route | MUST | Usability and Accessibility |
| NFR-UA-03 | **Visual Accessibility:** The application should use high-contrast colours (WCAG AA standard) to distinguish routes | SHOULD | Usability and Accessibility |
| NFR-UA-04 | **Error Feedback:** The system must provide human-readable error messages (e.g., "No route found" vs "Error 500") | SHOULD | Usability and Accessibility |

---

## 2.3 Data Ingestion & Integration Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| DR-01 | **Data Linking:** Programmatically link NaPTAN stop points with NPTG localities to group stops into logical "towns" (e.g., grouping "Lancaster Rail Station" into "Lancaster") | MUST |
| DR-02 | **Feed Normalisation:** Normalise diverse operator data (e.g., Northern vs. Stagecoach) into a single standard format | MUST |
| DR-03 | **Polling Frequency:** Poll live API endpoints at a rate sufficient for accuracy but within server rate limits | MUST |

---

## 2.4 Routing Logic & Reliability Heuristics

| ID | Requirement | Priority |
|----|-------------|----------|
| RL-01 | **Fragile Connection Avoidance:** Do not provide routes with connection times less than a specific amount (e.g. <5 mins) | SHOULD |
| RL-02 | **Hub Prioritisation:** Weight "well-served transport hubs" higher than remote stops | SHOULD |
| RL-03 | **Disruption Rerouting:** Automatically recalculate active journeys when a "Cancelled" or "Delayed" message is received | MUST |
| RL-04 | **Multi-Modal Stitching:** Connect bus legs to rail legs, accounting for walking time between stops and platforms | MUST |

---

## 2.5 Operational & Deployment Constraints

| ID | Requirement | Priority |
|----|-------------|----------|
| OD-01 | **Containerisation:** All backend services must be deployable as Docker/Podman containers | MUST |
| OD-02 | **CI/CD Pipeline:** The repository must include a CI/CD pipeline for automated testing and building | MUST |
| OD-03 | **Resource Efficiency:** The system must run effectively within the resource limits of the provided lab VMs/Scafell server | MUST |

---

## 2.6 Accessibility & Interface Compliance

| ID | Requirement | Priority |
|----|-------------|----------|
| AIC-01 | **Visual Clarity:** Use distinct visual styles (e.g., colour/dash) to differentiate "Live Data" from "Timetable Only" data | MUST |
| AIC-02 | **Contextual Geography:** Display key landmarks and town names on the map | SHOULD |
| AIC-03 | **Device Responsiveness:** The UI must be usable on mobile viewports | SHOULD |
| AIC-04 | **WCAG Compliance:** Follow basic accessibility guidelines (contrast, sizing) | SHOULD |
