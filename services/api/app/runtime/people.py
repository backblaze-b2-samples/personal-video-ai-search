import logging

from fastapi import APIRouter, HTTPException

from app.service.people import (
    PersonNotFoundError,
    faces_available,
    list_people,
    name_person,
    person_clips,
)
from app.types import Clip, NamePersonRequest, Person

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/people", response_model=list[Person])
async def list_people_endpoint():
    return list_people()


@router.get("/people/available")
async def people_available_endpoint():
    """Whether the local face stack is installed. The UI uses this to show a
    clear 'face indexing not available' state instead of an empty page."""
    return {"available": faces_available()}


@router.get("/people/{cluster_id}/clips", response_model=list[Clip])
async def person_clips_endpoint(cluster_id: str):
    try:
        return person_clips(cluster_id)
    except PersonNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail) from None


@router.post("/people/{cluster_id}/name", response_model=Person)
async def name_person_endpoint(cluster_id: str, req: NamePersonRequest):
    try:
        return name_person(cluster_id, req.name)
    except PersonNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail) from None
