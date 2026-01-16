from google import genai
from PIL import Image
# from dotenv import load_dotenv
import os
import json

# load_dotenv()


def build_studio_prompt(params: dict) -> str:
    # Base instruction
    instruction = "Create a professional fashion model photoshoot using the garment from the reference image and given parameters."
    
    # Clean nested parameters - remove None/empty values recursively
    def clean_dict(d):
        if not isinstance(d, dict):
            return d
        return {k: clean_dict(v) for k, v in d.items() if v}
    
    clean_params = clean_dict(params)
    
    # Format as JSON string
    params_json = json.dumps(clean_params, indent=2)
    
    # Combine instruction with parameters
    full_prompt = f"{instruction}\n\nParameters:\n{params_json}"
    
    return full_prompt

def build_wardrobe_prompt(params:dict)-> str:
    bg_color = params['bg_color']
    full_prompt = f"""
    A professional studio fashion photoshoot of a clothing garment.

    The garment is displayed naturally as in a real fashion shoot, with correct proportions,
    realistic fabric drape, natural wrinkles, and visible stitching details.

    Background:
    - Solid {bg_color} background
    - Clean studio setup with subtle shadow falloff

    Style:
    - E-commerce fashion photography
    - No mannequins visible
    - No human body parts
    - No AI artifacts or distortions

    The final image should look like it was captured during a professional clothing brand photoshoot.
    """

    return full_prompt

def generate_fashion_image(type,input_image_path: str, params: dict, output_path: str = "transformed_image.png"):
    """
    Generate a fashion model image using the input garment and specified parameters.
    
    Args:
        input_image_path: Path to the input garment image
        params: Dictionary of parameters for image generation
        output_path: Path to save the generated image
        
    Returns:
        The generated image object
    """
    # Initialize the client
    client = genai.Client(
        vertexai=True, 
        project="buoyant-insight-483713-s1", 
        location="us-central1"
    )
    
    # Load the input image
    input_image = Image.open(input_image_path)
    
    # Build the prompt
    if type == 'studio':
        prompt = build_studio_prompt(params)
    else:
        prompt = build_wardrobe_prompt(params)
    
    # print(f"Generated Prompt:\n{prompt}\n")
    # print(f"Generating image...")
    
    # Generate content
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, input_image]
    )
    
    # Save the result
    generated_image = None
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            generated_image = part.as_image()
            generated_image.save(output_path)
            print(f"Image saved to: {output_path}")
            break
    
    return generated_image


parameters = {
    "garment_type": "t-shirt",
    "image_size": "1080x566",
    "background": {
        "location": "street",
        "lighting": "soft natural lighting with fill light"
    },
    "model": {
        "gender": "male",
        "age_group": "10-20",
        "model_region": "Indian",
        "model_color": "fair skin",
        "model_type": "tall",
        "mood": "attitude",
        "body_type" : "Athletic",
        "hair_style" : "mullet",
        "hair_color" : "black",
        "pose": "casual standing pose with hands in pockets",
    },
    "extra": {
        "camera_angle": "slightly below eye level",
        "style": "modern street style photography"
    },
}

# Example 2: Wardrobe Image Image Prompt
parameters = {
    "bg_color" : "white"
}


# Generate the image
if __name__ == "__main__":
    generate_fashion_image(
        type = "wardrobe", 
        input_image_path=r"c:\Users\Planet\Downloads\person_yellow_tshirt.jpg",
        params=parameters,
        output_path="transformed_image_4.png"
)

