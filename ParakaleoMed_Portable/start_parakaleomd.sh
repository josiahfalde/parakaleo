#!/bin/bash
echo "Starting ParakaleoMed..."
python3 -m streamlit run app.py --server.port 8501 --server.headless true
