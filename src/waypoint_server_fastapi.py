from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import logging
from typing import List, Dict, Any
import asyncio
import uvicorn
import random

app = FastAPI()

waypoints = {
    "1": {"latitude": 18.56849790505247, "longitude": 73.77241440377952, "height": 30},
    "2": {"latitude": 18.56814419638304, "longitude": 73.7733034003183, "height": 30},
    "3": {"latitude": 18.567303425474776, "longitude": 73.773753306481, "height": 30},
    "4": {"latitude": 18.56612635758804, "longitude": 73.77348577255606, "height": 30},
    "5": {"latitude": 18.56551173791928, "longitude": 73.77262109753568, "height": 30},
    "6": {"latitude": 18.565732082455305, "longitude": 73.77149764543142, "height": 30},
    "7": {"latitude": 18.566184354851693, "longitude": 73.77036678591514, "height": 30},
    "8": {"latitude": 18.567305732662255, "longitude": 73.77006645984676, "height": 30},
    "9": {"latitude": 18.5680572313157, "longitude": 73.77054917556094, "height": 30},
    "10": {"latitude": 18.568529703661184, "longitude": 73.77129523877957, "height": 30}
}

# Add a new Device here
devices = ["66e299a6b649065f39d6d5d8", "66e29a0db649065f39d6d601","66e29a6bb649065f39d6d626","66e9c311b649065f39d7d603","66e9c382b649065f39d7d64c"]

# Define delays for processing each waypoint for each device
delays = [ 2,2,2,2,2,2,2,2,2,2 ]

# Configure Logger
logging.basicConfig(filename='../logs/waypoint_server.log',  # Log file name
                    level=logging.DEBUG,  # Logging level
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


@app.get('/waypoints')
async def send_waypoint():
    global waypoints, delays
    try:
        logging.info(f"Received GET Waypoint Request {time.time()}")

        # Simulate delay
        wp_no = random.randint(1, len(waypoints))  # Ensure wp_no is between 1 and len(waypoints)
        await asyncio.sleep(5.0)

        # Check if the waypoint exists
        if str(wp_no) not in waypoints:
            raise ValueError(f"Invalid waypoint number: {wp_no}")

        # Return the waypoint
        waypoint = waypoints[str(wp_no)]
        logging.info(f"Success : Sending Waypoint : {waypoint} {time.time()}")
        return {
            "waypoint": waypoint,
            "waypoint_no": wp_no
        }
    except Exception as e:
        logging.error(f"Error (send_waypoint): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error from Waypoint Server: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, port=5000, log_level="debug")
