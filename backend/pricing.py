import os
import razorpay
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from models import PlanType, PricingPlan, CouponValidation, UserQuota, SubscriptionStatus, Subscription, User, UserHistory
from dotenv import load_dotenv
from uuid import uuid4
from sqlalchemy.orm import Session

load_dotenv()

# Initialize Razorpay client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    # Attach submodules for linter clarity
    razorpay_plan = razorpay.Plan(razorpay_client)
    razorpay_customer = razorpay.Customer(razorpay_client)
    razorpay_subscription = razorpay.Subscription(razorpay_client)
    razorpay_utility = razorpay.Utility(razorpay_client)
else:
    razorpay_client = None
    razorpay_plan = None
    razorpay_customer = None
    razorpay_subscription = None
    razorpay_utility = None
    print("⚠️ Razorpay credentials not found. Payment features will be disabled.")

# Pricing Plans
PRICING_PLANS = {
    PlanType.FREE: PricingPlan(
        id="free",
        name="Free Plan",
        price=0,
        pdf_limit=3,
        features=[
            "3 PDFs total (lifetime)",
            "Basic summaries",
            "No login required"
        ],
        popular=False
    ),
    PlanType.STARTER: PricingPlan(
        id="starter",
        name="Starter Plan",
        price=4900,  # ₹49 in paise
        pdf_limit=15,
        features=[
            "15 PDFs per month",
            "Advanced AI summaries",
            "Quiz generation",
            "Download study packs",
            "User history"
        ],
        popular=True
    ),
    PlanType.UNLIMITED: PricingPlan(
        id="unlimited",
        name="Unlimited Plan",
        price=19900,  # ₹199 in paise
        pdf_limit=None,  # Unlimited
        features=[
            "Unlimited PDFs",
            "Advanced AI summaries",
            "Quiz generation",
            "Download study packs",
            "User history",
            "Priority support"
        ],
        popular=False
    )
}

# Valid Coupons
VALID_COUPONS = {
    "SASMIT26NARNAWARE": {
        "amount_off": 19900,  # 100% off (₹199)
        "uses_left": None,
        "email_lock": "sasmit26narnaware@gmail.com"
    },
    "LAUNCH50": {
        "percent_off": 50,  # 50% off
        "uses_left": 100
    },
    "WELCOME20": {
        "percent_off": 20,  # 20% off
        "uses_left": 50
    }
}

# In-memory storage for user quotas (replace with database in production)
user_quotas: Dict[int, Dict] = {}

