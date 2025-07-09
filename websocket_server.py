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

async def handle_client(websocket):
    """Handle a new WebSocket client connection"""
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    logger.info(f"New client connected from {client_ip}. Total clients: {len(connected_clients)}")
    
    # Send periodic pings to maintain connection
    async def send_periodic_ping():
        try:
            while websocket in connected_clients:
                await asyncio.sleep(30)  # Ping every 30 seconds
                if websocket in connected_clients:
                    try:
                        await websocket.send("ping")
                        logger.debug(f"Sent ping to {client_ip}")
                    except:
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Ping task error for {client_ip}: {e}")
    
    # Start ping task
    ping_task = asyncio.create_task(send_periodic_ping())
    
    try:
        # Send welcome message
        await websocket.send(f"welcome:ParakaleoMed_sync_server")
        
        async for message in websocket:
            # Handle ping/pong messages
            if message.startswith("ping:") or message == "ping":
                await websocket.send("pong")
                logger.debug(f"Responded to ping from {client_ip}")
                continue
            elif message.startswith("pong:") or message == "pong":
                logger.debug(f"Received pong from {client_ip}")
                continue
            
            # Broadcast message to all other connected clients
            if connected_clients:
                # Parse message and add timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                broadcast_message = f"{message}"
                
                # Log the message type for debugging
                if "new_patient" in message or "new_name_registered" in message or "new_family_registered" in message:
                    logger.info(f"🚨 PATIENT REGISTRATION MESSAGE RECEIVED: {message}")
                
                # Send to all clients except sender
                disconnected = set()
                broadcast_count = 0
                for client in connected_clients:
                    if client != websocket:
                        try:
                            await client.send(broadcast_message)
                            broadcast_count += 1
                        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
                            disconnected.add(client)
                        except Exception as e:
                            logger.warning(f"Error sending to client: {e}")
                            disconnected.add(client)
                
                # Remove disconnected clients
                connected_clients.difference_update(disconnected)
                
                logger.info(f"Broadcasted: {message} to {broadcast_count} clients (total connected: {len(connected_clients)})")
                
    except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
        logger.info(f"Client {client_ip} connection closed normally")
    except Exception as e:
        logger.error(f"Error handling client {client_ip}: {e}")
    finally:
        # Cancel ping task
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass
        
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
    
    # Enhanced server configuration for offline stability
    server = await websockets.serve(
        handle_client, 
        "0.0.0.0", 
        6789,
        # Increase timeouts for offline/slow connections
        ping_timeout=60,  # Wait 60 seconds for ping response
        ping_interval=30,  # Send ping every 30 seconds
        close_timeout=10,  # Wait 10 seconds for close handshake
        # Keep connections alive longer in offline environment
        max_size=2**20,   # 1MB max message size
        max_queue=32,     # Queue up to 32 messages per client
    )
    
    logger.info("ParakaleoMed WebSocket server running on ws://0.0.0.0:6789")
    logger.info("Enhanced for offline iPad connectivity on Pi hotspot network")
    logger.info("Server configuration: ping_interval=30s, ping_timeout=60s")
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
