"""Database models and operations."""

import streamlit as st
from typing import List, Dict, Optional
from .connection import create_supabase_client, get_supabase_config

class TranscriptionDB:
    """Database handler for transcription storage."""
    
    def __init__(self):
        """Initialize database connection."""
        self.supabase_config = get_supabase_config()
        self.supabase, error = create_supabase_client()
        self.use_supabase = self.supabase is not None
        
        if error and self.supabase_config['available']:
            st.error(f"Database connection error: {error}")
        
        # Fallback to session state if Supabase not available
        if not self.use_supabase:
            if 'transcription_history' not in st.session_state:
                st.session_state.transcription_history = []

    def add_transcription(self, transcription: Dict) -> bool:
        """Add a new transcription."""
        if self.use_supabase:
            try:
                data = self.supabase.table('transcriptions').insert({
                    'name': transcription['name'],
                    'filename': transcription['filename'],
                    'date': transcription['date'],
                    'text': transcription['text'],
                    'improved_text': transcription.get('improved_text'),
                    'language': transcription['language'],
                    'output_format': transcription.get('output_format', 'text')
                }).execute()
                return True
            except Exception as e:
                st.error(f"Error saving to Supabase: {str(e)}")
                return False
        else:
            st.session_state.transcription_history.insert(0, transcription)
            return True

    def get_all_transcriptions(self) -> List[Dict]:
        """Get all transcriptions."""
        if self.use_supabase:
            try:
                response = self.supabase.table('transcriptions').select("*").order('created_at', desc=True).execute()
                return response.data
            except Exception as e:
                st.error(f"Error fetching from Supabase: {str(e)}")
                return []
        else:
            return st.session_state.transcription_history

    def delete_transcription(self, transcription_id: str) -> bool:
        """Delete a transcription."""
        if self.use_supabase:
            try:
                self.supabase.table('transcriptions').delete().eq('id', transcription_id).execute()
                return True
            except Exception as e:
                st.error(f"Error deleting from Supabase: {str(e)}")
                return False
        else:
            st.session_state.transcription_history = [
                t for t in st.session_state.transcription_history
                if t.get('id') != transcription_id
            ]
            return True

    def clear_all_transcriptions(self) -> bool:
        """Clear all transcriptions."""
        if self.use_supabase:
            try:
                # Delete all records - be careful with this!
                self.supabase.table('transcriptions').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                return True
            except Exception as e:
                st.error(f"Error clearing Supabase: {str(e)}")
                return False
        else:
            st.session_state.transcription_history = []
            return True

    def search_transcriptions(self, query: str) -> List[Dict]:
        """Search transcriptions by name or content."""
        all_transcriptions = self.get_all_transcriptions()
        if not query:
            return all_transcriptions
        
        query_lower = query.lower()
        return [
            t for t in all_transcriptions
            if query_lower in t.get('name', '').lower() or
               query_lower in t.get('text', '').lower()
        ]

@st.cache_resource
def get_db() -> TranscriptionDB:
    """Get cached database instance."""
    return TranscriptionDB()