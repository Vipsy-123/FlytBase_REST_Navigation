import requests

base_url = 'http://127.0.0.1:5000'

# Define waypoints for Drones 
waypoints = [[ # Drone1 wps
            {"latitude": 12.9716, "longitude": 77.5946, "height": 300},
            {"latitude": 28.7041, "longitude": 77.1025, "height": 200},
            {"latitude": 19.0760, "longitude": 72.8777, "height": 150}
            ],
            [  # Drone2 wps
            {"latitude": 12.9716, "longitude": 77.5946, "height": 300},
            {"latitude": 28.7041, "longitude": 77.1025, "height": 200},
            {"latitude": 19.0760, "longitude": 72.8777, "height": 150}
            ] 
    ]

# Define delays for processing each waypoints
delays = [[0.2,0.2,0.2],
        [0.2,0.2,0.2]]

def post_waypoint(waypoints,delays):

    # Combine waypoints and delays into a single dictionary
    data = {
        "waypoints": waypoints,
        "delays": delays
    }

    # Post the combined data to the server
    url = f"{base_url}/waypoints"  # A single endpoint to handle both waypoints and delays
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()  # Return the JSON response for assertions
    else:
        return None

def test_post_waypoint():
    response_data = post_waypoint(waypoints, delays)
    assert response_data is not None, "Failed to get response"

if __name__ == "__main__":
    test_post_waypoint()