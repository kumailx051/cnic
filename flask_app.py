from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json
import base64
import os
import threading
import queue
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'remote_desktop_secret_key_azure')

# Configure SocketIO for maximum performance
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=False,
    engineio_logger=False,
    ping_timeout=30,        # Reduced for faster detection of disconnects
    ping_interval=10,       # More frequent pings for better connection monitoring
    max_http_buffer_size=20000000,  # 20MB buffer for large images
    compression=True,       # Enable compression for better bandwidth usage
    always_connect=True,    # Ensure connections are always available
    binary=True            # Enable binary mode for better image transmission
)

# Server status variables with performance tracking
server_status = {
    'start_time': datetime.now(),
    'controllers': {},  # Store multiple controllers
    'targets': {},      # Store multiple targets
    'total_connections': 0,
    'controller_connections': 0,
    'target_connections': 0,
    'active_sessions': {},  # Track controller-target pairs
    'performance_stats': {
        'frames_processed': 0,
        'total_data_transferred': 0,
        'average_frame_size': 0,
        'last_frame_time': 0
    }
}

# High-performance message queue for screen data
screen_data_queue = queue.Queue(maxsize=100)  # Limit queue size to prevent memory issues
frame_drop_counter = 0

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
    controller_id = data.get('controller_id', request.sid)
    server_status['controllers'][request.sid] = {
        'ip': request.environ.get('REMOTE_ADDR', 'Unknown'),
        'timestamp': datetime.now(),
        'controller_id': controller_id
    }
    server_status['controller_connections'] += 1
    
    # Join specific controller room
    join_room(f'controller_{controller_id}')
    join_room('controllers')
    emit('connection_status', {'status': 'connected', 'type': 'controller', 'controller_id': controller_id})
    print(f"Controller joined: {request.sid} with ID: {controller_id}")

@socketio.on('join_as_target')
def on_join_target(data):
    target_id = data.get('target_id', request.sid)
    server_status['targets'][request.sid] = {
        'ip': request.environ.get('REMOTE_ADDR', 'Unknown'),
        'timestamp': datetime.now(),
        'target_id': target_id
    }
    server_status['target_connections'] += 1
    
    # Join specific target room
    join_room(f'target_{target_id}')
    join_room('targets')
    emit('connection_status', {'status': 'connected', 'type': 'target', 'target_id': target_id})
    print(f"Target joined: {request.sid} with ID: {target_id}")

@socketio.on('pair_with_target')
def on_pair_with_target(data):
    """Controller requesting to pair with a specific target"""
    controller_sid = request.sid
    target_id = data.get('target_id')
    
    if controller_sid in server_status['controllers']:
        # Find target by ID
        target_sid = None
        for sid, target_info in server_status['targets'].items():
            if target_info.get('target_id') == target_id:
                target_sid = sid
                break
        
        if target_sid:
            # Create session pair
            session_id = f"session_{controller_sid}_{target_sid}"
            server_status['active_sessions'][session_id] = {
                'controller': controller_sid,
                'target': target_sid,
                'timestamp': datetime.now()
            }
            
            # Join session room
            join_room(session_id)
            socketio.server.enter_room(target_sid, session_id)
            
            emit('pairing_success', {'target_id': target_id, 'session_id': session_id})
            socketio.emit('controller_paired', {'controller_id': server_status['controllers'][controller_sid]['controller_id'], 'session_id': session_id}, room=target_sid)
            print(f"Paired controller {controller_sid} with target {target_sid}")
        else:
            emit('pairing_failed', {'error': 'Target not found'})

@socketio.on('screen_data')
def on_screen_data(data):
    """High-performance screen data handler with frame dropping"""
    global frame_drop_counter
    target_sid = request.sid
    session_id = data.get('session_id')
    
    if target_sid not in server_status['targets']:
        return
    
    # Performance optimization: Drop frames if queue is getting full
    current_queue_size = screen_data_queue.qsize()
    
    if current_queue_size > 5:  # If more than 5 frames waiting, drop this frame
        frame_drop_counter += 1
        if frame_drop_counter % 10 == 0:  # Log every 10th dropped frame
            print(f"Dropped {frame_drop_counter} frames for performance")
        return
    
    # Add timestamp for latency tracking
    data['server_timestamp'] = time.time()
    
    # Update performance stats
    image_size = len(data.get('image', ''))
    server_status['performance_stats']['frames_processed'] += 1
    server_status['performance_stats']['total_data_transferred'] += image_size
    server_status['performance_stats']['last_frame_time'] = time.time()
    
    # Calculate average frame size
    frames = server_status['performance_stats']['frames_processed']
    total_data = server_status['performance_stats']['total_data_transferred']
    server_status['performance_stats']['average_frame_size'] = total_data / frames if frames > 0 else 0
    
    # Fast routing based on session
    if session_id and session_id in server_status['active_sessions']:
        # Direct emit to specific session - fastest path
        socketio.emit('screen_update', data, room=session_id, binary=True)
    else:
        # Fallback: broadcast to all controllers
        socketio.emit('screen_update', data, room='controllers', binary=True)

