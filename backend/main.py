from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from pdf_processor import PDFProcessor
from models import TimeLimit, SummaryResponse, User, UserHistory, HistoryResponse, Token, GoogleAuthRequest, HistoryItem, Base, PricingPlan, PaymentRequest, PaymentResponse, CouponValidation, UserQuota, UserResponse, PlanType, PaymentVerificationRequest, CreateSubscriptionRequest, CancelSubscriptionRequest, Subscription, SubscriptionStatus
from database import get_db, engine
from auth import verify_google_token, create_access_token, get_current_user, get_or_create_user
from pdf_generator import StudyPackPDFGenerator
from pricing import PricingService, razorpay_utility
import logging
import json
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables - IMPORTANT: This must be after importing all models
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Thirty-Minute PDF API",
    description="API for generating time-based PDF summaries with user authentication",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://snapreads.in",
        "https://www.snapreads.in",
    ],  # React dev servers and production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
pdf_processor = PDFProcessor()
pdf_generator = StudyPackPDFGenerator()
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

class CouponRequest(BaseModel):
    coupon_code: Optional[str] = None
    user_email: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Thirty-Minute PDF API is running!"}

@app.post("/auth/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate user with Google OAuth"""
    try:
        # Verify Google token
        google_user_info = verify_google_token(request.id_token)
        if not google_user_info:
            logger.error("Google token verification failed")
            raise HTTPException(status_code=401, detail="Invalid Google token. Please try signing in again.")
        
        # Get or create user
        user = get_or_create_user(db, google_user_info)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=30)
        )
        
        # Convert User to UserResponse
        user_response = UserResponse(
            id=getattr(user, 'id'),
            email=getattr(user, 'email'),
            name=getattr(user, 'name'),
            picture=getattr(user, 'picture'),
            created_at=getattr(user, 'created_at').isoformat() if getattr(user, 'created_at') else ""
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    # Authenticate user
    logger.info(f"Received Authorization header: {credentials.credentials[:20]}..." if credentials.credentials else "No Authorization header")
    user = get_current_user(db, credentials.credentials)
    logger.info(f"User authentication result: {user.id if user else 'None'}")
    if not user:
        # Check if it's a token expiration issue
        try:
            jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        except JWTError as e:
            if "expired" in str(e).lower():
                raise HTTPException(status_code=401, detail="Token has expired. Please sign in again.")
            else:
                raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")
    return user

@app.get("/history", response_model=HistoryResponse)
async def get_user_history(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get user's processing history"""
    user = get_current_user(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check user quota/plan
    quota = PricingService.get_user_quota(db, getattr(user, 'id'), getattr(user, 'email'))
    if quota.plan_type == PlanType.FREE and quota.pdf_limit is not None and quota.pdfs_used >= quota.pdf_limit:
        raise HTTPException(status_code=403, detail="Upgrade to view full history.")
    
    history_items = db.query(UserHistory).filter(
        UserHistory.user_id == user.id
    ).order_by(UserHistory.created_at.desc()).all()
    
    # For free users, only show first 3 history items
    if quota.plan_type == PlanType.FREE:
        history_items = history_items[:3]
    
    # Convert UserHistory objects to HistoryItem objects
    history_response_items = []
    for item in history_items:
        try:
            # Always convert time_limit to string
            time_limit_value = getattr(item, 'time_limit')
            time_limit_str = str(time_limit_value)
            time_limit_enum = TimeLimit(time_limit_str)
            # Always convert created_at to ISO string
            created_at_value = getattr(item, 'created_at')
            if hasattr(created_at_value, 'isoformat'):
                created_at_str = created_at_value.isoformat()
            else:
                created_at_str = str(created_at_value)
            history_response_items.append(HistoryItem(
                id=getattr(item, 'id'),
                original_filename=str(getattr(item, 'original_filename')),
                time_limit=time_limit_enum,
                total_reading_time=getattr(item, 'total_reading_time'),
                total_word_count=getattr(item, 'total_word_count'),
                created_at=created_at_str
            ))
        except Exception as e:
            print(f"Skipping history row id={getattr(item, 'id', 'unknown')} due to error: {e}")
            continue
    
    return HistoryResponse(history=history_response_items)

@app.get("/history/{history_id}")
async def get_history_item(
    history_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get specific history item with full data"""
    user = get_current_user(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    history_item = db.query(UserHistory).filter(
        UserHistory.id == history_id,
        UserHistory.user_id == user.id
    ).first()
    
    if not history_item:
        raise HTTPException(status_code=404, detail="History item not found")
    
    # Parse JSON data
    try:
        outline = json.loads(str(getattr(history_item, 'outline_json')))
        condensed_content = json.loads(str(getattr(history_item, 'condensed_content_json')))
        key_points = json.loads(str(getattr(history_item, 'key_points_json')))
        quiz_json = getattr(history_item, 'quiz_json')
        quiz = json.loads(str(quiz_json)) if quiz_json else []
        processing_notes = json.loads(str(getattr(history_item, 'processing_notes_json')))
        
        return SummaryResponse(
            outline=outline,
            condensed_content=condensed_content,
            key_points=key_points,
            total_reading_time_minutes=float(getattr(history_item, 'total_reading_time')),
            total_word_count=int(getattr(history_item, 'total_word_count')),
            quiz=quiz if quiz else [],
            original_filename=str(getattr(history_item, 'original_filename')),
            processing_notes=processing_notes
        )
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing history item JSON: {e}")
        raise HTTPException(status_code=500, detail="Error parsing history data")

@app.post("/process-pdf", response_model=SummaryResponse)
async def process_pdf(
    file: UploadFile = File(...),
    time_limit: TimeLimit = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Process a PDF file and generate a time-based summary
    
    Args:
        file: PDF file to process
        time_limit: Time limit in minutes (10, 20, 30, or 60)
        credentials: JWT token for authentication
    
    Returns:
        SummaryResponse: Structured summary with outline, content, and quiz
    """
    try:
        # Add detailed logging
        logger.info(f"Received process-pdf request:")
        logger.info(f"  File: {file.filename}")
        logger.info(f"  Time limit: {time_limit} (type: {type(time_limit)})")
        logger.info(f"  Available time limits: {[t.value for t in TimeLimit]}")
        
        # Authenticate user
        logger.info(f"Received Authorization header: {credentials.credentials[:20]}..." if credentials.credentials else "No Authorization header")
        user = get_current_user(db, credentials.credentials)
        logger.info(f"User authentication result: {user.id if user else 'None'}")
        if not user:
            # Check if it's a token expiration issue
            try:
                jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
            except JWTError as e:
                if "expired" in str(e).lower():
                    raise HTTPException(status_code=401, detail="Token has expired. Please sign in again.")
                else:
                    raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Check user quota before processing
        if user:
            quota = PricingService.get_user_quota(db, int(getattr(user, 'id')))
            if quota.plan_type == PlanType.FREE and quota.pdfs_used >= 3:
                raise HTTPException(status_code=403, detail="You have used all 3 free PDFs. Please upgrade to continue.")
            if not quota.can_process:
                raise HTTPException(status_code=403, detail=quota.message)
            plan_type = quota.plan_type.value if hasattr(quota.plan_type, 'value') else str(quota.plan_type)
        else:
            plan_type = 'free'
        
        logger.info(f"Processing PDF: {file.filename} with {time_limit} minute limit for user {user.id if user else 'None'}")
        
        # Read file content
        content = await file.read()
        
        # Process the PDF
        summary = pdf_processor.process_pdf(content, time_limit, plan_type=plan_type)
        
        # Update the original filename
        summary.original_filename = file.filename
        
        # Note: Usage tracking is now handled by subscription system
        # No need to increment usage manually
        
        # Save to user history
        history_item = UserHistory(
            user_id=user.id if user else 0,
            original_filename=file.filename,
            time_limit=time_limit,
            total_reading_time=summary.total_reading_time_minutes,
            total_word_count=summary.total_word_count,
            outline_json=json.dumps([item.model_dump() for item in summary.outline]),
            condensed_content_json=json.dumps([chunk.model_dump() for chunk in summary.condensed_content]),
            key_points_json=json.dumps([point.model_dump() for point in summary.key_points]),
            quiz_json=json.dumps([q.model_dump() for q in summary.quiz]) if summary.quiz else None,
            processing_notes_json=json.dumps(summary.processing_notes)
        )
        
        db.add(history_item)
        db.commit()
        
        # Increment usage for free users
        if plan_type == 'free' and user and isinstance(user.id, int):
            PricingService.increment_user_usage(user.id)
        
        logger.info(f"Successfully processed PDF: {file.filename} and saved to history")
        return summary
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/download-pdf/{history_id}")
async def download_pdf(
    history_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Download a PDF study pack for a specific history item"""
    try:
        # Authenticate user
        user = get_current_user(db, credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check user quota/plan
        quota = PricingService.get_user_quota(db, getattr(user, 'id'), getattr(user, 'email'))
        if quota.plan_type == PlanType.FREE:
            raise HTTPException(status_code=403, detail="Subscribe to download PDFs.")
        
        # Get history item
        history_item = db.query(UserHistory).filter(
            UserHistory.id == history_id,
            UserHistory.user_id == user.id
        ).first()
        
        if not history_item:
            raise HTTPException(status_code=404, detail="History item not found")
        
        # Parse JSON data
        try:
            outline = json.loads(str(getattr(history_item, 'outline_json')))
            condensed_content = json.loads(str(getattr(history_item, 'condensed_content_json')))
            key_points = json.loads(str(getattr(history_item, 'key_points_json')))
            quiz_json = getattr(history_item, 'quiz_json')
            quiz = json.loads(str(quiz_json)) if quiz_json else None
            processing_notes = json.loads(str(getattr(history_item, 'processing_notes_json')))
            
            summary = SummaryResponse(
                outline=outline,
                condensed_content=condensed_content,
                key_points=key_points,
                total_reading_time_minutes=float(getattr(history_item, 'total_reading_time')),
                total_word_count=int(getattr(history_item, 'total_word_count')),
                quiz=quiz if quiz else [],
                original_filename=str(getattr(history_item, 'original_filename')),
                processing_notes=processing_notes
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing history item JSON: {e}")
            raise HTTPException(status_code=500, detail="Error parsing history data")
        
        # Generate PDF
        pdf_buffer = pdf_generator.generate_pdf(summary, str(getattr(history_item, 'original_filename')))
        
        # Create filename for download
        base_filename = os.path.splitext(str(getattr(history_item, 'original_filename')))[0]
        download_filename = f"{base_filename}_study_pack_{getattr(history_item, 'time_limit')}min.pdf"
        
        def iterfile():
            yield pdf_buffer.getvalue()
        
        return StreamingResponse(
            iterfile(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Thirty-Minute PDF API"}

@app.get("/test-auth")
async def test_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Test endpoint to check authentication"""
    logger.info(f"Testing auth with token: {credentials.credentials[:20]}..." if credentials.credentials else "No token")
    user = get_current_user(db, credentials.credentials)
    if user:
        return {"message": "Auth successful", "user_id": user.id, "email": user.email}
    else:
        return {"message": "Auth failed", "user": None}

@app.get("/pricing/plans")
async def get_pricing_plans():
    """Get all available pricing plans"""
    plans = PricingService.get_pricing_plans()
    return {"plans": plans}

@app.post("/pricing/validate-coupon")
async def validate_coupon(request: CouponRequest):
    print("Received coupon validation request:", request)
    if not request.coupon_code:
        return {"valid": False, "message": "Coupon code is required"}
    return PricingService.validate_coupon(request.coupon_code, request.user_email)

@app.post("/pricing/create-subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a Razorpay subscription"""
    try:
        # Get current user
        user = get_current_user(db, credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if this is a free plan
        if request.plan_type == PlanType.FREE:
            # For free plans, just create a free subscription
            subscription = PricingService.create_user_subscription(
                db=db,
                user_id=int(getattr(user, 'id')),
                plan_type=request.plan_type,
                subscription_id="free_subscription",
                customer_id="free_customer",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=36500)  # 100 years for free plan
            )
            return {"message": "Free plan activated successfully", "is_free": True}
        
        # Create subscription for paid plans
        subscription_data = PricingService.create_razorpay_subscription(
            plan_type=request.plan_type,
            user_email=str(user.email),
            coupon_code=request.coupon_code
        )

        # If is_free, create the subscription in the database and return
        if subscription_data.get('is_free'):
            subscription = PricingService.create_user_subscription(
                db=db,
                user_id=int(getattr(user, 'id')),
                plan_type=request.plan_type,
                subscription_id="free_coupon",
                customer_id="free_coupon",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=36500)  # 100 years for free coupon
            )
            return {"message": subscription_data.get('message', 'Free plan activated!'), "is_free": True}

        return subscription_data
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pricing/verify-subscription")
async def verify_subscription(
    request: dict = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify subscription payment and activate subscription"""
    try:
        logger.info(f"/pricing/verify-subscription called with: {request}")
        # Get current user
        user = get_current_user(db, credentials.credentials)
        logger.info(f"User from token: {user}")
        if not user:
            logger.error("No user found for token!")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Validate plan_type
        valid_plan_types = {pt.value for pt in PlanType}
        logger.info(f"Valid plan types: {valid_plan_types}, received: {request.get('plan_type')}")
        if request.get('plan_type') not in valid_plan_types:
            logger.error(f"Invalid plan_type: {request.get('plan_type')}")
            raise HTTPException(status_code=422, detail=f"Invalid plan_type: {request.get('plan_type')}. Must be one of {list(valid_plan_types)}")
        
        # Verify payment signature
        payment_id = str(request.get('payment_id') or '')
        subscription_id = str(request.get('subscription_id') or '')
        signature = str(request.get('signature') or '')
        logger.info(f"Verifying payment: payment_id={payment_id}, subscription_id={subscription_id}, signature={signature}")
        payment_verified = PricingService.verify_subscription_payment(payment_id, subscription_id, signature)
        logger.info(f"Payment verification result: {payment_verified}")
        if not payment_verified:
            logger.error("Payment verification failed!")
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        # Create subscription in database
        plan_enum = PlanType(request.get('plan_type'))
        logger.info(f"Creating subscription for user_id={user.id}, plan_type={plan_enum}, subscription_id={subscription_id}")
        
        # For now, use default period (you'd get this from Razorpay response)
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)  # 30 days subscription
        
        subscription = PricingService.create_user_subscription(
            db=db,
            user_id=int(getattr(user, 'id')),
            plan_type=plan_enum,
            subscription_id=subscription_id,
            customer_id="customer_id",  # You'd get this from Razorpay
            period_start=period_start,
            period_end=period_end
        )
        logger.info(f"Subscription created: {subscription}")
        
        return {"message": "Subscription verified and activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[DEBUG] Exception in /pricing/verify-subscription: {e}\n{tb}")
        logger.error(f"Error verifying subscription: {str(e)}\nTraceback: {tb}")
        # Return the traceback in the response for debugging (remove in production!)
        raise HTTPException(status_code=500, detail=f"{str(e)}\nTraceback:\n{tb}")

@app.get("/pricing/subscription")
async def get_subscription_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get user's current subscription status"""
    try:
        # Get current user
        user = get_current_user(db, credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        subscription = PricingService.get_user_subscription(db, int(getattr(user, 'id')))
        
        if not subscription:
            return {
                "has_subscription": False,
                "plan_type": "free",
                "message": "No active subscription"
            }
        
        # Calculate days remaining
        days_remaining = max(0, (getattr(subscription, 'current_period_end') - datetime.utcnow()).days)
        
        return {
            "has_subscription": True,
            "plan_type": getattr(subscription, 'plan_type'),
            "status": getattr(subscription, 'status'),
            "current_period_start": getattr(subscription, 'current_period_start').isoformat(),
            "current_period_end": getattr(subscription, 'current_period_end').isoformat(),
            "cancel_at_period_end": getattr(subscription, 'cancel_at_period_end'),
            "days_remaining": days_remaining,
            "message": f"Active {getattr(subscription, 'plan_type')} subscription"
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pricing/cancel-subscription")
async def cancel_subscription(
    request: CancelSubscriptionRequest = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Cancel user subscription"""
    try:
        # Get current user
        user = get_current_user(db, credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        success = PricingService.cancel_subscription(
            db=db,
            user_id=int(getattr(user, 'id')),
            cancel_at_period_end=request.cancel_at_period_end
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        message = "Subscription cancelled" if not request.cancel_at_period_end else "Subscription will be cancelled at the end of the current period"
        
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pricing/user-quota")
async def get_user_quota(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_current_user(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    quota = PricingService.get_user_quota(db, int(getattr(user, 'id')))
    return quota

@app.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Razorpay webhooks for subscription events"""
    try:
        # Get the raw body
        body = await request.body()
        signature = request.headers.get("x-razorpay-signature")
        
        if not signature:
            logger.error("No signature found in webhook")
            raise HTTPException(status_code=400, detail="No signature")
        
        # Verify webhook signature
        try:
            if not razorpay_utility:
                raise Exception("Razorpay utility not initialized")
            razorpay_utility.verify_webhook_signature(body.decode(), signature, os.getenv("RAZORPAY_WEBHOOK_SECRET", ""))
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse the webhook data
        webhook_data = json.loads(body.decode())
        event = webhook_data.get("event")
        payload = webhook_data.get("payload", {})
        
        logger.info(f"Received Razorpay webhook: {event}")
        
        if event == "subscription.activated":
            # Handle subscription activation
            subscription_data = payload.get("subscription", {})
            subscription_id = subscription_data.get("id")
            customer_id = subscription_data.get("customer_id")
            plan_id = subscription_data.get("plan_id")
            
            # Find user by customer_id
            user = db.query(User).filter(User.razorpay_customer_id == customer_id).first()
            if not user:
                logger.error(f"No user found for customer_id: {customer_id}")
                return {"status": "error", "message": "User not found"}
            
            # Determine plan type based on plan_id
            plan_type = None
            if plan_id == os.getenv("RAZORPAY_STARTER_PLAN_ID"):
                plan_type = PlanType.STARTER
            elif plan_id == os.getenv("RAZORPAY_UNLIMITED_PLAN_ID"):
                plan_type = PlanType.UNLIMITED
            elif plan_id in [os.getenv("RAZORPAY_LAUNCH50_STARTER_PLAN_ID"), os.getenv("RAZORPAY_LAUNCH50_UNLIMITED_PLAN_ID")]:
                # For discounted plans, use the base plan type
                if plan_id == os.getenv("RAZORPAY_LAUNCH50_STARTER_PLAN_ID"):
                    plan_type = PlanType.STARTER
                else:
                    plan_type = PlanType.UNLIMITED
            elif plan_id in [os.getenv("RAZORPAY_WELCOME20_STARTER_PLAN_ID"), os.getenv("RAZORPAY_WELCOME20_UNLIMITED_PLAN_ID")]:
                # For discounted plans, use the base plan type
                if plan_id == os.getenv("RAZORPAY_WELCOME20_STARTER_PLAN_ID"):
                    plan_type = PlanType.STARTER
                else:
                    plan_type = PlanType.UNLIMITED
            
            if not plan_type:
                logger.error(f"Unknown plan_id: {plan_id}")
                return {"status": "error", "message": "Unknown plan"}
            
            # Create or update subscription
            period_start = datetime.fromtimestamp(subscription_data.get("current_start", 0))
            period_end = datetime.fromtimestamp(subscription_data.get("current_end", 0))
            
            PricingService.create_user_subscription(
                db, getattr(user, 'id'), plan_type, subscription_id, customer_id, period_start, period_end
            )
            
            logger.info(f"Subscription activated for user {user.id}: {plan_type}")
            
        elif event == "subscription.charged":
            # Handle successful payment
            subscription_data = payload.get("subscription", {})
            subscription_id = subscription_data.get("id")
            plan_id = subscription_data.get("plan_id")
            
            # Handle renewal and plan transitions
            PricingService.handle_subscription_renewal(db, subscription_id, plan_id)
            
            # Update subscription period
            subscription = db.query(Subscription).filter(
                Subscription.razorpay_subscription_id == subscription_id
            ).first()
            
            if subscription:
                period_start = datetime.fromtimestamp(subscription_data.get("current_start", 0))
                period_end = datetime.fromtimestamp(subscription_data.get("current_end", 0))
                
                setattr(subscription, 'current_period_start', period_start)
                setattr(subscription, 'current_period_end', period_end)
                setattr(subscription, 'status', SubscriptionStatus.ACTIVE)
                setattr(subscription, 'updated_at', datetime.utcnow())
                
                db.commit()
                logger.info(f"Subscription charged and renewed: {subscription_id}")
            
        elif event == "subscription.halted":
            # Handle subscription halt (payment failed)
            subscription_data = payload.get("subscription", {})
            subscription_id = subscription_data.get("id")
            
            subscription = db.query(Subscription).filter(
                Subscription.razorpay_subscription_id == subscription_id
            ).first()
            
            if subscription:
                setattr(subscription, 'status', SubscriptionStatus.EXPIRED)
                setattr(subscription, 'updated_at', datetime.utcnow())
                db.commit()
                logger.info(f"Subscription halted: {subscription_id}")
            
        elif event == "subscription.cancelled":
            # Handle subscription cancellation
            subscription_data = payload.get("subscription", {})
            subscription_id = subscription_data.get("id")
            
            subscription = db.query(Subscription).filter(
                Subscription.razorpay_subscription_id == subscription_id
            ).first()
            
            if subscription:
                setattr(subscription, 'status', SubscriptionStatus.CANCELLED)
                setattr(subscription, 'updated_at', datetime.utcnow())
                db.commit()
                logger.info(f"Subscription cancelled: {subscription_id}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 