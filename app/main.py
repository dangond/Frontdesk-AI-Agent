import threading  
import logging
from typing_extensions import Annotated  
from fastapi import FastAPI, APIRouter, Query, HTTPException, Depends  
from app.domain import message_service
from app.schema import Payload, Message, Audio, Image, User  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFICATION_TOKEN = "sapientdev-ritz-demo"

app = FastAPI()

@app.get("/")
def verify_whatsapp(
    hub_mode: str = Query("subscribe", description="The mode of the webhook", alias="hub.mode"),
    hub_challenge: int = Query(..., description="The challenge to verify the webhook", alias="hub.challenge"),
    hub_verify_token: str = Query(..., description="The verification token", alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFICATION_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Invalid verification token")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/readiness")
def readiness():
    return {"status": "ready"}

def parse_message(payload: Payload) -> Message | None:  
    if not payload.entry[0].changes[0].value.messages:  
        return None  
    return payload.entry[0].changes[0].value.messages[0]  

def get_current_user(message: Annotated[Message, Depends(parse_message)]) -> User | None:  
    if not message:  
        return None  
    return message_service.authenticate_user_by_phone_number(message.from_)  

def parse_audio_file(message: Annotated[Message, Depends(parse_message)]) -> Audio | None:  
    if message and message.type == "audio":  
        return message.audio  
    return None  

def parse_image_file(message: Annotated[Message, Depends(parse_message)]) -> Image | None:  
    if message and message.type == "image":  
        return message.image  
    return None  

def message_extractor(  
        message: Annotated[Message, Depends(parse_message)],  
        audio: Annotated[Audio, Depends(parse_audio_file)],  
):  
    if audio:  
        return message_service.transcribe_audio(audio)  
    if message and message.text:  
        return message.text.body  
    return None

@app.post("/", status_code=200)
def receive_whatsapp(
        user: Annotated[User, Depends(get_current_user)],  
        user_message: Annotated[str, Depends(message_extractor)],  
        image: Annotated[Image, Depends(parse_image_file)],
):
    logger.info("Received request")

    # Log the user, user_message, and image
    logger.info(f"User: {user}")
    logger.info(f"User message: {user_message}")
    logger.info(f"Image: {image}")

    if not user and not user_message and not image:
        logger.info("No user, message, or image received. Returning 'ok'")
        return {"status": "ok"}

    if not user:
        logger.warning("Unauthorized access attempt - user not found")
        raise HTTPException(status_code=401, detail="Unauthorized")

    if image:
        logger.info("Image received (Can't handle images yet.)")
        return print("Image received (Can't handle images yet.)")

    if user_message:
        logger.info(f"Processing user message: {user_message}")
        # new thread for async processing 
        thread = threading.Thread(
            target=message_service.respond_and_send_message, 
            args=(user_message, user)
        )  
        thread.daemon = True  
        thread.start()

    return {"status": "ok"}
