
#!/bin/bash
cd /home/pi/parakaleoMed

# Wait for network to be ready
sleep 10

# Get and log the Pi's IP address for easy access
IP=$(hostname -I | awk '{print $1}')
echo "ParakaleoMed starting at: http://$IP:5000" >> /home/pi/startup.log
echo "$(date): ParakaleoMed started at IP $IP" >> /home/pi/startup.log

# If running as hotspot, also log the hotspot IP
if ip addr show wlan0 | grep -q "192.168.4.1"; then
    echo "WiFi Hotspot Active: ParakaleoMed-Clinic" >> /home/pi/startup.log
    echo "Hotspot URL: http://192.168.4.1:5000" >> /home/pi/startup.log
fi

# Start the app
python3 -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
