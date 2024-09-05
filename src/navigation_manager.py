import requests
import logging
import asyncio

'''
    Navigation Manager : Responsible for handling missions for Drones by coordinating with Waypoint server.
'''

base_url = 'http://127.0.0.1:5000'

# Define waypoints for Device
waypoints = {
    
    "M7DOCK1": [  # Drone 1 waypoints
        {"latitude": 12.9716, "longitude": 77.5946, "height": 300},
        {"latitude": 28.7041, "longitude": 77.1025, "height": 200},
        {"latitude": 19.0760, "longitude": 72.8777, "height": 150}
    ],
    
    "M30TDOCK2": [  # Drone 2 waypoints
        {"latitude": 12.9716, "longitude": 77.5946, "height": 300},
        {"latitude": 28.7041, "longitude": 77.1025, "height": 200},
        {"latitude": 19.0760, "longitude": 72.8777, "height": 150}
    ]
}

# Define delays for processing each waypoint for each device
delays = {
    "M7DOCK1":  [2, 2, 2],
    "M30TDOCK2":[2, 2, 2]
}

# Add a Device
devices = [ "M7DOCK1", "M30TDOCK2" ]

# Configure Logger
logging.basicConfig(
    filename='../logs/navigation_manager.log',  # Log file name
    level=logging.DEBUG,  # Logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class NavigationManager:
    """Class to manage navigation for drones."""

    def get_waypoint(self,device_id, index):
        """Get the next waypoint for a specific drone with added delay."""
        
        url = f"{base_url}/devices/{device_id}/{index}"
        response = requests.get(url)
        if response.status_code == 200 or response.json() is not None:
            logging.info(response.json())
            return response.json()
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")
        

    def setup_devices(self,devices,waypoints, delays):
        """Set waypoints and delays in one go."""
        
        # Combine waypoints and delays into a single dictionary
        data = {
            "devices" : devices,
            "waypoints": waypoints,
            "delays": delays
        }

        # Post the combined data to the server
        url = f"{base_url}/waypoints"  # A single endpoint to handle both waypoints and delays
        response = requests.post(url, json=data)

        # Check the response status
        if response.status_code == 200:
            logging.info("Waypoints and delays set successfully.")
            logging.info(response.json())
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")
            
    async def execute_mission(self, device_id):
        
        for wp_no in range(len(waypoints[device_id])):
            waypoint = self.get_waypoint(device_id, wp_no)
            await asyncio.sleep(0.1)
            self.goto_waypoint(device_id,waypoint)
    
    async def goto_waypoint(device_id,waypoint):
        # TODO : Handle Cloud API calls 

async def main():
    # Create a list of tasks
    tasks = []
    
    # Iterate over device ids and add tasks to the list
    for device_id in devices:
        tasks.append(nm.execute_mission(device_id))
    
    # Use asyncio.gather to run tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    nm = NavigationManager()
    nm.setup_devices(devices,waypoints,delays)
    
    #TODO : Initialise Drone API Setup
    asyncio.run(main())

    