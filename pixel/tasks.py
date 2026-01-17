from celery import shared_task
from django.core.files.base import ContentFile
from .models import Wardrobe, Studio
from .service import generate_fashion_image
import os
import tempfile
import logging
from dotenv import load_dotenv
from django.db.models import F
from user.models import User
logger = logging.getLogger(__name__)

load_dotenv()

@shared_task
def generate_wardrobe_image_task(wardrobe_id, temp_input_path, bg_color):
    try:
        wardrobe = Wardrobe.objects.get(id=wardrobe_id)
        wardrobe.status = 'PROCESSING'
        wardrobe.save()

        # Generate output path for the processed image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_output:
            temp_output_path = temp_output.name

        try:
            params = {'bg_color': bg_color}
            generated_image = generate_fashion_image(
                type='wardrobe',
                input_image_path=temp_input_path,
                params=params,
                output_path=temp_output_path
            )

            if not generated_image:
                raise Exception("Failed to generate wardrobe image")

            # Read the generated image and save it to the wardrobe instance
            with open(temp_output_path, 'rb') as f:
                wardrobe.image.save(
                    f'wardrobe_{wardrobe.id}.png',
                    ContentFile(f.read()),
                    save=False
                )
            
            wardrobe.status = 'COMPLETED'
            wardrobe.save()
            User.objects.filter(user_id=wardrobe.user.user_id).update(credit=F('credit') - 2)
        except Exception as e:
            logger.error(f"Error generating image for Wardrobe {wardrobe_id}: {str(e)}")
            wardrobe.status = 'FAILED'
            wardrobe.error_message = str(e)
            wardrobe.save()
            
        finally:
            # Clean up temporary output file
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)

    except Wardrobe.DoesNotExist:
        logger.error(f"Wardrobe instance with id {wardrobe_id} not found.")

    finally:
        # Clean up temporary input file
        # Note: We clean this up here because the task is responsible for the file now
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)


@shared_task
def generate_studio_mockup_task(studio_id, temp_input_path, parameters):
    """
    Background task to generate studio mockup image.
    
    Args:
        studio_id: ID of the Studio instance
        temp_input_path: Path to temporary input image file
        parameters: Dictionary containing all studio generation parameters
    """
    try:
        studio = Studio.objects.get(id=studio_id)
        studio.status = 'PROCESSING'
        studio.save()

        # Generate output path for the processed mockup image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_output:
            temp_output_path = temp_output.name

        try:
            # Generate the studio mockup image
            generated_image = generate_fashion_image(
                type='studio',
                input_image_path=temp_input_path,
                params=parameters,
                output_path=temp_output_path
            )

            if not generated_image:
                raise Exception("Failed to generate studio mockup image")

            # Read the generated mockup and save it to the studio instance
            with open(temp_output_path, 'rb') as f:
                studio.mockup.save(
                    f'studio_mockup_{studio.id}.png',
                    ContentFile(f.read()),
                    save=False
                )
            
            studio.status = 'COMPLETED'
            studio.save()
            User.objects.filter(user_id=studio.user.user_id).update(credit=F('credit') - 2)

        except Exception as e:
            logger.error(f"Error generating mockup for Studio {studio_id}: {str(e)}")
            studio.status = 'FAILED'
            studio.error_message = str(e)
            studio.save()
            
        finally:
            # Clean up temporary output file
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)

    except Studio.DoesNotExist:
        logger.error(f"Studio instance with id {studio_id} not found.")

    finally:
        # Clean up temporary input file
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)


# celery -A pixelweave_app worker --loglevel=INFO --pool=solo
