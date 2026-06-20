import streamlit as st


SESSION_DEFAULTS = {
    "youtube_api_key": "",
    "groq_api_key": "",
    "client": None,
    "selected_video": None,
    "transcript": "",
    "summary": "",
    "quiz": [],
    "chat_history": [],
    "user_progress": {
        "videos_watched": 0,
        "quizzes_taken": 0,
        "total_score": 0,
    },
    "podcast_script": "",
    "is_generating_podcast": False,
    "podcast_language": "English",
    "podcast_style": "Educational",
    "video_topic": "",
    "search_results": [],
}


def init_session_state():
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_video_state():
    st.session_state.transcript = ""
    st.session_state.summary = ""
    st.session_state.quiz = []
    st.session_state.chat_history = []
    st.session_state.podcast_script = ""
    st.session_state.is_generating_podcast = False
    st.session_state.video_topic = ""


def clear_chat_history():
    st.session_state.chat_history = []
