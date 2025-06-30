"""Database connection and configuration."""

import os
import streamlit as st

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

def get_supabase_config():
    """Get Supabase configuration from environment."""
    return {
        'url': os.getenv('SUPABASE_URL', ''),
        'key': os.getenv('SUPABASE_ANON_KEY', ''),
        'available': SUPABASE_AVAILABLE
    }

def create_supabase_client():
    """Create and return Supabase client if available."""
    config = get_supabase_config()
    
    if not config['available']:
        return None, "Supabase library not installed"
    
    if not config['url'] or not config['key']:
        return None, "Supabase credentials not configured"
    
    try:
        client = create_client(config['url'], config['key'])
        return client, None
    except Exception as e:
        return None, f"Failed to connect to Supabase: {str(e)}"

def get_database_status(use_supabase: bool):
    """Get database connection status without displaying UI."""
    if use_supabase:
        return {
            'status': 'success',
            'persistent': True,
            'message': 'Connected to Supabase - Transcriptions saved permanently',
            'need_refresh': False
        }
    else:
        return {
            'status': 'warning',
            'persistent': False,
            'message': 'Using temporary storage - Transcriptions will be lost on refresh',
            'need_refresh': True
        }

def display_database_status(use_supabase: bool):
    """Display database connection status (legacy function)."""
    status = get_database_status(use_supabase)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if status['status'] == 'success':
            st.markdown(f'<div class="success-box">✅ {status["message"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warning-box">⚠️ {status["message"]}</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()