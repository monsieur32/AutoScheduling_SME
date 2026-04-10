"""
Master Data CRUD endpoints.
Provides generic CRUD for all master data tables:
  - Materials, Machines, Capabilities, Speeds, ProcessDefinitions, Projects

GET    /api/masterdata/{table}          → List records
POST   /api/masterdata/{table}          → Add a record
PUT    /api/masterdata/{table}/{id}     → Update a record
DELETE /api/masterdata/{table}/{id}     → Delete a record
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from ..database.session import get_db
from ..database.models import (
    Material, Machine, MachineCapability, MachineSpeed,
    ProcessDefinition, Project,
)

router = APIRouter(prefix="/api/masterdata", tags=["Master Data"])

# Registry of table names to ORM models and their PK column name
TABLE_REGISTRY = {
    "materials": (Material, "id"),
    "machines": (Machine, "id"),
    "capabilities": (MachineCapability, "id"),
    "speeds": (MachineSpeed, "id"),
    "processes": (ProcessDefinition, "id"),
    "projects": (Project, "id"),
}


def _get_model(table: str):
    if table not in TABLE_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown table '{table}'. Available: {list(TABLE_REGISTRY.keys())}",
        )
    return TABLE_REGISTRY[table]


def _to_dict(obj) -> dict:
    """Convert an ORM object to a plain dict (excluding internal attrs)."""
    return {c.name: getattr(obj, c.name) for c in obj.__class__.__table__.columns}


@router.get("/{table}")
def list_records(table: str, db: Session = Depends(get_db)):
    """List all records in a master data table."""
    model_cls, pk_col = _get_model(table)
    records = db.query(model_cls).all()
    return {
        "table": table,
        "records": [_to_dict(r) for r in records],
        "total": len(records),
    }


@router.post("/{table}", status_code=201)
def create_record(table: str, data: dict, db: Session = Depends(get_db)):
    """Add a new record to a master data table."""
    model_cls, pk_col = _get_model(table)

    try:
        obj = model_cls(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return _to_dict(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{table}/{record_id}")
def update_record(table: str, record_id: Any, data: dict, db: Session = Depends(get_db)):
    """Update an existing record."""
    model_cls, pk_col = _get_model(table)
    pk_attr = getattr(model_cls, pk_col)

    # Try int conversion for integer PKs
    try:
        record_id_cast = int(record_id)
    except (ValueError, TypeError):
        record_id_cast = record_id

    obj = db.query(model_cls).filter(pk_attr == record_id_cast).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found in {table}")

    for key, value in data.items():
        if hasattr(obj, key) and key != pk_col:
            setattr(obj, key, value)

    try:
        db.commit()
        db.refresh(obj)
        return _to_dict(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{table}/{record_id}", status_code=204)
def delete_record(table: str, record_id: Any, db: Session = Depends(get_db)):
    """Delete a record."""
    model_cls, pk_col = _get_model(table)
    pk_attr = getattr(model_cls, pk_col)

    try:
        record_id_cast = int(record_id)
    except (ValueError, TypeError):
        record_id_cast = record_id

    obj = db.query(model_cls).filter(pk_attr == record_id_cast).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found in {table}")

    db.delete(obj)
    db.commit()
