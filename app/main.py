import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .simulator import RaceStrategyOptimizer, compare_strategies_by_stop_count
from .data import get_circuit, get_compounds, CIRCUITS

app = FastAPI(
    title="F1 Race Strategy Simulator",
    description="Computes the optimal pit strategy for a given circuit using DP over (lap, compound, tire_age) states.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "F1 Race Strategy Simulator API",
        "dashboard": "/dashboard",
        "endpoints": ["/circuits", "/simulate?circuit=monza", "/compare?circuit=monza&max_stops=4"],
    }


_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/dashboard", StaticFiles(directory=_FRONTEND_DIR, html=True), name="dashboard")


@app.get("/circuits")
def list_circuits():
    return {
        name: {"total_laps": c.total_laps, "pit_loss_seconds": c.pit_loss_seconds}
        for name, c in CIRCUITS.items()
    }


@app.get("/simulate")
def simulate(circuit: str = "monza"):
    try:
        circuit_obj = get_circuit(circuit)
        compounds = get_compounds(circuit)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    optimizer = RaceStrategyOptimizer(circuit_obj, compounds)
    result = optimizer.solve()
    return result


@app.get("/compare")
def compare(circuit: str = "monza", max_stops: int = 4):
    try:
        circuit_obj = get_circuit(circuit)
        compounds = get_compounds(circuit)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    results = compare_strategies_by_stop_count(circuit_obj, compounds, max_stops_range=max_stops)
    return {"circuit": circuit_obj.name, "comparison": results}
