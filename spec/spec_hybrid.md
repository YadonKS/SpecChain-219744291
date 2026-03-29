# Requirement ID: FR_hybrid_01
- Description: [The system shall provide a Sleep Quick Start action that starts a sleep session in one tap from the main sleep entry point.]
- Source Persona: [P1 - Sleep-Focused Evening User]
- Traceability: [Derived from hybrid review group G1]
- Acceptance Criteria: [Given the user is on the sleep entry screen, When the user taps Sleep Quick Start, Then audio playback shall begin within 3 seconds and no additional setup screen shall be required.]


# Requirement ID: FR_hybrid_02
- Description: [The system shall let users filter sleep content by narrator, duration range, and content type.]
- Source Persona: [P1 - Sleep-Focused Evening User]
- Traceability: [Derived from hybrid review group G1]
- Acceptance Criteria: [Given at least one filter is selected, When results are shown, Then every returned item shall match all selected filters, and clearing filters shall restore the unfiltered list.]


# Requirement ID: FR_hybrid_03
- Description: [The system shall provide a Short Sleep collection for users who need brief bedtime sessions.]
- Source Persona: [P1 - Sleep-Focused Evening User]
- Traceability: [Derived from hybrid review group G1]
- Acceptance Criteria: [Given the user opens Short Sleep, When sessions are listed, Then each listed session shall have a duration of 10 minutes or less.]


# Requirement ID: FR_hybrid_04
- Description: [The system shall recommend guided meditation sessions using user-selected mood and available time.]
- Source Persona: [P2 - Stress-Management Meditation User]
- Traceability: [Derived from hybrid review group G2]
- Acceptance Criteria: [Given the user selects one mood and one time range, When recommendations are generated, Then at least 5 sessions shall be shown and each session duration shall fall within the selected time range.]


# Requirement ID: FR_hybrid_05
- Description: [The system shall let users save guided sessions to Favorites and replay them directly from Favorites.]
- Source Persona: [P2 - Stress-Management Meditation User]
- Traceability: [Derived from hybrid review group G2]
- Acceptance Criteria: [Given a session is marked as Favorite, When the user opens Favorites, Then that session shall appear in the list and start playback in one tap.]


# Requirement ID: FR_hybrid_06
- Description: [The system shall show price, trial terms, and renewal date before the user confirms a subscription.]
- Source Persona: [P3 - Billing-Conscious Subscriber]
- Traceability: [Derived from hybrid review group G3]
- Acceptance Criteria: [Given the user is on the final subscription confirmation screen, When billing details are displayed, Then price, trial length, renewal date, and renewal amount shall all be visible on that same screen before confirmation.]


# Requirement ID: FR_hybrid_07
- Description: [The system shall provide an in-app cancellation flow that ends with explicit cancellation confirmation.]
- Source Persona: [P3 - Billing-Conscious Subscriber]
- Traceability: [Derived from hybrid review group G3]
- Acceptance Criteria: [Given the user completes cancellation, When the flow finishes, Then the system shall show a confirmation message with effective date and the subscription status shall update to canceled.]


# Requirement ID: FR_hybrid_08
- Description: [The system shall provide billing history entries with date, amount, plan type, and charge source.]
- Source Persona: [P3 - Billing-Conscious Subscriber]
- Traceability: [Derived from hybrid review group G3]
- Acceptance Criteria: [Given the user opens billing history, When entries are listed, Then every entry shall include charge date, amount, plan/term, and transaction source or reference.]


# Requirement ID: FR_hybrid_09
- Description: [The system shall provide playback controls for voice volume and background volume during guided content.]
- Source Persona: [P4 - Audio-Quality and Content-Curation User]
- Traceability: [Derived from hybrid review group G4]
- Acceptance Criteria: [Given guided audio is playing, When the user changes either volume control, Then the audible output shall reflect the new setting within 1 second and persist for the current session.]


# Requirement ID: FR_hybrid_10
- Description: [The system shall support narrator-based search and provide a narrator page listing related sessions.]
- Source Persona: [P4 - Audio-Quality and Content-Curation User]
- Traceability: [Derived from hybrid review group G4]
- Acceptance Criteria: [Given the user searches by a narrator name, When results are shown, Then the user shall be able to open that narrator page and view a list of sessions attributed to that narrator.]


# Requirement ID: FR_hybrid_11
- Description: [The system shall preserve startup, login, search, and playback reliability after app updates.]
- Source Persona: [P5 - Reliability-First Daily User]
- Traceability: [Derived from hybrid review group G5]
- Acceptance Criteria: [Given the app is updated to a new version, When a user performs startup, login, search, and playback flows, Then each flow shall complete without crash, freeze, or blocking error.]


# Requirement ID: FR_hybrid_12
- Description: [The system shall return categorized search results and support filter refinement.]
- Source Persona: [P5 - Reliability-First Daily User]
- Traceability: [Derived from hybrid review group G5]
- Acceptance Criteria: [Given the user enters a keyword query, When results load, Then each result shall show a category label and applying a filter shall update the results list to only matching items.]
