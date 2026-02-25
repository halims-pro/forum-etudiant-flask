import configparser
from fastapi import FastAPI, WebSocket
# Charger la configuration
config = configparser.ConfigParser()
config.read("conf.ini")
if "server" not in config:
    raise RuntimeError("Section [server] manquante dans conf.ini")
HOST = config["server"].get("host","127.0.0.1")
PORT = int(config["server"].get("backend_port", 5000))

app = FastAPI()

# Exemple route REST
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur le forum EST Salé"}

# WebSocket pour le chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message reçu: {data}")
