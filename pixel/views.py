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
from django.db.models import F
from user.models import User


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
        
        # Save the uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_input:
            for chunk in input_image.chunks():
                temp_input.write(chunk)
            temp_input_path = temp_input.name
        
        # Output path
        temp_output_path = temp_input_path.replace('.jpg', '_output.png')
        
        try:
            # Generate image synchronously
            params = {'bg_color': bg_color}
            generated_image_path = generate_fashion_image(
                type='wardrobe',
                input_image_path=temp_input_path,
                params=params,
                output_path=temp_output_path
            )

            if not generated_image_path:
                raise Exception("Failed to generate wardrobe image")

            # Create Wardrobe instance
            wardrobe = Wardrobe.objects.create(
                user=request.user,
                bg_color=bg_color,
                status='COMPLETED'
            )
            
            # Save images
            with open(temp_input_path, 'rb') as f:
                wardrobe.image.save(f'wardrobe_input_{wardrobe.id}.jpg', ContentFile(f.read()), save=False)
            
            with open(temp_output_path, 'rb') as f:
                wardrobe.image.save(f'wardrobe_{wardrobe.id}.png', ContentFile(f.read()), save=True)

            # Deduct credits
            User.objects.filter(user_id=request.user.user_id).update(credit=F('credit') - 2)
            
            # Return response
            serializer = WardrobeSerializer(wardrobe)
            return wrap_response(success=True, code="wardrobe_generated", data=serializer.data)
        
        except Exception as e:
            return wrap_response(success=False, code="generation_failed", message=str(e))
        finally:
            # Cleanup
            if os.path.exists(temp_input_path): os.unlink(temp_input_path)
            if os.path.exists(temp_output_path): os.unlink(temp_output_path)

    def get(self, request):
        """
        Get all wardrobe images for the authenticated user.
        """
        wardrobe_id = request.query_params.get('wardrobe_id')
        if wardrobe_id:
            wardrobes = Wardrobe.objects.filter(id=wardrobe_id,user=request.user)
        else:
            wardrobes = Wardrobe.objects.filter(user=request.user).order_by('-created')
        serializer = WardrobeSerializer(wardrobes, many=True)
        return wrap_response(success=True, code="wardrobe_list", data=serializer.data)

    def delete(self, request):
        """
        Delete a wardrobe image by ID.
        """
        wardrobe_id = request.query_params.get('wardrobe_id')
        if not wardrobe_id:
            return wrap_response(success=False, code="missing_id", message="wardrobe_id is required")
        
        try:
            wardrobe = Wardrobe.objects.get(id=wardrobe_id, user=request.user)
            # Delete the image file from storage
            if wardrobe.image:
                wardrobe.image.delete(save=False)
            
            wardrobe.delete()
            return wrap_response(success=True, code="wardrobe_deleted", message="Wardrobe image deleted successfully")
        except Wardrobe.DoesNotExist:
            return wrap_response(success=False, code="not_found", message="Wardrobe image not found or access denied")


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
        temp_input_path = None
        wardrobe_instance = None
        
        if wardrobe_id:
            try:
                wardrobe_instance = Wardrobe.objects.get(id=wardrobe_id, user=request.user)
                temp_input_path = wardrobe_instance.image.path
            except Wardrobe.DoesNotExist:
                return wrap_response(success=False, code="wardrobe_not_found", message="Wardrobe not found")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_input:
                for chunk in input_image.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name
        
        # Output path
        temp_output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Generate synchronously
            generated_mockup_path = generate_fashion_image(
                type='studio',
                input_image_path=temp_input_path,
                params=parameters,
                output_path=temp_output_path
            )

            if not generated_mockup_path:
                raise Exception("Failed to generate studio mockup")

            # Create Studio instance
            studio = Studio.objects.create(
                user=request.user,
                wardrobe=wardrobe_instance,
                status='COMPLETED'
            )
            
            # Save image if uploaded
            if input_image:
                with open(temp_input_path, 'rb') as f:
                    studio.image.save(f'studio_input_{studio.id}.jpg', ContentFile(f.read()), save=False)
            
            # Save mockup
            with open(temp_output_path, 'rb') as f:
                studio.mockup.save(f'studio_mockup_{studio.id}.png', ContentFile(f.read()), save=True)

            # Deduct credits
            User.objects.filter(user_id=request.user.user_id).update(credit=F('credit') - 2)
            
            response_serializer = StudioSerializer(studio)
            return wrap_response(success=True, code="studio_mockup_generated", data=response_serializer.data)
        
        except Exception as e:
            return wrap_response(success=False, code="generation_failed", message=str(e))
        finally:
            # Cleanup only if it was a new upload
            if not wardrobe_id and temp_input_path and os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)

    def get(self, request):
        """
        Get all studio mockups for the authenticated user.
        """
        studio_id = request.query_params.get('studio_id')
        if studio_id:
            studio = Studio.objects.filter(id=studio_id,user=request.user)
        else:
            studio = Studio.objects.filter(user=request.user).order_by('-created')
        serializer = StudioSerializer(studio, many=True)
        return wrap_response(success=True, code="studio_list", data=serializer.data)

    def delete(self, request):
        """
        Delete a studio mockup by ID.
        """
        studio_id = request.query_params.get('studio_id')
        if not studio_id:
            return wrap_response(success=False, code="missing_id", message="studio_id is required")
        
        try:
            studio = Studio.objects.get(id=studio_id, user=request.user)
            # Delete associated files
            # if studio.image:
            #     studio.image.delete(save=False)
            # if studio.mockup:
            #     studio.mockup.delete(save=False)
            
            studio.delete()
            return wrap_response(success=True, code="studio_deleted", message="Studio mockup deleted successfully")
        except Studio.DoesNotExist:
            return wrap_response(success=False, code="not_found", message="Studio mockup not found or access denied")
