from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class User(UserCreate):
    id: int


router = APIRouter(prefix="/users", tags=["users"])
users: list[User] = []
next_id = 1


@router.get("/", response_model=list[User])
def list_users() -> list[User]:
    return users


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int) -> User:
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@router.post("/", response_model=User, status_code=201)
def create_user(payload: UserCreate) -> User:
    global next_id
    user = User(id=next_id, name=payload.name.strip(), email=payload.email)
    next_id += 1
    users.append(user)
    return user


@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserCreate) -> User:
    for index, user in enumerate(users):
        if user.id == user_id:
            updated = User(id=user_id, name=payload.name.strip(), email=payload.email)
            users[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{user_id}", status_code=200)
def delete_user(user_id: int) -> dict[str, str]:
    for index, user in enumerate(users):
        if user.id == user_id:
            users.pop(index)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="User not found")
