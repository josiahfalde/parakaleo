
#!/bin/bash
cd /home/pi/parakaleoMed

# Wait for network to be ready
sleep 10

# Get and log the Pi's IP address for easy access
IP=$(hostname -I | awk '{print $1}')
echo "ParakaleoMed starting at: http://$IP:5000" >> /home/pi/startup.log
echo "$(date): ParakaleoMed started at IP $IP" >> /home/pi/startup.log

# Start the app
python3 -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
