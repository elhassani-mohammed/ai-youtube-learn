import streamlit as st

from ai_service import (
    chat_with_ai,
    create_groq_client,
    generate_professional_podcast_script,
    generate_summary_and_quiz,
)
from config import (
    APP_SUBTITLE,
    APP_TITLE,
    FOOTER_MARKDOWN,
    LANGUAGES,
    PAGE_CONFIG,
    PODCAST_STYLES,
)
from state import clear_chat_history, init_session_state, reset_video_state
from youtube_service import extract_video_id, fetch_transcript, is_youtube_url, search_youtube_videos


def save_api_keys(youtube_key: str, groq_key: str):
    st.session_state.youtube_api_key = youtube_key
    st.session_state.groq_api_key = groq_key
    st.session_state.client = create_groq_client(groq_key)
    st.success("✅ API Keys saved!")


def select_video(video: dict):
    st.session_state.selected_video = video
    reset_video_state()
    st.rerun()


def render_progress():
    st.header("📊 Your Progress")
    st.metric("Videos Watched", st.session_state.user_progress["videos_watched"])
    st.metric("Quizzes Taken", st.session_state.user_progress["quizzes_taken"])
    if st.session_state.user_progress["quizzes_taken"] > 0:
        avg_score = (
            st.session_state.user_progress["total_score"]
            / st.session_state.user_progress["quizzes_taken"]
        )
        st.metric("Average Score", f"{avg_score:.1f}%")


def render_sidebar():
    with st.sidebar:
        st.header("🔑 API Keys")
        st.caption(
            "Get a YouTube API key from "
            "[Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com)"
        )
        st.caption(
            "Get a Groq API key from "
            "[Groq Console](https://console.groq.com/keys)"
        )
        youtube_key = st.text_input(
            "YouTube API Key:",
            value=st.session_state.youtube_api_key,
            type="password",
            help="Get from Google Cloud Console",
        )
        groq_key = st.text_input(
            "Groq API Key:",
            value=st.session_state.groq_api_key,
            type="password",
            help="Get from Groq Cloud Console",
        )

        if st.button("Save API Keys", use_container_width=True):
            save_api_keys(youtube_key, groq_key)

        if st.session_state.youtube_api_key and st.session_state.groq_api_key:
            st.success("✅ API Keys configured")
        else:
            st.warning("⚠️ Please enter both API keys")

        st.divider()
        st.header("🔍 Search Videos")
        search_query = st.text_input(
            "Search for educational videos or paste YouTube URL:"
        )

        if st.button("Search / Load Video", use_container_width=True):
            if not st.session_state.youtube_api_key:
                st.error("Please set YouTube API key first")
            elif search_query:
                if is_youtube_url(search_query):
                    video_id = extract_video_id(search_query)
                    if video_id:
                        select_video({"id": video_id, "title": "YouTube Video"})
                    else:
                        st.error("Could not extract video ID from URL")
                else:
                    with st.spinner("Searching..."):
                        try:
                            st.session_state.search_results = search_youtube_videos(
                                search_query,
                                st.session_state.youtube_api_key,
                            )
                        except Exception as exc:
                            st.error(f"Error searching videos: {exc}")

        if st.session_state.search_results:
            st.subheader("Search Results")
            for video in st.session_state.search_results:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(video["thumbnail"], width=80)
                    with col2:
                        label = (
                            f"{video['title'][:50]}..."
                            if len(video["title"]) > 50
                            else video["title"]
                        )
                        if st.button(label, key=video["id"], use_container_width=True):
                            select_video(video)
                    st.markdown(f"*{video['channel']}*")
                    st.divider()

        render_progress()


def ensure_client():
    if st.session_state.client is None and st.session_state.groq_api_key:
        st.session_state.client = create_groq_client(st.session_state.groq_api_key)


def load_selected_video_content(video_id: str):
    with st.spinner("🔄 Loading video content..."):
        transcript = fetch_transcript(video_id, st.session_state.youtube_api_key)
        if transcript:
            st.session_state.transcript = transcript
            summary, quiz, topic = generate_summary_and_quiz(
                transcript,
                st.session_state.client,
            )
            if summary and quiz:
                st.session_state.summary = summary
                st.session_state.quiz = quiz
                st.session_state.video_topic = topic
                st.session_state.user_progress["videos_watched"] += 1
                st.rerun()


