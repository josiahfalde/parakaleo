
#!/bin/bash
cd /home/pi/parakaleoMed
python3 -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
