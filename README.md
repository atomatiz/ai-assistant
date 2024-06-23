# AI Assistant.

This is AI Assistant repo which is created by FastAPI, Redis, Websocket, Cloudhost, OpenAI, Gemini, Docker, Github CI/CD.

## Running Locally

Find required variables in config file.
Create .env file and append variables with your value to .env.
Can run the application in VS Code or a terminal and it will be available at `http://localhost:8000/api`.

```bash
python3 -m virtualenv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install --no-cache-dir --upgrade -r requirements.txt
uvicorn main:app --reload
```
