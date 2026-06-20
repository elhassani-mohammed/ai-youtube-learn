import json
import re

from groq import Groq

from config import GROQ_MODEL
from youtube_service import fetch_transcript


def create_groq_client(api_key: str):
    if not api_key:
        return None
    return Groq(api_key=api_key)


def extract_video_topic(transcript: str, client) -> str:
    """Extract the main subject area from the transcript."""
    try:
        prompt = f"""Analyze the following video transcript and identify the primary topic or subject area.

Transcript:
{transcript[:2000]}

Return only the topic name (e.g., "English Grammar", "Machine Learning", "Cooking", "Personal Finance", etc.). Be specific but concise."""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
            temperature=0.3,
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "General Knowledge"


def generate_summary_and_quiz(transcript: str, client):
    """Generate a learning summary and topic-based quiz from the transcript."""
    summary_prompt = f"""Based on the following video transcript, provide a comprehensive summary highlighting the key points and main takeaways:

Transcript:
{transcript[:4000]}

Provide a clear, structured summary."""

    summary_response = client.chat.completions.create(
        messages=[{"role": "user", "content": summary_prompt}],
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=1000,
    )
    summary = summary_response.choices[0].message.content

    topic = extract_video_topic(transcript, client)
    quiz_prompt = f"""You are creating a quiz to test understanding of the topic "{topic}" based on the following video transcript.

The quiz should:
- Test conceptual understanding of the topic, not just recall of transcript details.
- Include questions that apply knowledge, analyze situations, or evaluate ideas.
- Each question should be multiple-choice with 4 options (A, B, C, D).
- Provide the correct answer as the letter (A, B, C, or D).

Generate 5 multiple-choice questions in JSON format:
[
    {{
        "question": "question text",
        "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
        "correct": "A"
    }}
]

Return ONLY the JSON array, no other text.

Transcript for context:
{transcript[:3000]}"""

    quiz_response = client.chat.completions.create(
        messages=[{"role": "user", "content": quiz_prompt}],
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=1500,
    )

    quiz_text = quiz_response.choices[0].message.content
    json_match = re.search(r"\[.*\]", quiz_text, re.DOTALL)
    quiz = json.loads(json_match.group()) if json_match else []
    return summary, quiz, topic


def chat_with_ai(user_message: str, transcript: str, chat_history: list, client) -> str:
    """Chat about the video using the transcript as grounding context."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful learning assistant. Answer questions based on "
                f"this video transcript: {transcript[:3000]}"
            ),
        }
    ]

    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        messages=messages,
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content


def analyze_video_content(transcript: str, client):
    """Perform deeper analysis of the video's main ideas."""
    analysis_prompt = f"""As a professional content analyst, deeply analyze this video transcript to understand its true essence:

Transcript:
{transcript[:3000]}

Provide a structured analysis with:
1. CORE CONCEPT: What is the central idea or theme?
2. KEY ARGUMENTS: Main points made by the speaker
3. EVIDENCE/EXAMPLES: Supporting evidence or examples used
4. AUDIENCE: Who is this content for?
5. EXPERTISE LEVEL: Beginner, Intermediate, or Advanced?
6. EMOTIONAL TONE: Inspirational, Analytical, Practical, etc.
7. UNIQUE INSIGHTS: What makes this content valuable?

Format as a structured analysis for a podcast producer."""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": analysis_prompt}],
        model=GROQ_MODEL,
        temperature=0.3,
        max_tokens=1500,
    )
    return response.choices[0].message.content


def create_professional_podcast_script(
    analysis: str,
    language: str,
    client,
    style: str = "professional",
):
    """Create a podcast script from a prior content analysis."""
    if style == "educational":
        role = "an award-winning educational podcast host"
    elif style == "conversational":
        role = "a skilled conversationalist and interviewer"
    elif style == "storytelling":
        role = "a master storyteller and narrative expert"
    else:
        role = "a professional podcast producer and host"

    prompt = f"""You are {role}. Based on the following deep analysis of a YouTube video, create a professional podcast episode.

DEEP ANALYSIS OF VIDEO CONTENT:
{analysis}

Now create a {style} podcast script in {language} that:
1. STARTS with an engaging hook that captures the essence
2. EXPLORES the key concepts with insight and context
3. PROVIDES valuable takeaways that listeners can apply
4. ENDS with a memorable conclusion

The script should:
- Sound like a professional podcast, not a lecture
- Include natural pauses and conversational markers
- Have proper podcast structure (intro, segments, outro)
- Be approximately 800-1000 words
- Use appropriate {language} idioms and expressions
- Include thought-provoking questions for the listener

Write the podcast script in {language} as if you're speaking to an intelligent audience."""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def generate_professional_podcast_script(
    video_id: str,
    language: str,
    api_key: str,
    client,
    style: str = "professional",
):
    """Generate a professional podcast script for the selected video."""
    transcript = fetch_transcript(video_id, api_key)
    if not transcript or "Unable" in transcript:
        return None, "Could not get video content"

    analysis = analyze_video_content(transcript, client)
    if not analysis:
        return None, "Could not analyze video content"

    script = create_professional_podcast_script(analysis, language, client, style)
    if not script:
        return None, "Could not create professional podcast script"

    return script, None
