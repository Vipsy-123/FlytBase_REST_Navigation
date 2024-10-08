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

def get_waypoint(device_id, index):
    # Combine waypoints and delays into a single dictionary
    data = {
        "waypoints": waypoints,
        "delays": delays
    }

    # Post the combined data to the server
    url = f"{base_url}/waypoints"  # A single endpoint to handle both waypoints and delays
    response = requests.post(url, json=data)
    
    url = f"{base_url}/devices/{device_id}/{index}"
    response = requests.get(url)  # Use GET to match the server method
    
    if response.status_code == 200:
        return response.json()  # Return the JSON response for assertions
    else:
        return None

def test_get_waypoint_m7dock1():
    response_data = get_waypoint("M7DOCK1", 1)
    assert response_data is not None, "Failed to get response"
    assert response_data["device_id"] == "M7DOCK1", "Device ID mismatch"


def test_get_waypoint_m30tdock2():
    response_data = get_waypoint("M30TDOCK2", 2)
    assert response_data is not None, "Failed to get response"
    assert response_data["device_id"] == "M30TDOCK2", "Device ID mismatch"


