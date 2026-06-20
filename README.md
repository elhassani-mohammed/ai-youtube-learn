# AI YouTube Learn

`AI YouTube Learn` is a Streamlit app that turns YouTube videos into a guided learning experience with AI summaries, quizzes, chat, and podcast-style script generation.

## 📱 App Link

**Try it here:** [https://ai-youtube-learn.streamlit.app](https://ai-youtube-learn.streamlit.app)



## Features

- Search YouTube videos or paste a direct YouTube URL
- Load transcript-like content from captions or fall back to video description
- Generate an AI summary of the video
- Create a short quiz to test understanding
- Chat with AI about the selected video
- Generate a professional podcast script in multiple styles and languages
- Track simple learning progress across watched videos and quiz scores

## Project Structure

```text
ai-youtube-learn/
|-- app.py
|-- ai_service.py
|-- config.py
|-- requirements.txt
|-- state.py
|-- youtube_service.py
`-- README.md
```

- `app.py`: Streamlit page flow and UI rendering
- `ai_service.py`: Groq-based summary, quiz, topic, chat, and podcast generation
- `config.py`: Shared app configuration and constants
- `state.py`: Session-state defaults and reset helpers
- `youtube_service.py`: YouTube search, URL parsing, and transcript/description retrieval

## Requirements

Install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Run The App

From the `ai-youtube-learn` directory:

```bash
streamlit run app.py
```

## How To Use

1. Get your YouTube API key from [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com) and your Groq API key from [Groq Console](https://console.groq.com/keys).
2. Save the keys.
3. Search for an educational video or paste a YouTube URL.
4. Select a video to load it in the app.
5. Review the AI summary.
6. Take the quiz and check your score.
7. Ask follow-up questions in the chat panel.
8. Generate a podcast script if you want an audio-style study version.

## Notes

- The app uses the YouTube Data API for video search and metadata fallback.
- Transcript retrieval is based on available caption data from the YouTube page and may not work for every video.
- Quiz and podcast generation depend on Groq responses being valid and relevant to the video content.
- The podcast generator currently produces scripts, not audio files.

## Example Use Cases

```text
- Learn from a programming tutorial and quiz yourself afterward
- Summarize a business talk and ask follow-up questions in chat
- Turn a lecture video into a podcast-style revision script
```
