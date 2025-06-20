@echo off
echo Starting ParakaleoMed...
python -m streamlit run app.py --server.port 8501 --server.headless true
pause
