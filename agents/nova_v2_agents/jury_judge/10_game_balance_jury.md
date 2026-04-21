# 10. Game Balance Jury Agent

## Doel
Evalueert game design parameters voor Dark Ledger en andere REX games.

## Scope
- Enemy stats (health, damage, speed)
- Weapon stats voor Black Ledger
- Player progression (XP curves, upgrade costs)
- Economy balance (loot, credits, prijzen)
- Difficulty curves per level/act

## Jury Leden

**1. DPS Ratio Analyzer**
- Tool: Python + simulation
- Checkt: damage per second past bij tier van encounter
- Detecteert: over/undertuned enemies

**2. Screen Time Detector**
- Tool: Python simulation
- Simuleert gemiddelde player vs enemy encounter
- Output: time-to-kill distribution

**3. Player Damage Analyzer**
- Tool: Simulation
- Checkt: schade per encounter binnen acceptabele range
- Prevent one-shot deaths of trivial fights

**4. Reward Proportionality**
- Tool: Python economic analysis
- Checkt: loot/credits/XP past bij effort
- Economy inflation/deflation detection

**5. Variety Detector**
- Tool: Python statistical analysis
- Checkt: nieuwe enemy/weapon onderscheidbaar van bestaande
- Prevent duplicate content

**6. Difficulty Curve Validator**
- Tool: Python + player progression simulator
- Checkt: curve past bij level progression
- Detect difficulty spikes of valleys

## Judge

**Balance Judge**
- Input: statische stats + simulatie resultaten
- Output: ship / rebalance (specifieke waardes) / scrap

## Cursor Prompt

```
Bouw een NOVA v2 Game Balance Jury voor Dark Ledger en andere games:

1. Python service `balance_jury/dps_analyzer.py`:
   - Input: enemy/weapon stats JSON
   - Simulate combat via simple formulas
   - Compare tegen tier benchmark (tier 1/2/3/boss)
   - Output: {dps, relative_to_tier, balanced: bool}

2. Python service `balance_jury/screen_time_sim.py`:
   - Input: enemy stats + avg player loadout
   - Simulate 100 encounters (monte carlo)
   - Output: {mean_ttk, distribution, outliers}

3. Python service `balance_jury/player_damage.py`:
   - Input: encounter definition
   - Simulate damage taken distribution
   - Check: one-shot risk, trivial encounter risk
   - Output: {avg_damage_taken, lethal_probability, too_easy}

4. Python service `balance_jury/reward_proportion.py`:
   - Input: encounter + rewards
   - Calculate effort (time + risk) vs reward
   - Economy model simulation
   - Output: {proportionate, inflation_risk, recommendations}

5. Python service `balance_jury/variety_detector.py`:
   - Input: nieuwe entity + existing entities
   - Feature vector comparison
   - Detect duplicates via cosine similarity
   - Output: {unique, most_similar_existing, diff_score}

6. Python service `balance_jury/difficulty_curve.py`:
   - Input: progression stats (level, expected player power)
   - Check curve smoothness
   - Detect spikes/valleys
   - Output: {curve_shape, problematic_transitions: []}

7. Python service `balance_jury/balance_judge.py`:
   - Aggregate all jury outputs
   - Generate specific rebalance suggestions
   - Output: {verdict, adjustments: [{stat, from, to, reason}]}

8. Load Dark Ledger existing stats voor benchmarks
9. N8n workflow voor batch balance checks
10. Integration met Godot: generate updated .gd files met rebalanced stats

Gebruik Python 3.11, numpy voor simulaties, FastAPI.
```

## Integratie met Dark Ledger

Huidige Dark Ledger heeft:
- ReputationManager.gd voor player state
- FactionData.gd voor enemy groups
- MissionData.gd voor encounter definitions
- GameConstants.gd voor balance waardes

Balance jury leest deze, runt analyse, suggest adjustments. Cursor past .gd files aan op basis van verdict.

## Test Scenario's

1. Nieuwe enemy voor act 2 → analyze vs act 2 benchmark
2. Weapon upgrade path → check progression economy
3. Boss encounter → check ttk + lethality
4. Loot table change → check economy impact

## Success Metrics

- Detect obvious imbalance (2x over/under tuned): 95%+
- Economy inflation detection: 85%+
- Useful rebalance suggestions (accepted by designer): 60%+
