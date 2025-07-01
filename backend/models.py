from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class TimeLimit(str, Enum):
    """Time limit options in minutes"""
    TEN = "10"
    TWENTY = "20"
    THIRTY = "30"
    SIXTY = "60"  # 1 hour for deeper summaries

class Chunk(BaseModel):
    """Represents a text chunk from the PDF"""
    text: str
    page_number: int
    word_count: int
    reading_time_minutes: float
    importance_score: float
    headings: List[str] = []
    keywords: List[str] = []

class OutlineItem(BaseModel):
    """Represents an outline item"""
    title: str
    page_number: int
    reading_time_minutes: float

class KeyPoint(BaseModel):
    """Represents a key point from the content"""
    point: str
    category: Optional[str] = None
    warning: Optional[str] = None  # For warnings about images, equations, etc.

class QuizQuestion(BaseModel):
    """Represents a quiz question"""
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class SummaryResponse(BaseModel):
    """Response model for the PDF summary"""
    outline: List[OutlineItem]
    condensed_content: List[Chunk]
    key_points: List[KeyPoint]
    total_reading_time_minutes: float
    total_word_count: int
    quiz: List[QuizQuestion]
    original_filename: str
    processing_notes: List[str]
    key_points_warning: Optional[str] = None  # Warning if more than 10 key points

class ProcessingStatus(BaseModel):
    """Status model for processing updates"""
    status: str
    message: str
    progress: float = 0.0

# Database Models
class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True)
    razorpay_customer_id = Column(String, nullable=True)  # For webhook processing
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    history = relationship("UserHistory", back_populates="user")
    subscription = relationship("Subscription", back_populates="user")

class UserHistory(Base):
    """User history model for tracking processed PDFs"""
    __tablename__ = "user_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_filename = Column(String)
    time_limit = Column(Integer)
    total_reading_time = Column(Float)
    total_word_count = Column(Integer)
    outline_json = Column(Text)  # JSON string of outline
    condensed_content_json = Column(Text)  # JSON string of content
    key_points_json = Column(Text)  # JSON string of key points
    quiz_json = Column(Text, nullable=True)  # JSON string of quiz
    processing_notes_json = Column(Text)  # JSON string of notes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="history")

# Pydantic models for API
class UserCreate(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    google_id: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str] = None
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class GoogleAuthRequest(BaseModel):
    id_token: str

# History Models
class HistoryItem(BaseModel):
    id: int
    original_filename: str
    time_limit: TimeLimit
    total_reading_time: float
    total_word_count: int
    created_at: str

class HistoryResponse(BaseModel):
    history: List[HistoryItem]

# Pricing and Subscription Models
class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    UNLIMITED = "unlimited"

class PricingPlan(BaseModel):
    id: str
    name: str
    price: int  # in paise (₹1 = 100 paise)
    pdf_limit: Optional[int]  # None for unlimited
    features: List[str]
    popular: bool = False

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

class Subscription(Base):
    """Subscription model for tracking user subscriptions"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_type = Column(String)  # free, starter, unlimited
    status = Column(String, default=SubscriptionStatus.ACTIVE)
    razorpay_subscription_id = Column(String, nullable=True)
    razorpay_customer_id = Column(String, nullable=True)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="subscription")

class SubscriptionResponse(BaseModel):
    """Response model for subscription status"""
    plan_type: PlanType
    status: SubscriptionStatus
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    days_remaining: int
    can_process: bool
    message: str = ""

class CreateSubscriptionRequest(BaseModel):
    plan_type: PlanType
    coupon_code: Optional[str] = None

class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = True

class UserSubscription(BaseModel):
    user_id: int
    plan_type: PlanType
    status: SubscriptionStatus
    pdfs_used_this_month: int
    pdf_limit: int
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PaymentRequest(BaseModel):
    plan_type: PlanType
    coupon_code: Optional[str] = None
    email: str

class PaymentResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key: str
    prefill: Dict[str, str]

class CouponValidation(BaseModel):
    valid: bool
    discount_amount: int = 0
    message: str = ""

class UserQuota(BaseModel):
    plan_type: PlanType
    pdfs_used: int
    pdf_limit: Optional[int]
    can_process: bool
    message: str = ""

class PaymentVerificationRequest(BaseModel):
    payment_id: str
    order_id: str
    signature: str
    plan_type: str 