"""
Sample circuit and tire compound data.

Values are simplified/approximate, inspired by real F1 characteristics
(e.g. Monza is a low-degradation, high-speed track; Monaco/street circuits
have high pit loss due to narrow pit lanes and low overtaking difficulty
built into degradation assumptions here). Swap these out with real
telemetry (e.g. via the FastF1 library) once you want production-grade
accuracy.
"""

from .simulator import Circuit, TireCompound

CIRCUITS = {
    "monza": Circuit(name="Monza", total_laps=53, pit_loss_seconds=22.0),
    "monaco": Circuit(name="Monaco", total_laps=78, pit_loss_seconds=19.0),
    "silverstone": Circuit(name="Silverstone", total_laps=52, pit_loss_seconds=21.5),
    "spa": Circuit(name="Spa-Francorchamps", total_laps=44, pit_loss_seconds=23.0),
}

# Degradation and pace are illustrative, not scraped from real telemetry.
COMPOUND_SETS = {
    "monza": [
        TireCompound(name="soft", base_lap_time=80.0, degradation_per_lap=0.12, max_useful_life=18),
        TireCompound(name="medium", base_lap_time=80.8, degradation_per_lap=0.07, max_useful_life=28),
        TireCompound(name="hard", base_lap_time=81.6, degradation_per_lap=0.045, max_useful_life=40),
    ],
    "monaco": [
        TireCompound(name="soft", base_lap_time=71.5, degradation_per_lap=0.10, max_useful_life=25),
        TireCompound(name="medium", base_lap_time=72.2, degradation_per_lap=0.06, max_useful_life=38),
        TireCompound(name="hard", base_lap_time=73.0, degradation_per_lap=0.035, max_useful_life=55),
    ],
    "silverstone": [
        TireCompound(name="soft", base_lap_time=87.0, degradation_per_lap=0.14, max_useful_life=16),
        TireCompound(name="medium", base_lap_time=87.9, degradation_per_lap=0.08, max_useful_life=26),
        TireCompound(name="hard", base_lap_time=88.8, degradation_per_lap=0.05, max_useful_life=38),
    ],
    "spa": [
        TireCompound(name="soft", base_lap_time=106.0, degradation_per_lap=0.15, max_useful_life=15),
        TireCompound(name="medium", base_lap_time=107.1, degradation_per_lap=0.09, max_useful_life=24),
        TireCompound(name="hard", base_lap_time=108.2, degradation_per_lap=0.055, max_useful_life=35),
    ],
}


def get_circuit(name: str) -> Circuit:
    key = name.lower().strip()
    if key not in CIRCUITS:
        raise KeyError(f"Unknown circuit '{name}'. Available: {list(CIRCUITS.keys())}")
    return CIRCUITS[key]


def get_compounds(name: str):
    key = name.lower().strip()
    if key not in COMPOUND_SETS:
        raise KeyError(f"Unknown circuit '{name}'. Available: {list(COMPOUND_SETS.keys())}")
    return COMPOUND_SETS[key]
