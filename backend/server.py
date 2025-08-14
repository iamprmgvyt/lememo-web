from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uuid
from datetime import datetime
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_user_id: str
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    discord_user_id: str
    username: str
    created_at: datetime

class UserCreate(BaseModel):
    discord_user_id: str
    username: str
    password: str
    
    @validator('discord_user_id')
    def validate_discord_user_id(cls, v):
        if not v.isdigit():
            raise ValueError('Discord User ID must contain only numbers')
        if len(v) < 17 or len(v) > 19:
            raise ValueError('Discord User ID must be 17-19 digits long')
        # Discord IDs started around 2015, so they should be > 100000000000000000
        if int(v) < 100000000000000000:
            raise ValueError('Invalid Discord User ID - ID too small')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Username must be at least 2 characters long')
        if len(v.strip()) > 32:
            raise ValueError('Username must be no more than 32 characters long')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    discord_user_id: str
    password: str
    
    @validator('discord_user_id')
    def validate_discord_user_id(cls, v):
        if not v.isdigit():
            raise ValueError('Discord User ID must contain only numbers')
        if len(v) < 17 or len(v) > 19:
            raise ValueError('Discord User ID must be 17-19 digits long')
        if int(v) < 100000000000000000:
            raise ValueError('Invalid Discord User ID - ID too small')
        return v

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    discord_user_id: str
    content: str
    server_id: Optional[str] = None
    server_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NoteCreate(BaseModel):
    discord_user_id: str
    content: str
    server_id: Optional[str] = None
    server_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None

class NoteUpdate(BaseModel):
    content: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        discord_user_id: str = payload.get("discord_user_id")
        if discord_user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return discord_user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(discord_user_id: str = Depends(verify_token)):
    user = await db.users.find_one({"discord_user_id": discord_user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

# Auth endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"discord_user_id": user_data.discord_user_id})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password
    password_hash = pwd_context.hash(user_data.password)
    
    # Create new user
    user = User(
        discord_user_id=user_data.discord_user_id,
        username=user_data.username,
        password_hash=password_hash
    )
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token({"discord_user_id": user.discord_user_id})
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Check if user exists
    user = await db.users.find_one({"discord_user_id": user_data.discord_user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify password
    if not pwd_context.verify(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create access token
    access_token = create_access_token({"discord_user_id": user_data.discord_user_id})
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# Notes endpoints
@api_router.post("/notes", response_model=Note)
async def create_note(note_data: NoteCreate):
    # Get or create user
    user = await db.users.find_one({"discord_user_id": note_data.discord_user_id})
    if not user:
        # Auto-create user if they don't exist (for Discord bot integration)
        user_create = User(discord_user_id=note_data.discord_user_id, username=f"User_{note_data.discord_user_id}")
        await db.users.insert_one(user_create.dict())
        user_id = user_create.id
    else:
        user_id = user["id"]
    
    # Create note
    note = Note(user_id=user_id, **note_data.dict())
    await db.notes.insert_one(note.dict())
    
    return note

@api_router.get("/notes", response_model=List[Note])
async def get_notes(
    current_user: UserResponse = Depends(get_current_user),
    search: Optional[str] = None,
    server_id: Optional[str] = None,
    limit: int = 100
):
    query = {"discord_user_id": current_user.discord_user_id}
    
    if search:
        query["content"] = {"$regex": search, "$options": "i"}
    
    if server_id:
        query["server_id"] = server_id
    
    notes = await db.notes.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [Note(**note) for note in notes]

@api_router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: str, current_user: UserResponse = Depends(get_current_user)):
    note = await db.notes.find_one({"id": note_id, "discord_user_id": current_user.discord_user_id})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note(**note)

@api_router.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: str, note_update: NoteUpdate, current_user: UserResponse = Depends(get_current_user)):
    note = await db.notes.find_one({"id": note_id, "discord_user_id": current_user.discord_user_id})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    updated_note = {**note, **note_update.dict(), "updated_at": datetime.utcnow()}
    await db.notes.replace_one({"id": note_id}, updated_note)
    
    return Note(**updated_note)

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, current_user: UserResponse = Depends(get_current_user)):
    result = await db.notes.delete_one({"id": note_id, "discord_user_id": current_user.discord_user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}

# Bot endpoints (no auth required for Discord bot)
@api_router.get("/bot/notes/{discord_user_id}")
async def get_user_notes_for_bot(discord_user_id: str, limit: int = 10):
    notes = await db.notes.find({"discord_user_id": discord_user_id}).sort("created_at", -1).limit(limit).to_list(limit)
    return [Note(**note) for note in notes]

@api_router.get("/bot/notes/{discord_user_id}/search")
async def search_notes_for_bot(discord_user_id: str, q: str, limit: int = 5):
    query = {
        "discord_user_id": discord_user_id,
        "content": {"$regex": q, "$options": "i"}
    }
    notes = await db.notes.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [Note(**note) for note in notes]

@api_router.delete("/bot/notes/{note_id}")
async def delete_note_for_bot(note_id: str):
    result = await db.notes.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}

# Health check
@api_router.get("/")
async def root():
    return {"message": "Discord Notes API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()