#!/usr/bin/env python3
"""
WebSocket server for real-time updates across clinic iPads
Handles patient status updates, new registrations, and workflow notifications
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connected clients
connected_clients = set()

async def handle_client(websocket, path):
    """Handle a new WebSocket client connection"""
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0]
    logger.info(f"New client connected from {client_ip}. Total clients: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            # Broadcast message to all other connected clients
            if connected_clients:
                # Parse message and add timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                broadcast_message = f"[{timestamp}] {message}"
                
                # Send to all clients except sender
                disconnected = set()
                for client in connected_clients:
                    if client != websocket:
                        try:
                            await client.send(broadcast_message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected.add(client)
                
                # Remove disconnected clients
                connected_clients.difference_update(disconnected)
                
                logger.info(f"Broadcasted: {message} to {len(connected_clients)-1} clients")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Client {client_ip} disconnected. Total clients: {len(connected_clients)}")

async def broadcast_to_all(message):
    """Send a message to all connected clients"""
    if connected_clients:
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        connected_clients.difference_update(disconnected)

async def start_server():
    """Start the WebSocket server"""
    logger.info("Starting ParakaleoMed WebSocket server on port 6789...")
    server = await websockets.serve(handle_client, "0.0.0.0", 6789)
    logger.info("ParakaleoMed WebSocket server running on ws://0.0.0.0:6789")
    logger.info("Ready to sync clinic iPads in real-time!")
    return server

if __name__ == "__main__":
    async def main():
        # Start the WebSocket server
        server = await start_server()
        
        # Keep the server running
        await server.wait_closed()
    
    # Run the server
    asyncio.run(main())