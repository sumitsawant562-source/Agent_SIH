import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from app.db.supabase import get_supabase_admin_client, get_supabase_client
from app.schemas.trip import TripCreate, TripUpdate

# In-memory store used for development/testing when Supabase credentials are not yet configured
_dev_mock_trips: Dict[str, Dict[str, Any]] = {}


class TripService:
    @staticmethod
    def _is_supabase_available() -> bool:
        client = get_supabase_admin_client() or get_supabase_client()
        return client is not None

    @classmethod
    async def get_trips_for_user(cls, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all trips created by the specified authenticated user.
        Strictly filters by user_id.
        """
        client = get_supabase_admin_client() or get_supabase_client()
        if client:
            try:
                response = client.table("trips").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                return response.data or []
            except Exception as e:
                # If Supabase connection fails or table doesn't exist yet, log and check mock
                print(f"[Supabase Service Warning] Query failed: {e}")
                pass

        # Dev fallback filter
        return [t for t in _dev_mock_trips.values() if t.get("user_id") == user_id]

    @classmethod
    async def create_trip(cls, user_id: str, trip_data: TripCreate) -> Dict[str, Any]:
        """
        Creates a new trip belonging to the authenticated user.
        Forces user_id to match the verified token.
        """
        now = datetime.now(timezone.utc).isoformat()
        trip_dict = trip_data.model_dump(exclude_none=False)
        
        # Serialize fields for DB / JSON storage
        if trip_dict.get("travel_date") is not None:
            trip_dict["travel_date"] = str(trip_dict["travel_date"])
        if trip_dict.get("start_date") is not None:
            trip_dict["start_date"] = str(trip_dict["start_date"])
        if trip_dict.get("end_date") is not None:
            trip_dict["end_date"] = str(trip_dict["end_date"])
        if trip_dict.get("budget") is not None:
            trip_dict["budget"] = float(trip_dict["budget"])
            
        trip_dict["user_id"] = user_id

        client = get_supabase_admin_client() or get_supabase_client()
        if client:
            try:
                response = client.table("trips").insert(trip_dict).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            except Exception as e:
                print(f"[Supabase Service Warning] Insert failed: {e}")
                pass

        # Dev mock storage
        new_id = str(uuid.uuid4())
        record = {
            "id": new_id,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            **trip_dict
        }
        _dev_mock_trips[new_id] = record
        return record

    @classmethod
    async def get_trip_by_id(cls, user_id: str, trip_id: str) -> Dict[str, Any]:
        """
        Retrieves a single trip. Enforces that the trip belongs to the authenticated user.
        Raises 404 if not found, or 403 if it belongs to someone else.
        """
        client = get_supabase_admin_client() or get_supabase_client()
        if client:
            try:
                response = client.table("trips").select("*").eq("id", trip_id).execute()
                if not response.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Trip with ID '{trip_id}' was not found."
                    )
                trip = response.data[0]
                if str(trip.get("user_id")) != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access forbidden: You do not own this trip."
                    )
                return trip
            except HTTPException:
                raise
            except Exception as e:
                print(f"[Supabase Service Warning] Get trip failed: {e}")
                pass

        # Dev mock lookup
        if trip_id not in _dev_mock_trips:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID '{trip_id}' was not found."
            )
        trip = _dev_mock_trips[trip_id]
        if trip.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not own this trip."
            )
        return trip

    @classmethod
    async def update_trip(cls, user_id: str, trip_id: str, update_data: TripUpdate) -> Dict[str, Any]:
        """
        Updates a trip. Enforces user ownership.
        """
        # First verify existence and ownership
        await cls.get_trip_by_id(user_id, trip_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await cls.get_trip_by_id(user_id, trip_id)

        if "travel_date" in update_dict and update_dict["travel_date"] is not None:
            update_dict["travel_date"] = str(update_dict["travel_date"])
        if "start_date" in update_dict and update_dict["start_date"] is not None:
            update_dict["start_date"] = str(update_dict["start_date"])
        if "end_date" in update_dict and update_dict["end_date"] is not None:
            update_dict["end_date"] = str(update_dict["end_date"])
        if "budget" in update_dict and update_dict["budget"] is not None:
            update_dict["budget"] = float(update_dict["budget"])

        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        client = get_supabase_admin_client() or get_supabase_client()
        if client:
            try:
                response = client.table("trips").update(update_dict).eq("id", trip_id).eq("user_id", user_id).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            except Exception as e:
                print(f"[Supabase Service Warning] Update failed: {e}")
                pass

        # Dev mock update
        current = _dev_mock_trips[trip_id]
        current.update(update_dict)
        _dev_mock_trips[trip_id] = current
        return current

    @classmethod
    async def delete_trip(cls, user_id: str, trip_id: str) -> bool:
        """
        Deletes a trip. Enforces user ownership.
        """
        # Verify ownership
        await cls.get_trip_by_id(user_id, trip_id)

        client = get_supabase_admin_client() or get_supabase_client()
        if client:
            try:
                client.table("trips").delete().eq("id", trip_id).eq("user_id", user_id).execute()
                return True
            except Exception as e:
                print(f"[Supabase Service Warning] Delete failed: {e}")
                pass

        # Dev mock delete
        if trip_id in _dev_mock_trips:
            del _dev_mock_trips[trip_id]
        return True
