# flask_app.py

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testsecret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Simple test homepage
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask WebSocket Test</title>
        <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
        <script>
            const socket = io();
            socket.on('connect', () => {
                document.getElementById("status").innerText = "🟢 Connected";
                socket.emit("test_event", {message: "Hello from client!"});
            });

            socket.on("test_response", (data) => {
                document.getElementById("response").innerText = "Server says: " + data.reply;
            });
        </script>
    </head>
    <body style="font-family: sans-serif; margin: 40px;">
        <h1>✅ Flask WebSocket Test Page</h1>
        <p>Status: <span id="status">🔴 Connecting...</span></p>
        <p><span id="response">Waiting for response...</span></p>
    </body>
    </html>
    """)

@socketio.on('test_event')
def handle_test_event(data):
    print("Received from client:", data)
    emit('test_response', {'reply': 'Hello from Flask WebSocket Server!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
