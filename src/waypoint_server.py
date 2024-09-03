from flask import Flask, jsonify, request
import time
'''
    Waypoint Server : A REST server that takes in waypoints and sends back the next waypoint for a specific drone request.
    
    Arguments : 1] A list of n waypoints. A waypoint is defined by latitude, longitude and height.
                2] A list of n delay times (in seconds)
                
    Return : A single waypoint for each drone request. 

'''
app = Flask(__name__)

waypoints = [[ {"latitude": 12.9716, "longitude": 77.5946, "height": 300},
               {"latitude": 28.7041, "longitude": 77.1025, "height": 200},
               {"latitude": 19.0760, "longitude": 72.8777, "height": 150}
            ],
            [  
               {"latitude": 12.9716, "longitude": 77.5946, "height": 300},
               {"latitude": 28.7041, "longitude": 77.1025, "height": 200},
               {"latitude": 19.0760, "longitude": 72.8777, "height": 150}
            ] 
    ]

delay = [5,5,5]

device_dict = { "M7DOCK1": 0 , 
                "M30TDOCK2": 1
              }

@app.route('/waypoints/<string:device_id>/<int:wp_no>', methods=['GET'])  # http://127.0.0.1:5000/waypoints/M7DOCK1/1
def send_waypoint(device_id,wp_no):
    # Sleep for a particular delay time
    time.sleep(delay[device_dict[device_id]])
    
    # Return the waypoint
    return jsonify({
        "device_id": device_id,
        "waypoint": waypoints[device_dict[device_id]][wp_no - 1]
    })

if __name__ == '__main__':
    app.run(debug=True)