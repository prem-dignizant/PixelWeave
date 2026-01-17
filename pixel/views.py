from rest_framework import status
from rest_framework.views import APIView
from pixelweave_app.utils import wrap_response
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from .models import Wardrobe, Studio
from .serializers import WardrobeSerializer, WardrobeCreateSerializer, StudioSerializer, StudioCreateSerializer
from .service import generate_fashion_image
import os
import tempfile
from django.conf import settings
from .tasks import generate_wardrobe_image_task, generate_studio_mockup_task


class WardrobeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a wardrobe image from uploaded clothing image and background color.
        
        Expected payload:
        - input_image: Image file (multipart/form-data)
        - bg_color: Background color (optional, default: 'white')
        """
        if request.user.credit < 1:
            return wrap_response(success=False, code="insufficient_credits", 
                               message="You need at least 2 credits to generate a wardrobe image")
        
        serializer = WardrobeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(success=False, code="invalid_data", message=serializer.errors)
        
        input_image = serializer.validated_data['input_image']
        bg_color = serializer.validated_data.get('bg_color')
        
        # Save the uploaded image temporarily so the Celery task can access it
        # Note: In a production environment with distributed workers, you should upload 
        # this to shared storage (e.g., S3) or save it to a model field instead of a local temp file.
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_input:
            for chunk in input_image.chunks():
                temp_input.write(chunk)
            temp_input_path = temp_input.name
        
        try:
            # Create Wardrobe instance with keys set to PENDING
            wardrobe = Wardrobe.objects.create(
                user=request.user,
                bg_color=bg_color,
                status='PENDING'
            )
            
            # Queue the background task
            generate_wardrobe_image_task.delay(wardrobe.id, temp_input_path, bg_color)
            
            # Serialize and return the response immediately
            response_serializer = WardrobeSerializer(wardrobe)
            return wrap_response(success=True, code="wardrobe_processing_started", data=response_serializer.data)
        
        except Exception as e:
            # Clean up if something fails before queuing
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            return wrap_response(success=False, code="failed_to_queue_task", message=str(e))

    def get(self, request):
        """
        Get all wardrobe images for the authenticated user.
        """
        wardrobes = Wardrobe.objects.filter(user=request.user).order_by('-created')
        serializer = WardrobeSerializer(wardrobes, many=True)
        return wrap_response(success=True, code="wardrobe_list", data=serializer.data)


class MockupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a studio mockup from uploaded clothing image or wardrobe reference.
        
        Expected payload:
        - input_image: Image file (optional, multipart/form-data)
        - wardrobe_id: ID of existing wardrobe (optional)
        - garment_type: Type of garment (required)
        - image_size: Size of output image (required)
        - gender: Model gender (required)
        - background: Background parameters (optional)
        - model: Model parameters (optional)
        - extra: Extra parameters (optional)
        """
        if request.user.credit < 2:
            return wrap_response(success=False, code="insufficient_credits", 
                               message="You need at least 2 credits to generate a wardrobe image")

        serializer = StudioCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(success=False, code="invalid_data", message=serializer.errors)
        
        # Extract validated data
        input_image = serializer.validated_data.get('input_image')
        wardrobe_id = serializer.validated_data.get('wardrobe_id')
        garment_type = serializer.validated_data['garment_type']
        image_size = serializer.validated_data['image_size']
        # gender = serializer.validated_data['gender']
        background_params = serializer.validated_data.get('background', {})
        model_params = serializer.validated_data.get('model', {})
        extra_params = serializer.validated_data.get('extra', {})
        
        # Build parameters dictionary for the service
        parameters = {
            "garment_type": garment_type,
            "image_size": image_size,
            "background": background_params,
            "model": {
                **model_params
            },
            "extra": extra_params
        }
        
        # Determine input image path
        wardrobe_instance = None
        if wardrobe_id:
            # Use image from existing wardrobe
            try:
                wardrobe_instance = Wardrobe.objects.get(id=wardrobe_id, user=request.user)
                if not wardrobe_instance.image:
                    return wrap_response(success=False, code="no_wardrobe_image", 
                                       message="Selected wardrobe has no image")
                temp_input_path = wardrobe_instance.image.path
            except Wardrobe.DoesNotExist:
                return wrap_response(success=False, code="wardrobe_not_found", 
                                   message="Wardrobe not found or access denied")
        else:
            # Save uploaded image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_input:
                for chunk in input_image.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name
        
        try:
            # Create Studio instance with PENDING status
            studio = Studio.objects.create(
                user=request.user,
                wardrobe=wardrobe_instance,
                status='PENDING'
            )
            
            # Save the input image to studio.image if uploaded directly
            if input_image:
                with open(temp_input_path, 'rb') as f:
                    studio.image.save(
                        f'studio_input_{studio.id}.jpg',
                        ContentFile(f.read()),
                        save=True
                    )
            
            # Queue the background task
            generate_studio_mockup_task.delay(studio.id, temp_input_path, parameters)
            
            # Serialize and return the response immediately
            response_serializer = StudioSerializer(studio)
            return wrap_response(success=True, code="studio_mockup_processing_started", 
                               data=response_serializer.data)
        
        except Exception as e:
            # Clean up temp file if it was created and something fails
            if input_image and os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            return wrap_response(success=False, code="failed_to_queue_task", message=str(e))

    def get(self, request):
        """
        Get all studio mockups for the authenticated user.
        """
        studios = Studio.objects.filter(user=request.user).order_by('-created')
        serializer = StudioSerializer(studios, many=True)
        return wrap_response(success=True, code="studio_list", data=serializer.data)