def render_chat_panel():
    st.subheader("💬 AI Chat")
    chat_container = st.container(height=400)

    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])

    user_input = st.chat_input("Ask about the video...")
    if user_input and st.session_state.transcript and st.session_state.client:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_with_ai(
                    user_input,
                    st.session_state.transcript,
                    st.session_state.chat_history,
                    st.session_state.client,
                )
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response}
                )
        st.rerun()
    elif user_input and not st.session_state.client:
        st.error("Please set Groq API key first")
    elif user_input and not st.session_state.transcript:
        st.error("Please load a video first")

    with st.expander("⚙️ Chat Options"):
        if st.button("Clear Chat History", use_container_width=True):
            clear_chat_history()
            st.rerun()


def render_summary_tab():
    st.subheader("AI Summary")
    if st.session_state.video_topic:
        st.info(f"📌 Topic: {st.session_state.video_topic}")
    st.markdown(st.session_state.summary)


def render_quiz_tab():
    st.subheader("Quiz")
    if not st.session_state.quiz:
        st.info("Quiz generation in progress...")
        return

    if st.session_state.video_topic:
        st.info(f"📌 Topic: {st.session_state.video_topic} - Test your understanding!")
    else:
        st.info("📌 Quiz based on the video content")

    with st.form("quiz_form"):
        user_answers = {}
        for index, question in enumerate(st.session_state.quiz):
            st.markdown(f"**Q{index + 1}:** {question['question']}")
            user_answers[index] = st.radio(
                "Choose:",
                question["options"],
                key=f"q_{index}",
                label_visibility="collapsed",
            )
            st.divider()

        if st.form_submit_button("Submit", use_container_width=True):
            score = sum(
                1
                for index, question in enumerate(st.session_state.quiz)
                if user_answers[index][0] == question["correct"]
            )
            percentage = (score / len(st.session_state.quiz)) * 100
            st.metric("Score", f"{score}/{len(st.session_state.quiz)}")

            st.session_state.user_progress["quizzes_taken"] += 1
            st.session_state.user_progress["total_score"] += percentage

            if percentage >= 80:
                st.balloons()
                st.success("🎉 Excellent! You've mastered this topic!")
            elif percentage >= 60:
                st.info("👍 Good job! Review the summary to improve further.")
            else:
                st.warning("📚 Keep learning! Try reviewing the video again.")


