import requests
import time

base_url = 'http://127.0.0.1:5000/waypoints'

# Get waypoint for a specific drone and index
def get_waypoint(device_id, index):
    url = f"{base_url}/{device_id}/{index}"
    response = requests.get(url)
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error {response.status_code}: {response.json()}")

if __name__ == "__main__":
    get_waypoint("M7DOCK1",1)