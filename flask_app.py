from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json
import base64
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'remote_desktop_secret_key_azure')

# Configure SocketIO for Azure
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Server status variables
server_status = {
    'start_time': datetime.now(),
    'controllers': {},  # Store multiple controllers
    'targets': {},      # Store multiple targets
    'total_connections': 0,
    'controller_connections': 0,
    'target_connections': 0
}

@app.route('/')
def status_page():
    uptime = datetime.now() - server_status['start_time']
    
    controller_status = "🟢 Connected" if server_status['controllers'] else "🔴 Disconnected"
    target_status = "🟢 Connected" if server_status['targets'] else "🔴 Disconnected"
    
    controller_info = ""
    if server_status['controllers']:
        controller_info = f"{len(server_status['controllers'])} active controllers"
        
    target_info = ""
    if server_status['targets']:
        target_info = f"{len(server_status['targets'])} active targets"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Remote Desktop Server - Status</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .header { 
                text-align: center; 
                margin-bottom: 40px;
                border-bottom: 2px solid rgba(255,255,255,0.3);
                padding-bottom: 20px;
            }
            .status-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 30px 0;
            }
            .status-card {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .status-card h3 {
                margin-top: 0;
                color: #ffd700;
            }
            .info-section {
                background: rgba(0,0,0,0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .live-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #00ff00;
                border-radius: 50%;
                animation: pulse 2s infinite;
                margin-right: 10px;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                font-size: 0.9em;
                opacity: 0.8;
            }
            code {
                background: rgba(0,0,0,0.3);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            .update-notice {
                background: rgba(255, 215, 0, 0.2);
                border: 1px solid rgba(255, 215, 0, 0.5);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖥️ Remote Desktop Server</h1>
                <p><span class="live-indicator"></span>Hosted on Azure App Service (WebSocket Optimized)</p>
                <p><strong>Server Status:</strong> 🟢 Running</p>
            </div>
            
            <div class="update-notice">
                <h3>✅ Optimized for Azure</h3>
                <p>Server uses WebSocket connections with eventlet async mode for optimal performance on Azure App Service.</p>
                <p><strong>You need to update your controller and target programs!</strong></p>
            </div>
            
            <div class="status-grid">
                <div class="status-card">
                    <h3>📱 Controller Status</h3>
                    <p><strong>Status:</strong> {{ controller_status }}</p>
                    {% if controller_info %}
                    <p><strong>Connected from:</strong> {{ controller_info }}</p>
                    {% endif %}
                    <p><strong>Total Controller Connections:</strong> {{ controller_connections }}</p>
                </div>
                
                <div class="status-card">
                    <h3>🎯 Target Status</h3>
                    <p><strong>Status:</strong> {{ target_status }}</p>
                    {% if target_info %}
                    <p><strong>Connected from:</strong> {{ target_info }}</p>
                    {% endif %}
                    <p><strong>Total Target Connections:</strong> {{ target_connections }}</p>
                </div>
            </div>
            
            <div class="info-section">
                <h3>📊 Server Statistics</h3>
                <p><strong>Server Started:</strong> {{ start_time }}</p>
                <p><strong>Uptime:</strong> {{ uptime }}</p>
                <p><strong>Total Connections:</strong> {{ total_connections }}</p>
                <p><strong>Web Interface URL:</strong> https://your-app-name.azurewebsites.net/</p>
            </div>
            
            <div class="info-section">
                <h3>🔧 Connection Instructions (Updated)</h3>
                <p><strong>For Controller (Your PC):</strong></p>
                <ul>
                    <li>Server URL: <code>https://your-app-name.azurewebsites.net</code></li>
                    <li>Protocol: <code>WebSocket</code></li>
                    <li>Run: <code>controller.py</code> (Azure optimized)</li>
                </ul>
                
                <p><strong>For Target (PC to control):</strong></p>
                <ul>
                    <li>Server URL: <code>https://your-app-name.azurewebsites.net</code></li>
                    <li>Protocol: <code>WebSocket</code></li>
                    <li>Run: <code>target.py</code> (Azure optimized)</li>
                </ul>
            </div>
            
            <div class="info-section">
                <h3>ℹ️ How it Works (Azure Version)</h3>
                <p>This server uses WebSocket connections optimized for Azure App Service:</p>
                <ol>
                    <li><strong>Controller</strong> connects via WebSocket and sends control commands</li>
                    <li><strong>Server</strong> relays commands through WebSocket rooms with eventlet async mode</li>
                    <li><strong>Target</strong> receives commands and sends back screen data</li>
                    <li><strong>Azure WebSocket support</strong> enables full real-time communication</li>
                </ol>
            </div>
            
            <div class="footer">
                <p>🔄 Auto-refresh every 10 seconds | Last updated: {{ current_time }}</p>
                <p>Remote Desktop WebSocket Server v3.0 | Powered by Azure App Service</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template,
        controller_status=controller_status,
        target_status=target_status,
        controller_info=controller_info,
        target_info=target_info,
        start_time=server_status['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
        uptime=str(uptime).split('.')[0],
        total_connections=server_status['total_connections'],
        controller_connections=server_status['controller_connections'],
        target_connections=server_status['target_connections'],
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@socketio.on('connect')
def on_connect():
    server_status['total_connections'] += 1
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"Client disconnected: {request.sid}")
    
    # Clean up if this was a controller or target
    if request.sid in server_status['controllers']:
        del server_status['controllers'][request.sid]
        print("Controller disconnected")
        
    if request.sid in server_status['targets']:
        del server_status['targets'][request.sid]
        print("Target disconnected")

@socketio.on('join_as_controller')
def on_join_controller(data):
    server_status['controllers'][request.sid] = {
        'ip': request.environ.get('REMOTE_ADDR', 'Unknown'),
        'timestamp': datetime.now()
    }
    server_status['controller_connections'] += 1
    
    join_room('controllers')
    emit('connection_status', {'status': 'connected', 'type': 'controller'})
    print(f"Controller joined: {request.sid}")

@socketio.on('join_as_target')
def on_join_target(data):
    server_status['targets'][request.sid] = {
        'ip': request.environ.get('REMOTE_ADDR', 'Unknown'),
        'timestamp': datetime.now()
    }
    server_status['target_connections'] += 1
    
    join_room('targets')
    emit('connection_status', {'status': 'connected', 'type': 'target'})
    print(f"Target joined: {request.sid}")

@socketio.on('control_event')
def on_control_event(data):
    """Forward control events from controller to all targets"""
    if request.sid in server_status['controllers'] and server_status['targets']:
        socketio.emit('control_command', data, room='targets')
        print(f"Forwarded control event: {data['type']} to {len(server_status['targets'])} targets")

@socketio.on('screen_data')
def on_screen_data(data):
    """Forward screen data from target to all controllers"""
    if request.sid in server_status['targets'] and server_status['controllers']:
        socketio.emit('screen_update', data, room='controllers')
        # Only log occasionally to avoid spam
        if server_status['total_connections'] % 100 == 0:
            print(f"Forwarded screen data to {len(server_status['controllers'])} controllers")

@app.route("/test")
def test():
    return "Hello from Flask on Azure! SocketIO Server is running!"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
