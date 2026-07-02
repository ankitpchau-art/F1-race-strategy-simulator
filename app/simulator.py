"""
Race Strategy Simulator - Core DP Engine

Models pit strategy as a shortest-path problem over the state space:
  state = (lap, tire_compound, tire_age)

At each lap you either:
  - stay out on the current tire (cost = degraded lap time), or
  - pit for a fresh tire of any compound (cost = pit_loss + fresh lap time)

We find the minimum total race time from lap 0 to the final lap using
memoized DP (equivalent to Dijkstra on a DAG since all edge weights are
positive and the graph has no cycles across laps).
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple, Optional


@dataclass(frozen=True)
class TireCompound:
    name: str
    base_lap_time: float       # seconds, on a fresh tire, no degradation
    degradation_per_lap: float  # seconds added per lap of tire age
    max_useful_life: int        # laps after which tire is unsafe/too slow to use


@dataclass(frozen=True)
class Circuit:
    name: str
    total_laps: int
    pit_loss_seconds: float    # time lost entering/exiting pits + stationary time


def degraded_lap_time(compound: TireCompound, tire_age: int) -> float:
    """Lap time increases roughly linearly with tire age (simplified model)."""
    return compound.base_lap_time + compound.degradation_per_lap * tire_age


class RaceStrategyOptimizer:
    def __init__(self, circuit: Circuit, compounds: List[TireCompound]):
        self.circuit = circuit
        self.compounds = {c.name: c for c in compounds}
        self.compound_names = tuple(self.compounds.keys())

    def solve(self) -> Dict:
        """
        Returns the optimal strategy: total race time and the sequence of
        stints (compound, start_lap, end_lap, stint_length).
        """
        total_laps = self.circuit.total_laps
        compounds = self.compound_names

        # memo[(lap_remaining, compound, tire_age)] -> (best_time, choice)
        memo: Dict[Tuple[int, str, int], float] = {}
        choice: Dict[Tuple[int, str, int], Optional[str]] = {}

        def best_time(laps_left: int, compound: str, tire_age: int) -> float:
            if laps_left == 0:
                return 0.0
            key = (laps_left, compound, tire_age)
            if key in memo:
                return memo[key]

            c = self.compounds[compound]

            # Option 1: stay out this lap (only if tire not past useful life)
            options = []
            if tire_age < c.max_useful_life:
                stay_cost = degraded_lap_time(c, tire_age) + best_time(
                    laps_left - 1, compound, tire_age + 1
                )
                options.append(("stay", stay_cost, None))

            # Option 2: pit now, switch to any compound (including same one, fresh)
            for new_compound in compounds:
                nc = self.compounds[new_compound]
                pit_cost = (
                    self.circuit.pit_loss_seconds
                    + degraded_lap_time(nc, 0)
                    + best_time(laps_left - 1, new_compound, 1)
                )
                options.append((f"pit:{new_compound}", pit_cost, new_compound))

            if not options:
                # Forced: tire past life and can't pit (shouldn't happen since
                # pitting is always available) - fallback safety
                options.append(("stay", degraded_lap_time(c, tire_age) + best_time(
                    laps_left - 1, compound, tire_age + 1
                ), None))

            best_choice, best_val, _ = min(options, key=lambda x: x[1])
            memo[key] = best_val
            choice[key] = best_choice
            return best_val

        # Try starting on every compound (fresh tire, age 0) and pick the best
        start_results = []
        for start_compound in compounds:
            t = best_time(total_laps, start_compound, 0)
            start_results.append((start_compound, t))
        best_start_compound, best_total = min(start_results, key=lambda x: x[1])

        # Reconstruct the path
        stints = []
        laps_left = total_laps
        compound = best_start_compound
        tire_age = 0
        stint_start_lap = 1
        current_stint_len = 0

        while laps_left > 0:
            key = (laps_left, compound, tire_age)
            action = choice.get(key, "stay")
            current_stint_len += 1

            if action.startswith("pit:"):
                new_compound = action.split(":")[1]
                stints.append({
                    "compound": compound,
                    "start_lap": stint_start_lap,
                    "end_lap": stint_start_lap + current_stint_len - 1,
                    "length": current_stint_len,
                })
                stint_start_lap += current_stint_len
                current_stint_len = 0
                compound = new_compound
                tire_age = 1
            else:
                tire_age += 1

            laps_left -= 1

        # close out final stint
        stints.append({
            "compound": compound,
            "start_lap": stint_start_lap,
            "end_lap": total_laps,
            "length": current_stint_len,
        })

        return {
            "circuit": self.circuit.name,
            "total_laps": total_laps,
            "total_time_seconds": round(best_total, 3),
            "total_time_formatted": _format_time(best_total),
            "num_pit_stops": len(stints) - 1,
            "stints": stints,
        }


class ConstrainedStrategyOptimizer:
    """
    Same DP as RaceStrategyOptimizer, but with an added `stops_used` dimension
    so we can ask "what's the best possible time using AT MOST N pit stops?"
    Used to build the 1-stop vs 2-stop vs 3-stop comparison view.
    """

    def __init__(self, circuit: Circuit, compounds: List[TireCompound], max_stops: int):
        self.circuit = circuit
        self.compounds = {c.name: c for c in compounds}
        self.compound_names = tuple(self.compounds.keys())
        self.max_stops = max_stops

    def solve(self) -> Dict:
        total_laps = self.circuit.total_laps
        compounds = self.compound_names
        memo: Dict[Tuple[int, str, int, int], float] = {}
        choice: Dict[Tuple[int, str, int, int], str] = {}

        def best_time(laps_left: int, compound: str, tire_age: int, stops_left: int) -> float:
            if laps_left == 0:
                return 0.0
            key = (laps_left, compound, tire_age, stops_left)
            if key in memo:
                return memo[key]

            c = self.compounds[compound]
            options = []

            if tire_age < c.max_useful_life:
                stay_cost = degraded_lap_time(c, tire_age) + best_time(
                    laps_left - 1, compound, tire_age + 1, stops_left
                )
                options.append(("stay", stay_cost))

            if stops_left > 0:
                for new_compound in compounds:
                    nc = self.compounds[new_compound]
                    pit_cost = (
                        self.circuit.pit_loss_seconds
                        + degraded_lap_time(nc, 0)
                        + best_time(laps_left - 1, new_compound, 1, stops_left - 1)
                    )
                    options.append((f"pit:{new_compound}", pit_cost))

            if not options:
                # Out of pit stops and tire past its legal life - this branch of
                # the search is physically infeasible, not a free pass. Mark it
                # as infinitely costly so the DP correctly rejects it instead of
                # silently letting a tire run forever (which would break the
                # guarantee that more allowed stops can never make the best
                # achievable time worse).
                memo[key] = float("inf")
                choice[key] = "infeasible"
                return float("inf")

            best_choice, best_val = min(options, key=lambda x: x[1])
            memo[key] = best_val
            choice[key] = best_choice
            return best_val

        start_results = []
        for start_compound in compounds:
            t = best_time(total_laps, start_compound, 0, self.max_stops)
            start_results.append((start_compound, t))
        best_start_compound, best_total = min(start_results, key=lambda x: x[1])

        if best_total == float("inf"):
            return {
                "max_stops": self.max_stops,
                "feasible": False,
                "total_time_seconds": None,
                "total_time_formatted": None,
            }

        return {
            "max_stops": self.max_stops,
            "feasible": True,
            "total_time_seconds": round(best_total, 3),
            "total_time_formatted": _format_time(best_total),
        }


def compare_strategies_by_stop_count(
    circuit: Circuit, compounds: List[TireCompound], max_stops_range: int = 4
) -> List[Dict]:
    """Returns best achievable time for 0, 1, 2, ... max_stops_range stops."""
    results = []
    for n in range(0, max_stops_range + 1):
        opt = ConstrainedStrategyOptimizer(circuit, compounds, max_stops=n)
        results.append(opt.solve())
    return results


def _format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h:
        return f"{h}h {m}m {s:.1f}s"
    return f"{m}m {s:.1f}s"


def compare_fixed_stop_strategies(
    circuit: Circuit, compounds: List[TireCompound], max_stops: int = 3
) -> List[Dict]:
    """
    Quick comparison utility: for each stop count, run the optimizer and
    just report the best time found overall (the DP already finds the
    global optimum, so this is mainly useful for a 'what-if' style table
    in the API / frontend).
    """
    optimizer = RaceStrategyOptimizer(circuit, compounds)
    result = optimizer.solve()
    return [result]
