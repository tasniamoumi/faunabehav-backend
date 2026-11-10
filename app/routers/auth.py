from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import Token, User, UserCreate
from app.security import create_token, get_storage, hash_password, require_admin, require_user, verify_password
from app.storage.base import Row, Storage

router = APIRouter()


@router.post("/login", response_model=Token, summary="Exchange username and password for a JWT")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), storage: Storage = Depends(get_storage)):
    user = storage.get_user_by_username(form.username)
    if user is None or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "incorrect username or password")
    return Token(access_token=create_token(user, request.app.state.settings))


@router.get("/me", response_model=User)
def me(user: Row = Depends(require_user)):
    return user


@router.post("/users", response_model=User, status_code=201, summary="Create a dashboard user (admin)")
def create_user(body: UserCreate, _: Row = Depends(require_admin), storage: Storage = Depends(get_storage)):
    if storage.get_user_by_username(body.username):
        raise HTTPException(409, "username already exists")
    return storage.insert_user({"username": body.username, "password_hash": hash_password(body.password),
                                "role": body.role})
