from google.auth.transport import requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models import User, UserCreate, UserResponse
import json

load_dotenv()

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours instead of 30 minutes

# Google OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_google_token(token: str) -> Optional[dict]:
    """Verify Google ID token and return user info"""
    try:
        if not GOOGLE_CLIENT_ID:
            print("Error: GOOGLE_CLIENT_ID not configured")
            return None
            
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            print(f"Error: Wrong issuer. Expected Google, got {idinfo['iss']}")
            return None
            
        return idinfo
    except ValueError as e:
        print(f"Error verifying Google token (ValueError): {e}")
        return None
    except Exception as e:
        print(f"Error verifying Google token (Exception): {e}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token verification successful for user: {payload.get('sub')}")
        return payload
    except JWTError as e:
        print(f"Token verification failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in token verification: {e}")
        return None

def get_or_create_user(db: Session, google_user_info: dict) -> User:
    """Get existing user or create new one from Google info"""
    google_id = google_user_info.get('sub')
    email = google_user_info.get('email')
    name = google_user_info.get('name')
    picture = google_user_info.get('picture')
    
    # Check if user exists
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        # Create new user
        if not email or not name or not google_id:
            raise ValueError("Missing required user info from Google token")

        user_data = UserCreate(
            email=email,
            name=name,
            picture=picture,
            google_id=google_id
        )
        user = User(**user_data.dict())
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def get_current_user(db: Session, token: str) -> Optional[User]:
    """Get current user from JWT token"""
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    user_id = int(user_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    return user 