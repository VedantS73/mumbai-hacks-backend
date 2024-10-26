import json
from flask import Blueprint, request, jsonify
from app.services.campaign_services import CampaignService
import google.generativeai as genai
from PIL import Image
import io

gemini_bp = Blueprint('gemini', __name__)
print("Gemini API routes loaded", gemini_bp)

# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyBXWinWVpgn0dEqI53sNb52eOr5YunqF10"  # Replace with your API key
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_image(image):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "Please extract and list all the text visible in this image."
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        print(f"Text extraction error: {str(e)}")
        return ""

def create_personalized_prompt(product_info, persona, extracted_text):
    occupation = persona.get('occupation', 'customer')
    language = persona.get('language', 'English')

    occupation_prompts = {
        "trekker": "Create marketing text for a trekking enthusiast who needs reliable gear for their adventures.",
        "student": "Create marketing text for a student who needs practical solutions for their daily college life.",
        "professional": "Create marketing text for a working professional who needs reliable business accessories.",
        "athlete": "Create marketing text for an athlete who needs durable gear for their training and competitions.",
        # "customer": "Create personalized marketing text for this customer.",
    }

    # Adjusted language instructions for Bengali and other languages
    language_instructions = {
    "Hindi": """
        Generate marketing text in Hindi. Use culturally relevant Hindi expressions and format as:
        हिंदी: [Hindi marketing text with emojis in regional script]
    """,
    "Bengali": """
        Generate marketing text in Bengali. Use culturally relevant Bengali expressions and format as:
        বাংলা: [Bengali marketing text with emojis in regional script]
    """,
    "Telugu": """
        Generate marketing text in Telugu. Use culturally relevant Telugu expressions and format as:
        తెలుగు: [Telugu marketing text with emojis in regional script]
    """,
    "Marathi": """
        Generate marketing text in Marathi. Use culturally relevant Marathi expressions and format as:
        मराठी: [Marathi marketing text with emojis in regional script]
    """,
    "Tamil": """
        Generate marketing text in Tamil. Use culturally relevant Tamil expressions and format as:
        தமிழ்: [Tamil marketing text with emojis in regional script]
    """,
    "Urdu": """
        Generate marketing text in Urdu. Use culturally relevant Urdu expressions and format as:
        اردو: [Urdu marketing text with emojis in regional script]
    """,
    "Gujarati": """
        Generate marketing text in Gujarati. Use culturally relevant Gujarati expressions and format as:
        ગુજરાતી: [Gujarati marketing text with emojis in regional script]
    """,
    "Malayalam": """
        Generate marketing text in Malayalam. Use culturally relevant Malayalam expressions and format as:
        മലയാളം: [Malayalam marketing text with emojis in regional script]
    """,
    "Kannada": """
        Generate marketing text in Kannada. Use culturally relevant Kannada expressions and format as:
        ಕನ್ನಡ: [Kannada marketing text with emojis in regional script]
    """,
    "Odia": """
        Generate marketing text in Odia. Use culturally relevant Odia expressions and format as:
        ଓଡ଼ିଆ: [Odia marketing text with emojis in regional script]
    """,
    "Punjabi": """
        Generate marketing text in Punjabi. Use culturally relevant Punjabi expressions and format as:
        ਪੰਜਾਬੀ: [Punjabi marketing text with emojis in regional script]
    """,
    "English": "Generate engaging marketing text in English with relevant emojis.",
}


    base_prompt = f"""
    Product Context: {product_info}
    Image Details: {extracted_text}

    Target Audience Profile:
    - Age: {persona.get('age')}
    - Location: {persona.get('location')}
    - Occupation: {occupation}

    {occupation_prompts.get(occupation.lower(), "Create personalized marketing text for this customer.")}
    {language_instructions.get(language, language_instructions['English'])}

    Requirements:
    1. Make it personal and relatable to their specific lifestyle.
    2. Reference how the product solves their specific needs.
    3. Use occupation-specific scenarios and pain points.
    4. Include relevant emojis.
    5. Keep the tone friendly but professional.
    6. Make cultural references relevant to their location.
    7. Maximum length: 3-4 sentences.
    """
    return base_prompt

@gemini_bp.route('/api/gemini', methods=['POST'])
def generate_captions():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['image']
        img = Image.open(image_file)
        extracted_text = extract_text_from_image(img)

        data = request.form.to_dict()
        product_info = data.get('product_info')

        # Collect personas dynamically by parsing JSON data in person fields
        personas = []
        index = 1
        while True:
            person_key = f'person{index}'
            if person_key not in data:
                break
            
            # Parse the person data as JSON
            try:
                persona = json.loads(data[person_key])
                personas.append(persona)
            except json.JSONDecodeError:
                return jsonify({'error': f'Invalid JSON format for {person_key}'}), 400

            index += 1

        # Generate marketing content for each persona
        model = genai.GenerativeModel('gemini-1.5-flash')
        marketing_content = {}

        for idx, persona in enumerate(personas):
            prompt = create_personalized_prompt(product_info, persona, extracted_text)
            response = model.generate_content(prompt)
            marketing_content[f"persona_{idx + 1}"] = {
                "text": response.text,
                "language": persona.get('language', 'English'),
                "occupation": persona.get('occupation', 'customer')
            }

        return jsonify({
            'extracted_text': extracted_text,
            'marketing_content': marketing_content,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
    
@gemini_bp.route('/api/gemini/<int:campaign_id>', methods=['POST'])
def generate_campaign_data(campaign_id):
    # Fetch the data from the database with the given ID
    campaign = CampaignService.get_campaign_by_id(campaign_id)

    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    print("Campaign fetched - ", campaign.title)
    
    # You can add further processing here if needed

    return jsonify({
        'id': campaign.id,
        'title': campaign.title,
        'description': campaign.description,
        'status': campaign.status,
        'created_at': campaign.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }), 200