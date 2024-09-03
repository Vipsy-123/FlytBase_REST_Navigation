import requests

base_url = 'http://127.0.0.1:5000/waypoints'

def get_waypoint(device_id, index):
    url = f"{base_url}/{device_id}/{index}"
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