@socketio.on('control_event')
def on_control_event(data):
    """High-performance control event handler"""
    controller_sid = request.sid
    session_id = data.get('session_id')
    
    if controller_sid not in server_status['controllers']:
        return
    
    # Add timestamp for latency tracking
    data['server_timestamp'] = time.time()
    
    # Fast routing - prioritize session-based routing
    if session_id and session_id in server_status['active_sessions']:
        # Direct emit to specific target - fastest path
        socketio.emit('control_command', data, room=session_id, binary=True)
    else:
        # Fallback: broadcast to all targets
        socketio.emit('control_command', data, room='targets', binary=True)

@socketio.on('screenshot_request')
def on_screenshot_request(data):
    """High-performance screenshot request handler"""
    controller_sid = request.sid
    session_id = data.get('session_id')
    
    if controller_sid in server_status['controllers']:
        data['server_timestamp'] = time.time()
        if session_id and session_id in server_status['active_sessions']:
            socketio.emit('take_screenshot', data, room=session_id, binary=True)
        else:
            socketio.emit('take_screenshot', data, room='targets', binary=True)

@socketio.on('screenshot_data')
def on_screenshot_data(data):
    """High-performance screenshot data handler"""
    target_sid = request.sid
    session_id = data.get('session_id')
    
    if target_sid in server_status['targets']:
        data['server_timestamp'] = time.time()
        if session_id and session_id in server_status['active_sessions']:
            socketio.emit('screenshot_response', data, room=session_id, binary=True)
        else:
            socketio.emit('screenshot_response', data, room='controllers', binary=True)

@socketio.on('terminal_command')
def on_terminal_command(data):
    """High-performance terminal command handler"""
    controller_sid = request.sid
    session_id = data.get('session_id')
    
    if controller_sid in server_status['controllers']:
        data['server_timestamp'] = time.time()
        if session_id and session_id in server_status['active_sessions']:
            socketio.emit('execute_terminal', data, room=session_id, binary=True)
        else:
            socketio.emit('execute_terminal', data, room='targets', binary=True)

@socketio.on('terminal_output')
def on_terminal_output(data):
    """High-performance terminal output handler"""
    target_sid = request.sid
    session_id = data.get('session_id')
    
    if target_sid in server_status['targets']:
        data['server_timestamp'] = time.time()
        if session_id and session_id in server_status['active_sessions']:
            socketio.emit('terminal_response', data, room=session_id, binary=True)
        else:
            socketio.emit('terminal_response', data, room='controllers', binary=True)

@socketio.on('get_targets')
def on_get_targets(data):
    """Return list of available targets for controller"""
    if request.sid in server_status['controllers']:
        targets_list = []
        for sid, target_info in server_status['targets'].items():
            targets_list.append({
                'target_id': target_info.get('target_id', sid),
                'ip': target_info.get('ip', 'Unknown'),
                'timestamp': target_info.get('timestamp').isoformat() if target_info.get('timestamp') else None
            })
        emit('targets_list', {'targets': targets_list})

@app.route("/test")
def test():
    return "Hello from Flask on Azure! SocketIO Server is running!"

@app.route("/performance")
def performance():
    """Performance monitoring endpoint"""
    global frame_drop_counter
    
    uptime = datetime.now() - server_status['start_time']
    stats = server_status['performance_stats']
    
    # Calculate performance metrics
    frames_per_second = 0
    if uptime.total_seconds() > 0:
        frames_per_second = stats['frames_processed'] / uptime.total_seconds()
    
    avg_frame_size_mb = stats['average_frame_size'] / (1024 * 1024) if stats['average_frame_size'] > 0 else 0
    total_data_gb = stats['total_data_transferred'] / (1024 * 1024 * 1024)
    
    performance_data = {
        "server_uptime": str(uptime).split('.')[0],
        "total_frames_processed": stats['frames_processed'],
        "frames_per_second": round(frames_per_second, 2),
        "average_frame_size_mb": round(avg_frame_size_mb, 2),
        "total_data_transferred_gb": round(total_data_gb, 2),
        "frames_dropped": frame_drop_counter,
        "active_sessions": len(server_status['active_sessions']),
        "connected_controllers": len(server_status['controllers']),
        "connected_targets": len(server_status['targets']),
        "last_frame_time": stats['last_frame_time'],
        "queue_size": screen_data_queue.qsize()
    }
    
    return json.dumps(performance_data, indent=2)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
