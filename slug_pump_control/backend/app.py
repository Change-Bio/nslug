from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gpiozero import OutputDevice
from threading import Thread, Lock
import time
import os

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)

# Hardware Setup (configurable via environment variables)
STEP_PIN = int(os.environ.get('PUMP_STEP_PIN', 17))
DIR_PIN = int(os.environ.get('PUMP_DIR_PIN', 27))
STEPS_PER_REV = int(os.environ.get('PUMP_STEPS_PER_REV', 6400))

# Try to initialize GPIO, but don't crash if it fails
try:
    step = OutputDevice(STEP_PIN)
    direction = OutputDevice(DIR_PIN)
    GPIO_AVAILABLE = True
except Exception as e:
    print(f"Warning: GPIO initialization failed: {e}")
    print("Running in mock mode - pump commands will be logged but not executed")
    step = None
    direction = None
    GPIO_AVAILABLE = False

pump_state = {
    'running': False,
    'mode': None,
    'turns_remaining': 0
}
state_lock = Lock()

def move_pump(turns, mode):
    global pump_state

    with state_lock:
        pump_state['running'] = True
        pump_state['mode'] = mode
        pump_state['turns_remaining'] = turns

    if not GPIO_AVAILABLE:
        print(f"Mock mode: Would move pump {mode} for {turns} turns")
        time.sleep(turns * 2)  # Simulate operation time
        with state_lock:
            pump_state['running'] = False
            pump_state['mode'] = None
            pump_state['turns_remaining'] = 0
        return

    if mode.lower() == "forward":
        direction.off()
    else:
        direction.on()

    total_steps = int(turns * STEPS_PER_REV)

    for i in range(total_steps):
        with state_lock:
            if not pump_state['running']:
                break
            pump_state['turns_remaining'] = turns - (i / STEPS_PER_REV)

        step.on()
        time.sleep(0.0002)
        step.off()
        time.sleep(0.0002)

    with state_lock:
        pump_state['running'] = False
        pump_state['mode'] = None
        pump_state['turns_remaining'] = 0

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/pump/move', methods=['POST'])
def pump_move():
    data = request.json
    turns = float(data.get('turns', 1))
    mode = data.get('mode', 'forward')

    with state_lock:
        if pump_state['running']:
            return jsonify({'error': 'Pump is already running'}), 400

    thread = Thread(target=move_pump, args=(turns, mode))
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'ok', 'turns': turns, 'mode': mode})

@app.route('/api/pump/stop', methods=['POST'])
def pump_stop():
    with state_lock:
        pump_state['running'] = False
    return jsonify({'status': 'stopped'})

@app.route('/api/pump/status', methods=['GET'])
def pump_status():
    with state_lock:
        return jsonify(pump_state.copy())

if __name__ == '__main__':
    port = int(os.environ.get('PUMP_SERVER_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
