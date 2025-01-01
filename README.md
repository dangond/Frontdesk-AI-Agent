# Frontdesk-AI-Agent
tech:
- fastapi
- uvicorn
- ngrok


---

## Setup Instructions

1. **Clone the Repository:**

```bash
git clone https://github.com/dangond/Frontdesk-AI-Agent.git
cd Frontdesk-AI-Agent
```

2. **[Install uv](https://github.com/astral-sh/uv?tab=readme-ov-file) as our dependency manager and virtual environment:**

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. **Install Dependencies:**

```bash
uv sync
```

4. **Generate WHATSAPP_API_KEY and whitelist your phone number:**

- Navigate to our [meta developer page](https://developers.facebook.com/apps/2025363401270010/dashboard/?business_id=912842050976046)
- On the left navigation bar, navigate to WhatsApp > API Setup
- Click *Generate access token*

On the same page, under *Send and receive messages*, click _Select a recipient phone number_ under the *To* field and add your phone number associated with your WhatsApp account. This will allow the Test number to receive messages from you.

5. **Append private keys to .env and create .env if it doesn't already exist:**

```bash
echo "WHATSAPP_API_KEY=your_api_key_value" >> .env
# DO NOT SHARE THIS KEY:
echo "OPENAI_API_KEY = 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" >> .env
```

6. **Add your Whatsapp # to our own user whitelist for further authentication:**
- go to https://github.com/dangond/Frontdesk-AI-Agent/blob/844a1bc4f1c1e55a3a94480742b51048c3baf6d3/app/domain/message_service.py#L73
- Add an entry for yourself similar to the ones below:
```python
    allowed_users = [
        {"id": 1, "phone": "17818163706", "first_name": "David", "last_name": "Dangond", "role": "default"},
        {"id": 2, "phone": "+0987654321", "first_name": "test", "last_name": "test", "role": "default"}
    ]
```

7. **Run the app locally on port 8080:**

``` bash
uv run uvicorn app.main:app --reload --port 8080
```

8. **Create secure tunnel from internet to your local machine using Ngrok:**
- [Create Ngrok account] (https://dashboard.ngrok.com/signup)
- Get *$YOUR-AUTHENTICATION_TOKEN* which can be found under "Your Authtoken" in the ngrok side navigation
``` bash
uv run ngrok config add-authtoken $YOUR-AUTHENTICATION_TOKEN
uv run ngrok http http://localhost:8080
```

You will see something like this:
``` bash
Forwarding                    https://<random-string>.ngrok-free.app -> http://localhost:8080
```
Copy the https URL in the Forwarding header and save for the next step. This is your _Callback URL_

9. **Add the newly generated _Callback URL_ to our Webhook settings:**

- Navigate to our [meta developer page](https://developers.facebook.com/apps/2025363401270010/dashboard/?business_id=912842050976046)
- On the left navigation bar, navigate to WhatsApp > Configuration
- Paste the _Callback URL_ in the *Callback URL* field and _sapientdev-ritz-demo_ in the *Verify Token* field
- Click *Verify and Save*

10. **Send yourself a message to initiate the convo:**
- On the left navigation bar, navigate to WhatsApp > API Setup
- Select your phone number under the *To* field in *Step 1*
- Go to *Step 2* under *Send and receive messages*
- Copy the test message, paste and enter it from your terminal

*Expected Result:*
- Should see a response in the terminal ending with:
```bash
"message_status":"accepted"
```
- Should receive a a message to your WhatsApp.

11. DONE: You are ready to communicate with the AI front desk through WhatsApp.


**Troubleshooting**
- The WHATSAPP_API_KEY expires every now and then, generate a new one and replace the old one in .env
- Add logs to message_service similar to the ones that already exist if you want to troubleshoot further
