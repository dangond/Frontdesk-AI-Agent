import os  
import json  
import requests  
import logging
from typing import BinaryIO
from dotenv import load_dotenv
from openai import OpenAI 
from app.domain.agents.routing_agent import RoutingAgent  
from app.schema import User, Audio 

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()

WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = OpenAI(api_key= OPENAI_API_KEY)

# for voice notes (get download URL and download to file system)
def download_file_from_facebook(file_id: str, file_type: str, mime_type: str) -> str | None:  
    # First GET request to retrieve the download URL  
    url = f"https://graph.facebook.com/v19.0/{file_id}"  
    headers = {"Authorization": f"Bearer {WHATSAPP_API_KEY}"}  
    response = requests.get(url, headers=headers)
    if response.status_code == 200:  
        download_url = response.json().get('url')  
        # Second GET request to download the file  
        response = requests.get(download_url, headers=headers)  
        if response.status_code == 200:
            # Extract file extension from mime_type    
            file_extension = mime_type.split('/')[-1].split(';')[0]
            # Create file_path with extension
            file_path = f"{file_id}.{file_extension}"  
            with open(file_path, 'wb') as file:  
                file.write(response.content)  
            if file_type == "image" or file_type == "audio":  
                return file_path  
        raise ValueError(f"Failed to download file. Status code: {response.status_code}")  
    raise ValueError(f"Failed to retrieve download URL. Status code: {response.status_code}")

# transcribe audio using whisper LLM
def transcribe_audio_file(audio_file: BinaryIO) -> str:  
    if not audio_file:  
        return "No audio file provided"  
    try:  
        transcription = llm.audio.transcriptions.create(  
            file=audio_file,  
            model="whisper-1",  
            response_format="text"  
        )  
        return transcription  
    except Exception as e:  
        raise ValueError("Error transcribing audio") from e

# transcribe audio using download and transcribe functions defined above
def transcribe_audio(audio: Audio) -> str:  
    file_path = download_file_from_facebook(audio.id, "audio", audio.mime_type)  
    with open(file_path, 'rb') as audio_binary:  
        transcription = transcribe_audio_file(audio_binary)  
    try:  
        os.remove(file_path)  
    except Exception as e:  
        print(f"Failed to delete file: {e}")  
    return transcription

# authneticate user by phone number
def authenticate_user_by_phone_number(phone_number: str) -> User | None:
    logger.info(f"Attempting to authenticate user with phone number: {phone_number}")

    allowed_users = [
        {"id": 1, "phone": "17818163706", "first_name": "David", "last_name": "Dangond", "role": "default"},
        {"id": 2, "phone": "+0987654321", "first_name": "test", "last_name": "test", "role": "default"}
    ]

    for user in allowed_users:
        if user["phone"] == phone_number:
            logger.info(f"User found: {user['first_name']} {user['last_name']}")
            return User(**user)

    logger.warning(f"Authentication failed for phone number: {phone_number}")
    return None

# Send or respond to a guest
def send_whatsapp_message(to, message, template=False):
    url = "https://graph.facebook.com/v21.0/504587716075008/messages"
    headers = {
        "Authorization": f"Bearer " + WHATSAPP_API_KEY,
        "Content-Type": "application/json"
    }

    if not template:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {
                    "code": "en_US"
                }
            }
        }

    try:
        # Log the outgoing request details
        logging.info(f"Sending POST request to {url} with headers: {headers} and data: {json.dumps(data, indent=2)}")
        
        # Send the POST request
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # Log the HTTP response status and body
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Body: {response.text}")
        if response.status_code == 401:
            logging.error("Authentication error: Please check your API key.")
        
        # Parse and return the response JSON
        response_data = response.json()
        return response_data
    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return {"error": str(e)}

def respond_and_send_message(user_message: str, user: User):
    # if user is locked out, activate faceID:
    if user_message.lower() == ("I am locked out of my room. Can I have a new key?").lower():
        send_whatsapp_message(user.phone, "Sorry to hear that. Sure, please authenticate yourself using FaceID.")
        return
    # Create an instance of RoutingAgent
    agent = RoutingAgent(user)

    # Process the user's message
    response = agent.process_message(user_message)

    print('Got agent response: ', response)

    send_whatsapp_message(user.phone, response)
