import re

import requests


def extract_video_id(url_or_id: str) -> str:
    """Extract a YouTube video ID from a full URL or return the raw ID."""
    if "youtube.com" in url_or_id or "youtu.be" in url_or_id:
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/)([0-9A-Za-z_-]{11})",
            r"youtu\.be\/([0-9A-Za-z_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
    return url_or_id


def is_youtube_url(text: str) -> bool:
    return "youtube.com" in text or "youtu.be" in text


def search_youtube_videos(query: str, api_key: str, max_results: int = 10):
    """Search for YouTube videos using the YouTube Data API."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    videos = []
    for item in data.get("items", []):
        videos.append(
            {
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "channel": item["snippet"]["channelTitle"],
            }
        )

    return videos


def get_video_description(video_id: str, api_key: str) -> str:
    """Get the title and description when a transcript is unavailable."""
    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet&id={video_id}&key={api_key}"
    )
    response = requests.get(url, timeout=30)
    data = response.json()

    if "items" in data and data["items"]:
        snippet = data["items"][0]["snippet"]
        title = snippet.get("title", "")
        description = snippet.get("description", "")
        return f"Title: {title}\n\nDescription: {description}"

    return "Unable to fetch video content. Please try another video."


def fetch_transcript(video_id: str, api_key: str) -> str:
    """Fetch a transcript from the video page or fall back to the description."""
    try:
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(watch_url, timeout=30)

        if '"captionTracks"' in response.text:
            start = response.text.find('"captionTracks"')
            end = response.text.find("]", start) + 1
            caption_data = response.text[start:end]

            base_url_match = re.search(r'"baseUrl":"(.*?)"', caption_data)
            if base_url_match:
                caption_url = base_url_match.group(1).replace("\\u0026", "&")
                caption_response = requests.get(caption_url, timeout=30)
                matches = re.findall(r"<text[^>]*>(.*?)</text>", caption_response.text)

                if matches:
                    transcript_lines = []
                    for line in matches:
                        clean_line = (
                            line.replace("&#39;", "'")
                            .replace("&quot;", '"')
                            .replace("&amp;", "&")
                            .replace("\\n", " ")
                        )
                        transcript_lines.append(clean_line)
                    return " ".join(transcript_lines)

        return get_video_description(video_id, api_key)
    except Exception:
        return get_video_description(video_id, api_key)
