from flask import Flask, jsonify, request
import time
import logging
import os

app = Flask(__name__)

devices = []
waypoints = []
delays = []

log_filename = os.path.join(os.path.dirname(__file__), "../logs/waypoint_server.log")

# Configure Logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # This sets the date format
    handlers=[
        logging.FileHandler(log_filename),  # Log to a file
        logging.StreamHandler()  # Also log to the console (terminal)
    ]
)

@app.route('/devices/<string:device_id>/<int:wp_no>', methods=['GET'])
def get_waypoint(device_id, wp_no):
    global waypoints, delays

    try:
        # Ensure the device_id and wp_no are within the valid range
        if device_id not in waypoints or wp_no >= len(waypoints[device_id]):
            raise ValueError("Invalid device_id or waypoint number")
        
        logging.info(f"Sending Waypoint for {device_id} : {waypoints[device_id][wp_no]}")
        time.sleep(int(delays[device_id][wp_no]))
        waypoint = waypoints[device_id][wp_no]
        
        return jsonify({
            "device_id": device_id,
            "waypoint": waypoint
        })
    except Exception as e:
        logging.error(f"Exception (get_waypoint): {e}")
        return jsonify({"Exception occured from Waypoint Server": str(e)}), 500
    
@app.route('/devices', methods=['POST'])
def setup_devices():
    logging.info(f"Received POST request at /devices")
    data = request.json
    
    global waypoints, delays, devices
    try:
        devices = data.get('devices', [])
        waypoints = data.get('waypoints', [])
        delays = data.get('delays', [])
        logging.info(f"Success (setup_devices) : Setup Complete: {data}")
        return {"message": "Waypoints and delays set successfully."}, 200
    except Exception as e :
        logging.exception(f"Exception (setup_devices) : {e}")
        return {"message": f"Setup Failed : {e} "}, 500
        

if __name__ == "__main__":
    app.run(debug=True)
