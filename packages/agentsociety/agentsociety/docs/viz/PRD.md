## 1. Observability Framework Objectives
This framework is designed specifically for computational social scientists and urban planners. Its primary goal is to provide deep, multi-dimensional semantic and spatial debugging to validate whether LLM-based generative agents naturally replicate the statistical "physics" of empirical human mobility.

## 2. Core Features & Requirements

### 2.1 Causal Tracer: Mobility Trigger Distribution
* **Description:** A visualization tool to separate spatial movements based on their underlying cognitive trigger.
* **Requirements:**
    * Implement a bar plot at the individual agent level detailing the distribution of mobility triggers.
    * Explicitly categorize moves initiated by the `PlanBlock` (e.g., habitual commutes like Home-to-Work) versus moves initiated dynamically by the `NeedsBlock` (e.g., transitioning to a restaurant due to decaying hunger levels).

### 2.2 Reality Check Overlays (Mobility Laws)
* **Description:** Passive visual guides that plot empirical mobility laws against simulated agent behavior to highlight deviations from physical reality.
* **Requirements:**
    * [cite_start]Integrate baseline distributions from literature, starting with the travel distance distribution (truncated power law) defined by Gonzales et al[cite: 315].
    * Provide overlay graphs on the dashboard comparing the simulated population's current metrics against these empirical baselines.

### 2.3 Plan vs. Execution Timeline

* [cite_start]**Description:** A temporal visualization that contrasts the agent's intended 6-step granular daily schedule generated at midnight [cite: 112, 118] with their actual executed spatial actions.
* **Requirements:**
    * Create a Y-axis timeline component where the original midnight plan is displayed (e.g., using a base color or specific opacity).
    * Overlay the actual executed routine on this timeline.
    * Whenever the executed routine deviates from the original plan, color-code that specific time block according to the exact `need` (Hunger, Energy, Safety, Social) that forced the change.

### 2.4 Multi-Scale Demographicus & Needs Tracking

* **Description:** Hierarchical visualizations spanning from individual agent micro-views to population-level macro-views, tracking both demographics and internal state vectors.
* **Requirements:**
    * [cite_start]**Needs Tracking (Micro-View):** Display a graph tracking the individual agent's state vector across simulation steps for all four needs: hunger, energy, safety, and social connection[cite: 108]. 
    * [cite_start]**Critical Threshold Indicator:** Because need satisfaction decays over time and follows a strict hierarchy (Hunger > Safety > Energy > Social)[cite: 110], the graph must include a clear, visual horizontal line indicating the "threshold." [cite_start]It must be immediately obvious when a need falls below this line and becomes the dominant driver that alters the agent's plan[cite: 111].
    * [cite_start]**Demographicus (Macro-View):** A global dashboard displaying the distribution of initialized behavioral profiles (Scouters, Regulars, Routiners)[cite: 349, 350].
    * [cite_start]**Empirical Baselines:** Use empirical distribution baselines (e.g., specific regional percentages like Shanghai's 56% Regulars [cite: 552]) as static visual guides in the macro-view to ensure population accuracy.

### 2.5 Social Network Dynamics (Future Scope)
* [cite_start]**Description:** While agents are currently initialized with empty social networks[cite: 303], a foundational placeholder tab will be established for future integration of social edges.
* **Requirements:**
    * Deprioritized for the current iteration to focus on spatial/temporal accuracy and individual needs tracking. 
    * [cite_start]Future iterations will require visualizations of the weighted social network and relationship strengths[cite: 300].