"""
Digital Twin & Attack-Path REST API Router (Phase 8)
Endpoints for topological graphing, attack vector discovery, blast radius, and choke-point defense.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.digital_twin.graph_engine import DigitalTwinGraphEngine
from app.schemas.digital_twin import (
    DigitalTwinGraphResponse, AttackPathRequest, AttackPathResponse,
    BlastRadiusResponse, ChokePointResponse, SimulateCompromiseRequest
)

router = APIRouter(prefix="/digital-twin")


@router.get("/graph", response_model=DigitalTwinGraphResponse)
def get_digital_twin_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full topological graph nodes and edges for the organization's infrastructure."""
    engine = DigitalTwinGraphEngine(db, current_user.organization_id)
    return engine.get_graph_data()


@router.post("/attack-paths", response_model=AttackPathResponse)
def discover_attack_paths(
    req: AttackPathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compute traversable attack paths between source and target nodes with MITRE ATT&CK techniques."""
    try:
        engine = DigitalTwinGraphEngine(db, current_user.organization_id)
        return engine.calculate_attack_paths(req)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Attack path calculation failed: {str(e)}")


@router.get("/blast-radius/{asset_id}", response_model=BlastRadiusResponse)
def get_asset_blast_radius(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate the downstream blast radius and reachability if asset_id is compromised."""
    try:
        engine = DigitalTwinGraphEngine(db, current_user.organization_id)
        return engine.calculate_blast_radius(asset_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Blast radius analysis failed: {str(e)}")


@router.get("/choke-points", response_model=ChokePointResponse)
def get_defensive_choke_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Identify optimal defensive choke points in the network using NetworkX graph centrality."""
    try:
        engine = DigitalTwinGraphEngine(db, current_user.organization_id)
        return engine.identify_choke_points()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Choke point analysis failed: {str(e)}")


@router.post("/simulate-compromise")
def simulate_node_compromise(
    req: SimulateCompromiseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dynamically flag a node as compromised or restored for what-if attack simulation."""
    DigitalTwinGraphEngine.set_simulated_compromise(req.node_id, req.compromised)
    engine = DigitalTwinGraphEngine(db, current_user.organization_id)
    return {
        "status": "SUCCESS",
        "node_id": req.node_id,
        "is_compromised": req.compromised,
        "updated_summary": engine.get_graph_data().summary
    }


@router.post("/reset-simulation")
def reset_simulation(
    current_user: User = Depends(get_current_user)
):
    """Reset all transient compromise states back to live baseline."""
    DigitalTwinGraphEngine.clear_simulated_compromises()
    return {"status": "SUCCESS", "message": "All transient compromise states cleared."}
