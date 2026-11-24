"""
Network Topologies & Simulation API Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.topology import Topology
from app.models.segment import NetworkSegment
from app.models.device import NetworkDevice
from app.models.connection import NetworkConnection
from app.models.audit import AuditLog
from app.schemas.network import (
    TopologyCreate, TopologyUpdate, TopologyResponse, TopologyDetailResponse,
    DeploymentPreview, DeploymentResult
)
from app.core.dependencies import get_current_user, require_role
from app.network.manager import network_manager
from app.network.safety import HostProtectionError

router = APIRouter()


@router.get("/topologies", response_model=List[TopologyResponse])
def list_topologies(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists network topologies accessible to the user's organization."""
    query = db.query(Topology)
    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id:
        query = query.filter(Topology.organization_id == current_user.organization_id)
    return query.offset(skip).limit(limit).all()


@router.post("/topologies", response_model=TopologyDetailResponse, status_code=status.HTTP_201_CREATED)
def create_topology(
    payload: TopologyCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Creates a new visual network topology with segments, devices, and connections."""
    topology = Topology(
        name=payload.name,
        description=payload.description,
        site_id=payload.site_id,
        organization_id=current_user.organization_id or "default-org",
        status="DRAFT",
        graph_data=payload.graph_data
    )
    db.add(topology)
    db.flush()

    # Map created devices for link connection lookups
    created_devices = {}
    for dev_in in (payload.devices or []):
        dev = NetworkDevice(
            topology_id=topology.id,
            name=dev_in.name,
            device_type=dev_in.device_type,
            namespace_name=dev_in.namespace_name or f"cl-ns-{dev_in.name.lower().replace(' ', '-')}",
            ip_address=dev_in.ip_address,
            mac_address=dev_in.mac_address,
            config_data=dev_in.config_data,
            status="STOPPED"
        )
        db.add(dev)
        db.flush()
        created_devices[dev_in.name] = dev

    created_segments = {}
    for seg_in in (payload.segments or []):
        seg = NetworkSegment(
            topology_id=topology.id,
            name=seg_in.name,
            bridge_name=seg_in.bridge_name,
            vlan_id=seg_in.vlan_id,
            cidr_block=seg_in.cidr_block,
            gateway_ip=seg_in.gateway_ip,
            status="INACTIVE"
        )
        db.add(seg)
        db.flush()
        created_segments[seg_in.name] = seg

    for conn_in in (payload.connections or []):
        conn = NetworkConnection(
            topology_id=topology.id,
            source_device_id=conn_in.source_device_id,
            target_device_id=conn_in.target_device_id,
            segment_id=conn_in.segment_id,
            veth_name=conn_in.veth_name,
            peer_name=conn_in.peer_name,
            status="DISCONNECTED"
        )
        db.add(conn)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="TOPOLOGY_CREATED",
        resource_type="network_topology",
        resource_id=topology.id,
        status="SUCCESS",
        details=f"Created network topology '{topology.name}'"
    )
    db.add(audit)
    db.commit()
    db.refresh(topology)

    return topology


@router.get("/topologies/{topology_id}", response_model=TopologyDetailResponse)
def get_topology(
    topology_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full details of a network topology including nodes, links, and segments."""
    topology = db.query(Topology).filter(Topology.id == topology_id).first()
    if not topology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topology not found")
    return topology


@router.put("/topologies/{topology_id}", response_model=TopologyResponse)
def update_topology(
    topology_id: str,
    payload: TopologyUpdate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Updates topology attributes or saves React Flow canvas graph layout."""
    topology = db.query(Topology).filter(Topology.id == topology_id).first()
    if not topology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topology not found")

    if payload.name is not None:
        topology.name = payload.name
    if payload.description is not None:
        topology.description = payload.description
    if payload.graph_data is not None:
        topology.graph_data = payload.graph_data

    db.commit()
    db.refresh(topology)
    return topology


@router.delete("/topologies/{topology_id}", status_code=status.HTTP_200_OK)
def delete_topology(
    topology_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Deletes a topology after ensuring all deployed kernel resources are cleaned up."""
    topology = db.query(Topology).filter(Topology.id == topology_id).first()
    if not topology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topology not found")

    if topology.status == "DEPLOYED":
        network_manager.teardown_topology(db, topology_id, current_user.username)

    db.delete(topology)
    db.commit()
    return {"message": f"Topology '{topology.name}' and all associated resources deleted successfully"}


@router.get("/topologies/{topology_id}/preview", response_model=DeploymentPreview)
def preview_topology_deployment(
    topology_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates a pre-flight safety check and preview of all virtual network resources."""
    topology = db.query(Topology).filter(Topology.id == topology_id).first()
    if not topology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topology not found")

    preview = network_manager.preview_deployment(topology)
    return preview


@router.post("/topologies/{topology_id}/deploy", response_model=DeploymentResult)
def deploy_topology(
    topology_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Deploys a virtual network topology into isolated namespaces and virtual bridges."""
    try:
        result = network_manager.deploy_topology(db, topology_id, current_user.username)
        return result
    except HostProtectionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Deployment failure: {str(e)}")


@router.post("/topologies/{topology_id}/teardown", response_model=DeploymentResult)
def teardown_topology(
    topology_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Safely tears down and removes all virtual network resources created for a topology."""
    try:
        result = network_manager.teardown_topology(db, topology_id, current_user.username)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Teardown failure: {str(e)}")
