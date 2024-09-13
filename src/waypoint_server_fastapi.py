from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import logging
from typing import List, Dict, Any
import asyncio

'''
    Waypoint Server : A REST server that takes in waypoints and sends back the next waypoint for a specific drone request.
    
    Inputs :  1] A list of n waypoints. A waypoint is defined by latitude, longitude and height.
              2] A list of n delay times (in seconds)
               
    Return : A single waypoint for each drone request. 
'''

app = FastAPI()

# Initialize global variables
devices: List[str] = []
waypoints: Dict[str, List[Dict[str, Any]]] = {}
delays: Dict[str, List[int]] = {}

# Configure Logger
logging.basicConfig(filename='../logs/waypoint_server.log',  # Log file name
                    level=logging.DEBUG,  # Logging level
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class WaypointRequest(BaseModel):
    devices: List[str]
    waypoints: Dict[str, List[Dict[str, Any]]]  # Mapping device_id to list of waypoints
    delays: Dict[str, List[int]]  # Mapping device_id to list of delays

@app.get('/devices/{device_id}/{wp_no}')
async def send_waypoint(device_id: str, wp_no: int):
    global waypoints, delays
    try:
        # Simulate delay
        await asyncio.sleep(delays[device_id][wp_no])
        waypoint = waypoints[device_id][wp_no]
        
        # Return the waypoint
        logging.info(f"Sending Waypoint for {device_id} : {waypoint}")
        return {
            "device_id": device_id,
            "waypoint": waypoint
        }
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Error from Waypoint Server")

@app.post('/waypoints')
async def setup_devices(request: WaypointRequest):
    global waypoints, delays, devices
    
    # Extract waypoints and delays from the data
    devices = request.devices
    waypoints = request.waypoints
    delays = request.delays

    return {"message": "Waypoints and delays set successfully."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="debug")
