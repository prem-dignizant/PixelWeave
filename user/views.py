from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    CreateCheckoutSessionSerializer, PaymentSerializer
)
from .models import Payment, User
from pixelweave_app.utils import wrap_response
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import stripe
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class HealthCheck(APIView):
    def get(self, request):
        return wrap_response(True, "service_running")

class RegisterAPIView(APIView):
    """
    API view for user registration
    POST: Register a new user and return JWT tokens
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            return wrap_response(success=True, code="user_registered", data={
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        
        return wrap_response(success=False, code="invalid_data", message=serializer.errors)


class LoginAPIView(APIView):
    """
    API view for user login
    POST: Authenticate user and return JWT tokens
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            return wrap_response(success=True, code="login_successful", data={
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        
        return wrap_response(success=False, code="invalid_data", message=serializer.errors)


class UserProfileAPIView(APIView):
    """
    API view to get authenticated user profile
    GET: Return current user details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return wrap_response(success=True, code="user_profile", data=serializer.data)


class CreateCheckoutSessionAPIView(APIView):
    """Create Stripe checkout session for credit purchase"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return wrap_response(success=False, code="invalid_data", message=serializer.errors)
        
        amount_dollars = int(serializer.validated_data['amount'])
        amount_cents = int(amount_dollars * 100)
        credits = int(amount_dollars * settings.CREDIT_PER_DOLLAR)
        
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': amount_cents,
                        'product_data': {
                            'name': f'{credits} Credits',
                            'description': f'Purchase {credits} credits for PixelWeave',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                # success_url=request.build_absolute_uri('/payment/success/'),
                # cancel_url=request.build_absolute_uri('/payment/cancel/'),
                success_url=request.META.get('HTTP_ORIGIN','http://localhost:3000') + '/subscriptions/success',
                cancel_url=request.META.get('HTTP_ORIGIN','http://localhost:3000') + '/subscriptions/failure',
                client_reference_id=str(request.user.user_id),
                metadata={
                    'user_id': str(request.user.user_id),
                    'credits': credits,
                }
            )
            
            # Create Payment record
            payment = Payment.objects.create(
                user=request.user,
                stripe_session_id=checkout_session.id,
                amount=amount_dollars,
                credits=credits,
                status='PENDING'
            )
            
            return wrap_response(success=True, code="checkout_session_created", data={
                'session_id': checkout_session.id,
                'session_url': checkout_session.url,
                'payment': PaymentSerializer(payment).data
            })
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return wrap_response(success=False, code="checkout_creation_failed", message=str(e))


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhook events"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return Response({'error': 'Invalid signature'}, status=400)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_completed(session)
        
        return Response({'status': 'success'}, status=200)
    
    def handle_checkout_completed(self, session):
        """Handle successful payment completion"""
        try:
            payment = Payment.objects.get(stripe_session_id=session['id'])
            
            if payment.status == 'COMPLETED':
                logger.info(f"Payment {payment.id} already processed")
                return
            
            # Update payment status
            payment.status = 'COMPLETED'
            payment.save()
            
            # Add credits to user
            user = payment.user
            user.credit += payment.credits
            user.save()
            
            logger.info(f"Added {payment.credits} credits to user {user.user_name}")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for session {session['id']}")
        except Exception as e:
            logger.error(f"Error processing payment completion: {str(e)}")
