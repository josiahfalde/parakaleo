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
        # Center the logo only
        st.markdown(f'''
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            width: 100%;
        ">
            <div style="text-align: center;">
                {logo_svg}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Simulate loading time
    time.sleep(2)
    
    # Clear the loading screen
    placeholder.empty()