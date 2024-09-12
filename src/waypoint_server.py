from flask import Flask, jsonify, request
import time
import logging


'''
    Waypoint Server : A REST server that takes in waypoints and sends back the next waypoint for a specific drone request.
    
    Inputs :  1] A list of n waypoints. A waypoint is defined by latitude, longitude and height.
              2] A list of n delay times (in seconds)
                
    Return : A single waypoint for each drone request. 

'''

app = Flask(__name__)

devices = []
waypoints = []
delays = []

# Configure Logger
logging.basicConfig(filename='../logs/waypoint_server.log',  # Log file name
                    level=logging.DEBUG,  # Logging level
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


@app.route('/devices/<string:device_id>/<int:wp_no>', methods=['GET'])  # http://127.0.0.1:5000/devices/M7DOCK1/1
def send_waypoint(device_id,wp_no):
    # Sleep for a particular delay time and then send waypoint
    global waypoints,delays
    
    try:
        logging.info(f"Sending Waypoint for {device_id} : {waypoints[device_id][wp_no]}")
        print(f"Sending Waypoint for {device_id} : {waypoints[device_id][wp_no]}")
        time.sleep(int(delays[device_id][wp_no]))
        waypoint = waypoints[device_id][wp_no]
        
        # Return the waypoint
        print(device_id)
        print(waypoint)

        return jsonify({
            "device_id": device_id,
            "waypoint": waypoint
        })
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"ERR0R :: {e} !")
        return jsonify({"Error from Waypoint Server"}), 500
    
@app.route('/waypoints', methods=['POST'])
def setup_devices():
    # Get JSON data from the request
    data = request.json
    global waypoints, delays, devices
    
    # Extract waypoints and delays from the data
    devices = data.get('devices', [])
    waypoints = data.get('waypoints', [])
    delays = data.get('delays', [])
    
    # print(devices)
    # print(waypoints)
    # print(delays)
    
    return jsonify({"message": "Waypoints and delays set successfully."})

if __name__ == '__main__':
    app.run(debug=True)