class PricingService:
    @staticmethod
    def get_pricing_plans() -> Dict[PlanType, PricingPlan]:
        """Get all available pricing plans"""
        return PRICING_PLANS
    
    @staticmethod
    def validate_coupon(coupon_code: str, user_email: Optional[str] = None) -> CouponValidation:
        """Validate a coupon code"""
        print(f"[DEBUG] validate_coupon called with coupon_code={coupon_code}, user_email={user_email}")
        if not coupon_code:
            return CouponValidation(valid=False, message="No coupon code provided")
        
        coupon_code = coupon_code.upper()
        
        if coupon_code not in VALID_COUPONS:
            return CouponValidation(valid=False, message="Invalid coupon code")
        
        coupon = VALID_COUPONS[coupon_code]
        
        # Check email lock
        if "email_lock" in coupon and coupon["email_lock"]:
            if not user_email or user_email.lower() != coupon["email_lock"].lower():
                return CouponValidation(valid=False, message="This coupon is not valid for your email")
        
        # Check usage limit
        if "uses_left" in coupon and coupon["uses_left"] is not None:
            if coupon["uses_left"] <= 0:
                return CouponValidation(valid=False, message="This coupon has been used up")
        
        # Compose message
        if "amount_off" in coupon:
            msg = "100% off! This month is free!"
        elif "percent_off" in coupon:
            msg = f"{coupon['percent_off']}% off this month!"
        else:
            msg = "Discount applied!"
        return CouponValidation(
            valid=True,
            discount_amount=coupon.get("amount_off", 0),
            message=msg
        )
    
    @staticmethod
    def calculate_final_price(plan_type: PlanType, coupon_code: Optional[str] = None, user_email: Optional[str] = None) -> Tuple[int, int, str]:
        """Calculate final price after applying coupon"""
        plan = PRICING_PLANS[plan_type]
        original_price = plan.price
        discount_amount = 0
        message = ""
        
        if coupon_code:
            coupon_code_upper = coupon_code.upper()
            coupon = VALID_COUPONS.get(coupon_code_upper)
            if coupon:
                # Email lock
                if "email_lock" in coupon and coupon["email_lock"]:
                    if not user_email or user_email.lower() != coupon["email_lock"].lower():
                        return original_price, 0, "This coupon is not valid for your email"
                # Usage limit
                if "uses_left" in coupon and coupon["uses_left"] is not None:
                    if coupon["uses_left"] <= 0:
                        return original_price, 0, "This coupon has been used up"
                if "amount_off" in coupon:
                    discount_amount = min(original_price, coupon["amount_off"])
                    message = "100% off! This month is free!"
                elif "percent_off" in coupon:
                    discount_amount = (original_price * coupon["percent_off"]) // 100
                    message = f"{coupon['percent_off']}% off this month!"
                else:
                    discount_amount = 0
                    message = "Discount applied!"
            else:
                message = "Invalid coupon code"
        
        final_price = max(0, original_price - discount_amount)
        return final_price, discount_amount, message
    
    @staticmethod
    def create_razorpay_subscription(plan_type: PlanType, user_email: str, coupon_code: Optional[str] = None) -> Dict:
        """Create a Razorpay subscription for recurring payments"""
        if not razorpay_client:
            raise Exception("Razorpay is not configured")
        if plan_type == PlanType.FREE:
            raise Exception("Cannot create subscription for free plan")

        # Step 1: Lifetime free for SASMIT26NARNAWARE
        if coupon_code and coupon_code.upper() == "SASMIT26NARNAWARE" and user_email.lower() == "sasmit26narnaware@gmail.com":
            print("[DEBUG] Activating lifetime free subscription for user via coupon SASMIT26NARNAWARE")
            return {
                "is_free": True,
                "message": "Lifetime free plan activated!",
                "final_price": 0,
                "discount_amount": PRICING_PLANS[plan_type].price,
                "original_price": PRICING_PLANS[plan_type].price
            }

        # Step 2: Special plan IDs for LAUNCH50 and WELCOME20 with expiry logic
        now = datetime.utcnow()
        launch_date = datetime(2025, 6, 29)  # Set your launch date here
        # LAUNCH50: valid for 5 days after launch
        if coupon_code and coupon_code.upper() == "LAUNCH50" and (now - launch_date).days < 5:
            print(f"[DEBUG] Using LAUNCH50 plan for {plan_type}")
            if plan_type == PlanType.STARTER:
                plan_id = os.getenv("RAZORPAY_LAUNCH50_STARTER_PLAN_ID")
            else:
                plan_id = os.getenv("RAZORPAY_LAUNCH50_UNLIMITED_PLAN_ID")
            if not plan_id:
                raise Exception("LAUNCH50 plan ID not set in .env")
            # Continue with discounted plan
            final_price = PRICING_PLANS[plan_type].price // 2
            message = "50% off for your first month!"
            # Create customer and subscription as usual
            customer_data = {"name": "SnapReads User", "email": user_email}
            if not razorpay_customer:
                raise Exception("Razorpay customer module not initialized")
            try:
                customer = razorpay_customer.create(data=customer_data)
            except Exception as e:
                if "Customer already exists" in str(e):
                    print(f"[Razorpay] Customer already exists, fetching existing customer for email: {user_email}")
                    customers = razorpay_customer.all({'email': user_email})
                    if customers['count'] > 0:
                        customer = customers['items'][0]
                    else:
                        print(f"[Razorpay] No customer found for email: {user_email}")
                        raise Exception("Failed to fetch existing Razorpay customer")
                else:
                    print(f"[Razorpay] Error creating customer: {e}")
                    raise Exception("Failed to create Razorpay customer")
            subscription_data = {
                "plan_id": plan_id,
                "customer_notify": 1,
                "total_count": 1,  # 1 month only
                "customer_id": customer["id"]
            }
            if not razorpay_subscription:
                raise Exception("Razorpay subscription module not initialized")
            try:
                subscription = razorpay_subscription.create(data=subscription_data)
            except Exception as e:
                print(f"[Razorpay] Error creating subscription: {e}")
                raise Exception("Failed to create Razorpay subscription")
            return {
                "subscription_id": subscription["id"],
                "customer_id": customer["id"],
                "plan_id": plan_id,
                "key": RAZORPAY_KEY_ID,
                "prefill": {"email": user_email, "name": "SnapReads User"},
                "message": message,
                "final_price": final_price,
                "discount_amount": PRICING_PLANS[plan_type].price - final_price,
                "original_price": PRICING_PLANS[plan_type].price
            }
        # WELCOME20: valid for 30 days after launch
        if coupon_code and coupon_code.upper() == "WELCOME20" and (now - launch_date).days < 30:
            print(f"[DEBUG] Using WELCOME20 plan for {plan_type}")
            if plan_type == PlanType.STARTER:
                plan_id = os.getenv("RAZORPAY_WELCOME20_STARTER_PLAN_ID")
            else:
                plan_id = os.getenv("RAZORPAY_WELCOME20_UNLIMITED_PLAN_ID")
            if not plan_id:
                raise Exception("WELCOME20 plan ID not set in .env")
            # Continue with discounted plan
            final_price = PRICING_PLANS[plan_type].price * 80 // 100
            message = "20% off for your first month!"
            # Create customer and subscription as usual
            customer_data = {"name": "SnapReads User", "email": user_email}
            if not razorpay_customer:
                raise Exception("Razorpay customer module not initialized")
            try:
                customer = razorpay_customer.create(data=customer_data)
            except Exception as e:
                if "Customer already exists" in str(e):
                    print(f"[Razorpay] Customer already exists, fetching existing customer for email: {user_email}")
                    customers = razorpay_customer.all({'email': user_email})
                    if customers['count'] > 0:
                        customer = customers['items'][0]
                    else:
                        print(f"[Razorpay] No customer found for email: {user_email}")
                        raise Exception("Failed to fetch existing Razorpay customer")
                else:
                    print(f"[Razorpay] Error creating customer: {e}")
                    raise Exception("Failed to create Razorpay customer")
            subscription_data = {
                "plan_id": plan_id,
                "customer_notify": 1,
                "total_count": 1,  # 1 month only
                "customer_id": customer["id"]
            }
            if not razorpay_subscription:
                raise Exception("Razorpay subscription module not initialized")
            try:
                subscription = razorpay_subscription.create(data=subscription_data)
            except Exception as e:
                print(f"[Razorpay] Error creating subscription: {e}")
                raise Exception("Failed to create Razorpay subscription")
            return {
                "subscription_id": subscription["id"],
                "customer_id": customer["id"],
                "plan_id": plan_id,
                "key": RAZORPAY_KEY_ID,
                "prefill": {"email": user_email, "name": "SnapReads User"},
                "message": message,
                "final_price": final_price,
                "discount_amount": PRICING_PLANS[plan_type].price - final_price,
                "original_price": PRICING_PLANS[plan_type].price
            }

        final_price, discount_amount, message = PricingService.calculate_final_price(plan_type, coupon_code, user_email)
        print(f"[Razorpay] Creating subscription: plan_type={plan_type}, original_price={PRICING_PLANS[plan_type].price}, discount={discount_amount}, final_price={final_price}")
        if final_price <= 0:
            raise Exception("Final price must be greater than zero for paid plans")

        # --- PLAN CACHE (avoid duplicate plans) ---
        plan_cache = {
            PlanType.STARTER: os.getenv("RAZORPAY_STARTER_PLAN_ID"),
            PlanType.UNLIMITED: os.getenv("RAZORPAY_UNLIMITED_PLAN_ID")
        }
        plan_id = plan_cache.get(plan_type)
        if not plan_id:
            # Create a Razorpay plan if not cached
            plan_data = {
                "period": "monthly",
                "interval": 1,
                "item": {
                    "name": PRICING_PLANS[plan_type].name,
                    "amount": final_price,
                    "currency": "INR",
                    "description": f"{PRICING_PLANS[plan_type].name} Subscription"
                }
            }
            if not razorpay_plan:
                raise Exception("Razorpay plan module not initialized")
            try:
                plan = razorpay_plan.create(data=plan_data)
                plan_id = plan["id"]
            except Exception as e:
                print(f"[Razorpay] Error creating plan: {e}")
                raise Exception("Failed to create Razorpay plan")
        # --- END PLAN CACHE ---

        # Create a customer (reuse if already exists)
        customer_data = {
            "name": "SnapReads User",
            "email": user_email
        }
        if not razorpay_customer:
            raise Exception("Razorpay customer module not initialized")
        try:
            customer = razorpay_customer.create(data=customer_data)
        except Exception as e:
            # If customer already exists, fetch the existing customer
            if "Customer already exists" in str(e):
                print(f"[Razorpay] Customer already exists, fetching existing customer for email: {user_email}")
                customers = razorpay_customer.all({'email': user_email})
                if customers['count'] > 0:
                    customer = customers['items'][0]
                else:
                    print(f"[Razorpay] No customer found for email: {user_email}")
                    raise Exception("Failed to fetch existing Razorpay customer")
            else:
                print(f"[Razorpay] Error creating customer: {e}")
                raise Exception("Failed to create Razorpay customer")

        # Create a subscription
        subscription_data = {
            "plan_id": plan_id,
            "customer_notify": 1,
            "total_count": 12,  # 12 months
            "customer_id": customer["id"]
        }
        if not razorpay_subscription:
            raise Exception("Razorpay subscription module not initialized")
        try:
            subscription = razorpay_subscription.create(data=subscription_data)
        except Exception as e:
            print(f"[Razorpay] Error creating subscription: {e}")
            raise Exception("Failed to create Razorpay subscription")

        return {
            "subscription_id": subscription["id"],
            "customer_id": customer["id"],
            "plan_id": plan_id,
            "key": RAZORPAY_KEY_ID,
            "prefill": {
                "email": user_email,
                "name": "SnapReads User"
            },
            "message": message,
            "final_price": final_price,
            "discount_amount": discount_amount,
            "original_price": PRICING_PLANS[plan_type].price
        }
    
    @staticmethod
    def get_user_subscription(db: Session, user_id: int) -> Optional[Subscription]:
        """Get user's current subscription"""
        return db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING])
        ).first()
    
    @staticmethod
    def create_user_subscription(db: Session, user_id: int, plan_type: PlanType, 
                               subscription_id: str, customer_id: str, 
                               period_start: datetime, period_end: datetime) -> Subscription:
        """Create a new subscription for user"""
        # Cancel any existing subscription
        existing = PricingService.get_user_subscription(db, user_id)
        if existing:
            setattr(existing, 'status', SubscriptionStatus.CANCELLED)
            setattr(existing, 'updated_at', datetime.utcnow())
        
        # Update user's Razorpay customer ID
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            setattr(user, 'razorpay_customer_id', customer_id)
        
        # Create new subscription
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
            razorpay_subscription_id=subscription_id,
            razorpay_customer_id=customer_id,
            current_period_start=period_start,
            current_period_end=period_end,
            cancel_at_period_end=False
        )
        
        db.add(subscription)
        db.commit()
        return subscription
    
    @staticmethod
    def cancel_subscription(db: Session, user_id: int, cancel_at_period_end: bool = True) -> bool:
        """Cancel user subscription"""
        subscription = PricingService.get_user_subscription(db, user_id)
        if not subscription:
            return False
        
        if cancel_at_period_end:
            setattr(subscription, 'cancel_at_period_end', True)
            setattr(subscription, 'status', SubscriptionStatus.ACTIVE)  # Still active until period ends
        else:
            setattr(subscription, 'status', SubscriptionStatus.CANCELLED)
        
        setattr(subscription, 'updated_at', datetime.utcnow())
        db.commit()
        return True
    
    @staticmethod
    def get_user_quota(db: Session, user_id: int, user_email: Optional[str] = None) -> UserQuota:
        """Get user's current quota based on subscription"""
        subscription = PricingService.get_user_subscription(db, user_id)
        
        if subscription and getattr(subscription, 'status') == SubscriptionStatus.ACTIVE:
            # Check if subscription is still valid
            if datetime.utcnow() > getattr(subscription, 'current_period_end'):
                # Subscription expired, update status
                setattr(subscription, 'status', SubscriptionStatus.EXPIRED)
                db.commit()
                subscription = None
        
        if subscription and getattr(subscription, 'status') == SubscriptionStatus.ACTIVE:
            plan_type = PlanType(getattr(subscription, 'plan_type'))
            plan = PRICING_PLANS[plan_type]
            pdf_limit = plan.pdf_limit

            if plan_type == PlanType.STARTER:
                # Count PDFs processed in current billing period
                period_start = getattr(subscription, 'current_period_start')
                period_end = getattr(subscription, 'current_period_end')
                pdfs_used = db.query(UserHistory).filter(
                    UserHistory.user_id == user_id,
                    UserHistory.created_at >= period_start,
                    UserHistory.created_at < period_end
                ).count()
                if pdf_limit is not None:
                    can_process = pdfs_used < pdf_limit
                    message = f"Starter Plan: {pdfs_used}/{pdf_limit} PDFs used this month"
                else:
                    can_process = True
                    message = f"Starter Plan: {pdfs_used} PDFs used this month (unlimited)"
            else:
                # Unlimited plan
                pdfs_used = 0
                can_process = True
                message = f"Active {plan.name} subscription"

            if getattr(subscription, 'cancel_at_period_end'):
                days_remaining = (getattr(subscription, 'current_period_end') - datetime.utcnow()).days
                message += f" (cancels in {days_remaining} days)"

            return UserQuota(
                plan_type=plan_type,
                pdfs_used=pdfs_used,
                pdf_limit=pdf_limit,
                can_process=can_process,
                message=message
            )
        else:
            # No active subscription - free plan
            pdfs_used = db.query(UserHistory).filter(UserHistory.user_id == user_id).count()
            can_process = pdfs_used < 3
            message = "Free plan - 3 PDFs total" if can_process else "You have used all 3 free PDFs. Please upgrade to continue."
            return UserQuota(
                plan_type=PlanType.FREE,
                pdfs_used=pdfs_used,
                pdf_limit=3,
                can_process=can_process,
                message=message
            )
    
    @staticmethod
    def increment_user_usage(user_id: int) -> bool:
        """Increment user's PDF usage count (for free plan)"""
        # This is a simplified version for free plan usage tracking
        # In production, you'd track this in the database
        if user_id not in user_quotas:
            user_quotas[user_id] = {
                "plan_type": PlanType.FREE,
                "pdfs_used": 0,
                "pdf_limit": 3
            }
        
        quota_data = user_quotas[user_id]
        pdf_limit = quota_data.get("pdf_limit")
        
        # Check if user can process more PDFs
        if pdf_limit is not None and quota_data["pdfs_used"] >= pdf_limit:
            return False
        
        quota_data["pdfs_used"] += 1
        return True
    
    @staticmethod
    def verify_subscription_payment(payment_id: str, subscription_id: str, signature: str) -> bool:
        """Verify subscription payment signature"""
        if not razorpay_client:
            print("[Razorpay] Client not initialized")
            return False
        if not razorpay_utility:
            print("[Razorpay] Utility module not initialized")
            return False
        try:
            print(f"[DEBUG] Verifying payment: payment_id={payment_id}, subscription_id={subscription_id}, signature={signature}")
            params_dict = {
                'razorpay_subscription_id': subscription_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            print(f"[DEBUG] Params dict for signature verification: {params_dict}")
            razorpay_utility.verify_subscription_payment_signature(params_dict)
            print("[DEBUG] Signature verification succeeded")
            return True
        except Exception as e:
            print(f"[Razorpay] Signature verification failed: {e}")
            return False
    
    @staticmethod
    def handle_subscription_renewal(db: Session, subscription_id: str, plan_id: str) -> bool:
        """Handle subscription renewal and transition from discounted to regular plans"""
        try:
            subscription = db.query(Subscription).filter(
                Subscription.razorpay_subscription_id == subscription_id
            ).first()
            
            if not subscription:
                print(f"[DEBUG] No subscription found for ID: {subscription_id}")
                return False
            
            # Check if this is a discounted plan that needs to transition to regular plan
            current_plan_id = plan_id
            is_discounted_plan = (
                current_plan_id in [
                    os.getenv("RAZORPAY_LAUNCH50_STARTER_PLAN_ID"),
                    os.getenv("RAZORPAY_LAUNCH50_UNLIMITED_PLAN_ID"),
                    os.getenv("RAZORPAY_WELCOME20_STARTER_PLAN_ID"),
                    os.getenv("RAZORPAY_WELCOME20_UNLIMITED_PLAN_ID")
                ]
            )
            
            if is_discounted_plan:
                print(f"[DEBUG] Detected discounted plan renewal: {current_plan_id}")
                # Determine the regular plan to transition to
                if current_plan_id in [
                    os.getenv("RAZORPAY_LAUNCH50_STARTER_PLAN_ID"),
                    os.getenv("RAZORPAY_WELCOME20_STARTER_PLAN_ID")
                ]:
                    # Transition to regular starter plan
                    new_plan_id = os.getenv("RAZORPAY_STARTER_PLAN_ID")
                    new_plan_type = PlanType.STARTER
                else:
                    # Transition to regular unlimited plan
                    new_plan_id = os.getenv("RAZORPAY_UNLIMITED_PLAN_ID")
                    new_plan_type = PlanType.UNLIMITED
                
                print(f"[DEBUG] Transitioning from {current_plan_id} to {new_plan_id}")
                
                # Update the subscription in our database
                setattr(subscription, 'plan_type', new_plan_type.value)
                setattr(subscription, 'updated_at', datetime.utcnow())
                db.commit()
                
                print(f"[DEBUG] Successfully transitioned subscription {subscription_id} to {new_plan_type}")
                return True
            else:
                print(f"[DEBUG] Regular plan renewal, no transition needed: {current_plan_id}")
                return True
                
        except Exception as e:
            print(f"[ERROR] Failed to handle subscription renewal: {e}")
            return False 