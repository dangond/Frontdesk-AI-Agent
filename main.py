from fastapi import FastAPI, Query, HTTPException


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
