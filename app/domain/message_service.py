import os  
import json  
import requests  
from typing import BinaryIO
from dotenv import load_dotenv
from openai import OpenAI 

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
    allowed_users = [  
        {"id": 1, "phone": "+17818163706", "first_name": "David", "last_name": "Dangond", "role": "default"},  
        {"id": 2, "phone": "+0987654321", "first_name": "Jane", "last_name": "Smith", "role": "default"}  
    ]    
    for user in allowed_users:  
        if user["phone"] == phone_number:  
            return User(**user)  
    return None