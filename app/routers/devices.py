from fastapi import APIRouter, Depends

from app.schemas import Device, DeviceCreate, DeviceCreated
from app.security import get_storage, new_device_key, require_admin, require_user
from app.storage.base import Row, Storage

router = APIRouter()


@router.get("", response_model=list[Device], summary="List registered devices")
def list_devices(_: Row = Depends(require_user), storage: Storage = Depends(get_storage)):
    return storage.list_devices()


@router.post("", response_model=DeviceCreated, status_code=201,
             summary="Register a device and receive its API key (admin)")
def create_device(body: DeviceCreate, _: Row = Depends(require_admin), storage: Storage = Depends(get_storage)):
    key, key_hash = new_device_key()
    row = storage.insert_device({"device_name": body.device_name, "location": body.location,
                                 "status": "Active", "api_key_hash": key_hash})
    return DeviceCreated(**{k: row[k] for k in ("device_id", "device_name", "location", "status")},
                         created_at=row.get("created_at"), api_key=key)
