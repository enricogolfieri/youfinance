"""YouTube transcript analysis agent"""

import json
import modules.logger as logger
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from modules.cache import Cache


class YouTubeAgent:
    """Agent for analyzing YouTube channel transcripts"""

    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.cache = Cache(cache_dir="cache/youtube_transcripts", file_extension=".txt")

    def get_channel_videos(self, channel_url, max_videos=5):
        """
        Get recent videos from a YouTube channel

        Returns:
            tuple: (success: bool, videos: list or error_message: str)
        """
        try:
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "playlistend": max_videos,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Fetching videos from channel: {channel_url}")
                info = ydl.extract_info(channel_url, download=False)

                if "entries" not in info:
                    return False, "No videos found in channel"

                videos = []
                for entry in info["entries"][:max_videos]:
                    if entry:
                        videos.append(
                            {
                                "id": entry.get("id"),
                                "title": entry.get("title"),
                                "url": entry.get("url")
                                or f"https://youtube.com/watch?v={entry.get('id')}",
                            }
                        )

                logger.info(f"Found {len(videos)} videos")
                return True, videos

        except Exception as e:
            logger.error(f"Error fetching channel videos: {str(e)}")
            return False, f"Error fetching videos: {str(e)}"

    def _fetch_transcript_from_youtube(self, video_id):
        """
        Fetch transcript from YouTube API (called by cache on miss)

        Returns:
            tuple: (success: bool, transcript: str or error_message: str)
        """
        try:
            logger.info(f"Fetching transcript from YouTube API: {video_id}")
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id)

            # Combine all text
            full_transcript = " ".join([item.text for item in transcript_list])

            logger.info(f"Transcript fetched: {len(full_transcript)} characters")
            return True, full_transcript

        except Exception as e:
            logger.error(f"Error fetching transcript: {str(e)}")
            return False, f"Error fetching transcript: {str(e)}"

    def get_transcript(self, video_id):
        """
        Get transcript for a YouTube video (with caching)

        Returns:
            tuple: (success: bool, transcript: str or error_message: str)
        """
        return self.cache.get(
            video_id, fetch_callback=self._fetch_transcript_from_youtube
        )

    def save_transcript(self, video_id, transcript):
        """
        Manually save a transcript to cache

        Returns:
            tuple: (success: bool, message: str)
        """
        return self.cache.set(video_id, transcript)

    def analyze_transcript(self, video_title, transcript):
        """
        Analyze transcript for stock mentions and recommendations

        Returns:
            tuple: (success: bool, analysis: dict or error_message: str)
        """
        prompt = f"""Analyze this YouTube video transcript and extract stock investment information.

VIDEO TITLE: {video_title}

TRANSCRIPT:
{transcript}  

Extract and provide as JSON ONLY (no markdown, no extra text):
{{
    "stocks_mentioned": [
        {{
            "symbol": "STOCK_SYMBOL",
            "recommendation": "BUY/SELL/HOLD",
            "confidence": "HIGH/MEDIUM/LOW",
            "reasons": ["reason1", "reason2"]
        }}
    ],
    "other_insights": ["insight1", "insight2"],
    "summary": "Brief summary of video content"
}}

If no stocks are mentioned, return empty stocks_mentioned array.
"""

        try:
            response = self.ai_engine.send(prompt, max_tokens=6000, temperature=0.3)

            # Extract JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                return False, "AI response did not contain valid JSON"

            json_str = response[json_start:json_end]
            analysis = json.loads(json_str)

            logger.info(
                f"Transcript analyzed: {len(analysis.get('stocks_mentioned', []))} stocks found"
            )
            return True, analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return False, f"AI returned invalid JSON: {str(e)}"
        except Exception as e:
            logger.error(f"Error during transcript analysis: {str(e)}")
            return False, f"Error during analysis: {str(e)}"
