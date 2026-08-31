from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Path
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.trip import TripCreate, TripUpdate, TripResponse, TripListResponse
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("", response_model=TripListResponse, summary="List User Trips")
async def list_trips(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns all trips created by the currently authenticated user.
    """
    trips = await TripService.get_trips_for_user(current_user.id)
    return TripListResponse(total=len(trips), trips=trips)


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED, summary="Create Trip")
async def create_trip(
    trip_in: TripCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Creates a new trip draft belonging to the currently authenticated user.
    """
    try:
        created = await TripService.create_trip(current_user.id, trip_in)
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the trip: {str(e)}"
        )


@router.get("/{trip_id}", response_model=TripResponse, summary="Get Trip by ID")
async def get_trip(
    trip_id: str = Path(..., description="The unique UUID of the trip"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Retrieves a single trip. Enforces that the trip belongs to the authenticated user.
    """
    return await TripService.get_trip_by_id(current_user.id, trip_id)


@router.put("/{trip_id}", response_model=TripResponse, summary="Update Trip")
async def update_trip(
    trip_in: TripUpdate,
    trip_id: str = Path(..., description="The unique UUID of the trip to update"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Updates an existing trip belonging to the authenticated user.
    """
    return await TripService.update_trip(current_user.id, trip_id, trip_in)


@router.delete("/{trip_id}", status_code=status.HTTP_200_OK, summary="Delete Trip")
async def delete_trip(
    trip_id: str = Path(..., description="The unique UUID of the trip to delete"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Deletes a trip belonging to the authenticated user.
    """
    success = await TripService.delete_trip(current_user.id, trip_id)
    return {"message": "Trip successfully deleted", "trip_id": trip_id}