def render_podcast_tab(video: dict):
    st.subheader("🎙️ Create Professional Podcast Script")
    if not st.session_state.client:
        st.error("⚠️ Please set your Groq API key in the sidebar to generate podcasts.")
        return

    col_config1, col_config2 = st.columns(2)
    with col_config1:
        default_index = list(LANGUAGES.keys()).index(st.session_state.podcast_language)
        selected_language = st.selectbox(
            "🌍 Podcast Language",
            options=list(LANGUAGES.keys()),
            index=default_index,
            help="The AI will create the podcast in this language",
        )
        style_index = PODCAST_STYLES.index(st.session_state.podcast_style)
        podcast_style = st.selectbox(
            "🎭 Professional Style",
            options=PODCAST_STYLES,
            index=style_index,
            help="Choose the professional style for your podcast",
        )

    with col_config2:
        st.markdown("### 📝 Script Settings")
        duration = st.slider("⏱️ Target Duration (minutes)", 3, 15, 8)
        st.caption(f"AI will create a {duration}-minute professional script")
        st.checkbox("Include Key Takeaways", value=True)

    st.divider()
    if st.button(
        "📝 Generate Professional Podcast Script",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.is_generating_podcast,
    ):
        st.session_state.is_generating_podcast = True
        st.session_state.podcast_language = selected_language
        st.session_state.podcast_style = podcast_style
        try:
            with st.spinner("📝 Getting video transcript..."):
                with st.spinner("🎙️ Creating professional podcast script..."):
                    script, error = generate_professional_podcast_script(
                        video["id"],
                        selected_language,
                        st.session_state.youtube_api_key,
                        st.session_state.client,
                        podcast_style.lower(),
                    )
            if script:
                st.session_state.podcast_script = script
                st.success("✅ Professional Podcast Script Generated!")
            else:
                st.error(f"❌ {error}")
        except Exception as exc:
            st.error(f"❌ Error: {str(exc)[:100]}")
        st.session_state.is_generating_podcast = False
        st.rerun()

    st.divider()
    if st.session_state.podcast_script:
        st.subheader("📄 Your Professional Podcast Script")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Language", st.session_state.podcast_language)
        with col_info2:
            st.metric("Style", st.session_state.podcast_style)
        with col_info3:
            word_count = len(st.session_state.podcast_script.split())
            est_time = word_count // 150
            st.metric("Est. Duration", f"{max(est_time, 2)} min")

        st.text_area(
            "AI-Generated Script:",
            st.session_state.podcast_script,
            height=400,
        )

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.download_button(
                label="📥 Download Script (TXT)",
                data=st.session_state.podcast_script,
                file_name=f"podcast_script_{video['id'][:8]}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_dl2:
            st.download_button(
                label="📥 Download Script (MD)",
                data=f"# Podcast Script\n\n{st.session_state.podcast_script}",
                file_name=f"podcast_script_{video['id'][:8]}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_dl3:
            if st.button("🔄 Create New", use_container_width=True):
                st.session_state.podcast_script = ""
                st.rerun()
    elif not st.session_state.is_generating_podcast:
        st.info(
            """
            **🎙️ Professional Podcast Script Generator**

            **What it does:**
            - **Deep Content Analysis**: AI truly understands the video
            - **Professional Script**: Creates engaging, structured podcast content
            - **Multilingual**: Supports 10+ languages with natural idioms
            - **Multiple Styles**: Educational, Conversational, Storytelling, News

            **Why it's better:**
            - Not just reading transcript – it understands the concepts
            - Creates professional narrative flow
            - Adapts to your audience level
            - Includes thought-provoking questions

            **Perfect for:**
            - Educators creating audio lessons
            - Content creators repurposing videos
            - Students reviewing material
            - Language learning practice
            """
        )

        st.subheader("🚀 Quick Templates")
        template_cols = st.columns(4)
        with template_cols[0]:
            if st.button("🎓 Educational", use_container_width=True):
                st.session_state.podcast_language = "English"
                st.rerun()
        with template_cols[1]:
            if st.button("💬 Conversational", use_container_width=True):
                st.session_state.podcast_language = "English"
                st.rerun()
        with template_cols[2]:
            if st.button("📚 Storytelling", use_container_width=True):
                st.session_state.podcast_language = "English"
                st.rerun()
        with template_cols[3]:
            if st.button("🌍 Multilingual", use_container_width=True):
                st.session_state.podcast_language = "Spanish"
                st.rerun()


def render_video_content():
    if st.session_state.selected_video is None:
        st.info(
            "👈 Search for videos in the sidebar or paste a YouTube URL in the search box"
        )
        return

    ensure_client()
    video = st.session_state.selected_video
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📺 " + video.get("title", "Video"))
        st.video(f"https://www.youtube.com/watch?v={video['id']}")

        if not st.session_state.transcript and st.session_state.client:
            try:
                load_selected_video_content(video["id"])
            except Exception as exc:
                st.error(f"Error generating content: {exc}")
        elif not st.session_state.client:
            st.warning("Please set your Groq API key in the sidebar")

    with col2:
        render_chat_panel()

    if st.session_state.summary:
        st.divider()
        tab1, tab2, tab3 = st.tabs(
            ["📝 Summary", "🎯 Quiz", "🎙️ Professional Podcast"]
        )
        with tab1:
            render_summary_tab()
        with tab2:
            render_quiz_tab()
        with tab3:
            render_podcast_tab(video)

    st.divider()
    if st.button("← Search Another Video", use_container_width=True):
        st.session_state.selected_video = None
        reset_video_state()
        st.rerun()


def main():
    st.set_page_config(**PAGE_CONFIG)
    init_session_state()
    st.title(APP_TITLE)
    st.markdown(APP_SUBTITLE)
  
    render_sidebar()
    render_video_content()
    st.divider()
    st.markdown(FOOTER_MARKDOWN)


if __name__ == "__main__":
    main()
