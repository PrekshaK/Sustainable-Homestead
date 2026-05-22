# Homestead Simulator — Project Context

## What this project is

A self-sufficient homestead simulator that models energy flows, food production, waste cycles,
and land use for a net-zero single-family home. The sim covers solar energy, biogas production,
crop farming, cattle, water cycles, and overall energy balance.

This is also the primary vehicle for learning ML engineering by doing — the simulator generates
real structured data that feeds progressively harder ML problems across four phases.

## Background

Owner has completed CS 224N (NLP) and CS 124 from Stanford, so foundational ML theory is solid.
The goal is applied, project-driven ML practice — not more theory. Build real things, use real data.

---

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React + D3.js (live dashboard), Tailwind CSS |
| Sim engine | Python + FastAPI |
| Data | SQLite (dev) → Postgres (prod), time-series tables per variable |
| ML (Phase 2) | Scikit-learn → PyTorch |
| ML (Phase 3) | PyTorch + Gymnasium + Stable-Baselines3 |
| LLM (Phase 4) | Claude API (RAG-based advisor) |

---

## Project structure (target)

```
homestead-sim/
├── CLAUDE.md                  # this file
├── sim/                       # Python sim engine
│   ├── main.py                # FastAPI app
│   ├── models/
│   │   ├── solar.py           # solar irradiance → kWh
│   │   ├── biogas.py          # waste input → biogas yield
│   │   ├── crops.py           # soil/rain/temp → caloric yield
│   │   ├── cattle.py          # herd size → meat/dairy/waste output
│   │   ├── water.py           # rainfall/usage water cycle
│   │   └── energy_balance.py  # aggregate produced vs consumed
│   ├── data/
│   │   ├── weather.py         # NOAA API integration
│   │   └── synthetic.py       # generate N days of sim data
│   └── db.py                  # SQLite/Postgres connection
├── ml/
│   ├── phase2_forecasting/
│   │   ├── energy_demand.py   # regression: weather+season → kWh demand
│   │   ├── crop_yield.py      # regression: soil+rain+temp → yield
│   │   └── biogas_lstm.py     # LSTM on biogas time-series
│   └── phase3_rl/
│       ├── env.py             # Gymnasium env wrapping the sim
│       ├── reward.py          # reward: energy surplus + food security
│       └── train.py           # PPO/DQN training loop
├── frontend/
│   ├── src/
│   │   ├── Dashboard.jsx      # live energy/food/water dials
│   │   ├── Scenario.jsx       # what-if sliders
│   │   └── charts/            # D3 chart components
│   └── package.json
└── notebooks/                 # EDA, experiments, scratch work
```

---

## Build phases

### Phase 1 — Simulation core (start here, 8–12 weeks, no ML)

Build the physics/math models for one simulated day. Each model takes inputs
(weather, land size, herd count, etc.) and returns outputs (kWh, kg food, liters water).

**First thing to build:** `sim/models/energy_balance.py`
- Inputs: solar irradiance (W/m²), panel area (m²), house size (sqft), outdoor temp
- Output: kWh produced, kWh consumed, net balance
- Wire up to FastAPI endpoint, build React slider UI on top
- This becomes the MVP and the first data source for Phase 2

Key models to implement:
- Solar: standard PV formula, efficiency curve, temperature derating
- Biogas: first-order anaerobic digestion approximation
- Crops: simplified FAO crop water model
- Cattle: feed-in/output mass balance

Data sources to use:
- NOAA Climate Data Online API for real weather
- USDA crop yield tables for ground truth calibration
- Run sim for 10,000+ synthetic days to build training sets

### Phase 2 — Forecasting / supervised ML (4–6 weeks)

The sim now generates labeled data. Build three models:
1. **Energy demand regression** — features: weather, season, occupancy → label: kWh/day
   - Start: linear regression → gradient boosting (XGBoost) → LSTM
   - Key lesson: why each step helps, how seasonality/nonlinearity shows up
2. **Crop yield regression** — features: soil moisture, rainfall, temp, crop type → yield
3. **Biogas time-series** — LSTM on rolling window of temperature + feedstock input

Concepts to internalize: feature engineering, train/val/test splits, overfitting,
MAE/RMSE, cross-validation, learning curves.

### Phase 3 — Optimization / RL (6–8 weeks)

The homestead is a Gymnasium environment. The agent allocates resources.

- **State space:** current energy storage, food stores, water level, season, weather forecast
- **Action space:** how much land to allocate to each crop, cattle count, solar panel investment
- **Reward:** weighted combination of net energy surplus + food security score + land efficiency
- **Budget mode:** given $X and N acres, find the optimal system mix

Start with PPO (Stable-Baselines3). Visualize the agent "playing" the sim in real-time on the dashboard.

Concepts: MDP formulation, reward shaping, exploration vs exploitation, policy gradients, curriculum learning.

### Phase 4 — LLM integration (2–4 weeks, stretch goal)

Claude API-powered homestead advisor:
- Anomaly detection: "Your biogas yield dropped 30% — likely cold weather + low cattle density"
- Tradeoff explainer: natural language explanation of RL agent decisions
- RAG over homestead documentation and agronomic literature

---

## Data strategy

Generate synthetic but realistic data by:
1. Pulling NOAA weather for the target region (default: central Texas climate)
2. Running the Phase 1 sim across all weather combinations
3. Adding noise + edge cases (drought, overcast weeks, equipment failure)
4. Storing everything in time-series tables: `(date, variable, value, homestead_id)`

This gives full control over the feature space and deep understanding of every variable —
a big advantage over downloaded datasets.

---

## ML learning goals (per phase)

| Phase | Key skills practiced |
|---|---|
| 2 | Feature engineering, regression, LSTM, model evaluation |
| 3 | RL environment design, reward shaping, PPO/DQN, policy visualization |
| 4 | RAG, prompt engineering, anomaly detection, Claude API |

---

## Current status

Phase 1 — not started. Begin with `sim/models/energy_balance.py`.

---

## Notes for Claude (Claude Code sessions)

- Always prefer building real, runnable code over scaffolding/stubs
- When adding a new sim model, include a `__main__` block that prints sample output
- Keep ML experiments in `notebooks/` first, then productionize into `ml/`
- The sim engine and ML layer should be decoupled — ML reads from the DB, never imports sim models directly
- Prioritize interpretability in Phase 2 (understand the model before making it bigger)
