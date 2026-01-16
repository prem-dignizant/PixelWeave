from rest_framework import status
from rest_framework.views import APIView
from pixelweave_app.utils import wrap_response
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from .models import Wardrobe
from .serializers import WardrobeSerializer, WardrobeCreateSerializer
from .service import generate_fashion_image
import os
import tempfile
from django.conf import settings


class WardrobeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a wardrobe image from uploaded clothing image and background color.
        
        Expected payload:
        - input_image: Image file (multipart/form-data)
        - bg_color: Background color (optional, default: 'white')
        """
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
        
        # Generate output path for the processed image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Generate the wardrobe image using the service
            params = {'bg_color': bg_color}
            generated_image = generate_fashion_image(
                type='wardrobe',
                input_image_path=temp_input_path,
                params=params,
                output_path=temp_output_path
            )
            
            if not generated_image:
                return wrap_response(success=False, code="failed_to_generate_image", message="Failed to generate wardrobe image")
            
            # Create Wardrobe instance
            wardrobe = Wardrobe.objects.create(
                user=request.user,
                bg_color=bg_color
            )
            
            # Read the generated image and save it to the wardrobe instance
            with open(temp_output_path, 'rb') as f:
                wardrobe.image.save(
                    f'wardrobe_{wardrobe.id}.png',
                    ContentFile(f.read()),
                    save=True
                )
            
            # Serialize and return the response
            response_serializer = WardrobeSerializer(wardrobe)
            return wrap_response(success=True, code="wardrobe_created", data=response_serializer.data)
        
        except Exception as e:
            return wrap_response(success=False, code="failed_to_generate_image", message=str(e))
        
        finally:
            # Clean up temporary files
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)

    def get(self, request):
        """
        Get all wardrobe images for the authenticated user.
        """
        wardrobes = Wardrobe.objects.filter(user=request.user).order_by('-created')
        serializer = WardrobeSerializer(wardrobes, many=True)
        return wrap_response(success=True, code="wardrobe_list", data=serializer.data)