from flask import Flask, request
from datetime import datetime
import os

app = Flask(__name__)

LOG_FILE = "access.log"

@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
def index():
    user_agent = request.headers.get("User-Agent", "unknown")
    ip_address = request.remote_addr or "unknown"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] IP: {ip_address} | User-Agent: {user_agent}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    return "OK\n", 200

if __name__ == "__main__":
    print("Servidor local iniciado")
    print(f"Log: {os.path.abspath(LOG_FILE)}")
    app.run(host='0.0.0.0', port=8081), debug=False)
