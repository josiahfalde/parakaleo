import streamlit as st
import time

def show_loading_screen():
    """Display loading screen with Parakaleo logo"""
    
    # Load logo
    with open("parakaleo_logo.svg", "r") as f:
        logo_svg = f.read()
    
    # Create loading screen
    placeholder = st.empty()
    
    with placeholder.container():
        # Center the logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f'<div style="text-align: center; margin-top: 100px;">{logo_svg}</div>', unsafe_allow_html=True)
            st.markdown('<h2 style="text-align: center; margin-top: 20px;">ParakaleoMed</h2>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; color: #666;">Loading...</p>', unsafe_allow_html=True)
    
    # Simulate loading time
    time.sleep(2)
    
    # Clear the loading screen
    placeholder.empty()