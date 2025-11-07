"""
Lead Routes

CRUD operations for leads.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.models import Lead, LeadStatus
from app.services.couchbase_service import couchbase_service
from app.services.kafka_service import kafka_service

router = APIRouter(prefix="/leads", tags=["Leads"])


class LeadCreateRequest(BaseModel):
    """Request model for creating a lead"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    user_id: str
    notes: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    """Request model for updating a lead"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[LeadStatus] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


@router.post("/", response_model=Lead)
async def create_lead(request: LeadCreateRequest):
    """
    Create a new lead.

    Args:
        request: Lead creation data

    Returns:
        Created lead
    """
    try:
        lead = Lead(
            name=request.name,
            email=request.email,
            phone=request.phone,
            company=request.company,
            user_id=request.user_id,
            notes=request.notes
        )

        # Save to Couchbase
        lead = await couchbase_service.create_lead(lead)

        # Produce event to Kafka
        kafka_service.produce_lead_event(
            lead=lead.model_dump(),
            event_type='lead.created'
        )

        logger.info(f"Created lead: {lead.id}")
        return lead

    except Exception as e:
        logger.error(f"Failed to create lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    """
    Get a lead by ID.

    Args:
        lead_id: Lead ID

    Returns:
        Lead object
    """
    try:
        lead = await couchbase_service.get_lead(lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        return lead

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, request: LeadUpdateRequest):
    """
    Update a lead.

    Args:
        lead_id: Lead ID
        request: Update data

    Returns:
        Updated lead
    """
    try:
        # Get existing lead
        lead = await couchbase_service.get_lead(lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Update fields
        if request.name is not None:
            lead.name = request.name
        if request.email is not None:
            lead.email = request.email
        if request.phone is not None:
            lead.phone = request.phone
        if request.company is not None:
            lead.company = request.company
        if request.status is not None:
            lead.status = request.status
        if request.assigned_to is not None:
            lead.assigned_to = request.assigned_to
        if request.notes is not None:
            lead.notes = request.notes

        # Update timestamp
        from datetime import datetime
        lead.updated_at = datetime.utcnow()

        # Save to Couchbase
        lead = await couchbase_service.update_lead(lead)

        # Produce event to Kafka
        kafka_service.produce_lead_event(
            lead=lead.model_dump(),
            event_type='lead.updated'
        )

        logger.info(f"Updated lead: {lead.id}")
        return lead

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str):
    """
    Delete a lead.

    Args:
        lead_id: Lead ID

    Returns:
        Success message
    """
    try:
        success = await couchbase_service.delete_lead(lead_id)

        if not success:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Produce event to Kafka
        kafka_service.produce_lead_event(
            lead={'id': lead_id},
            event_type='lead.deleted'
        )

        logger.info(f"Deleted lead: {lead_id}")
        return {"success": True, "message": "Lead deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Lead])
async def list_leads(
    user_id: str = Query(..., description="User ID to filter leads"),
    status: Optional[LeadStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """
    List leads with filters.

    Args:
        user_id: User ID
        status: Optional status filter
        limit: Maximum results

    Returns:
        List of leads
    """
    try:
        filters = {'user_id': user_id}

        if status:
            filters['status'] = status.value

        leads = await couchbase_service.query_leads(filters, limit=limit)

        logger.info(f"Retrieved {len(leads)} leads for user {user_id}")
        return leads

    except Exception as e:
        logger.error(f"Failed to list leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
