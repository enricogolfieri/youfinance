"""YouTube transcript analysis agent"""

import modules.logger as logger
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from modules.agents.base_agent import Agent
from modules.cache import Cache
from modules.mongodb_cache import MongoDBCache


# Prompt for analyzing transcripts
TRANSCRIPT_ANALYSIS_PROMPT = """Analyze this YouTube video transcript and extract stock investment information.

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


class YouTubeAgent(Agent):
    """Agent for analyzing YouTube channel transcripts"""

    def __init__(self, ai_engine):
        super().__init__(ai_engine)
        # Keep file-based cache for transcripts (text data)
        self.cache = Cache(cache_dir="cache/youtube_transcripts", file_extension=".txt")
        # Use MongoDB for stock analysis (structured data with aggregations)
        self.mongodb = MongoDBCache()

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

    def get_video_metadata(self, video_id):
        """
        Get video metadata including publish date

        Returns:
            tuple: (success: bool, metadata: dict or error_message: str)
        """
        try:
            ydl_opts = {
                "quiet": True,
            }

            video_url = f"https://youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Fetching metadata for video: {video_id}")
                info = ydl.extract_info(video_url, download=False)

                metadata = {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "upload_date": info.get("upload_date"),  # Format: YYYYMMDD
                    "description": info.get("description"),
                    "uploader": info.get("uploader"),
                    "duration": info.get("duration"),
                }

                logger.info(f"Metadata fetched for {video_id}")
                return True, metadata

        except Exception as e:
            logger.error(f"Error fetching video metadata: {str(e)}")
            return False, f"Error fetching metadata: {str(e)}"

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

    def analyze_transcript(self, video_url, video_title, transcript):
        """
        Analyze transcript for stock mentions and recommendations (with caching)

        Args:
            video_url: YouTube video URL
            video_title: Video title
            transcript: Video transcript text

        Returns:
            tuple: (success: bool, analysis: dict or error_message: str)
        """
        # Check if analysis already exists in MongoDB
        success, existing_analysis = self.mongodb.get_analysis_by_video_url(video_url)
        if success and existing_analysis:
            logger.info(f"Analysis found in MongoDB for video: {video_url}")
            return True, existing_analysis

        # No existing analysis - run AI analysis
        prompt = TRANSCRIPT_ANALYSIS_PROMPT.format(
            video_title=video_title,
            transcript=transcript,
        )

        success, analysis = self.ask(prompt, max_tokens=8192, expect_json=True)

        return success, analysis

    def store_analysis(self, video_url, video_title, video_date, analysis):
        """
        Store analysis results for stocks mentioned

        Args:
            video_url: YouTube video URL
            video_title: Video title
            video_date: Video publication date (ISO format string)
            analysis: Analysis dict with stocks_mentioned

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            stocks_mentioned = analysis.get("stocks_mentioned", [])

            if not stocks_mentioned:
                return True, "No stocks to store"

            # Store each stock mention in MongoDB
            stored_count = 0
            for stock in stocks_mentioned:
                symbol = stock.get("symbol", "").upper()
                if not symbol:
                    continue

                success, msg = self.mongodb.store_analysis(
                    symbol=symbol,
                    video_url=video_url,
                    video_title=video_title,
                    video_date=video_date,
                    recommendation=stock.get("recommendation"),
                    confidence=stock.get("confidence"),
                    reasons=stock.get("reasons", []),
                    summary=analysis.get("summary", ""),
                )

                if success and "stored successfully" in msg.lower():
                    stored_count += 1

            logger.info(f"Stored analysis for {stored_count} stocks")
            if stored_count > 0:
                return True, f"Stored {stored_count} stock mention(s)"
            else:
                return True, "All mentions already exist (no duplicates)"

        except Exception as e:
            logger.error(f"Error storing analysis: {str(e)}")
            return False, f"Error storing: {str(e)}"

    def get_all_analyzed_stocks(self):
        """
        Get list of all stocks that have been analyzed

        Returns:
            list: Stock symbols
        """
        return self.mongodb.get_all_symbols()

    def get_stock_analysis(self, symbol):
        """
        Get all analysis mentions for a stock

        Returns:
            tuple: (success: bool, mentions: list or error_message)
        """
        return self.mongodb.get_stock_analysis(symbol)

    def remove_mention(self, symbol, video_url):
        """
        Remove a specific mention from a stock's analysis

        Args:
            symbol: Stock symbol
            video_url: Video URL to identify which mention to remove

        Returns:
            tuple: (success: bool, message: str)
        """
        return self.mongodb.remove_analysis(symbol, video_url)

    def get_portfolio(self):
        """
        Get portfolio summary with aggregated data

        Returns:
            tuple: (success: bool, portfolio data or error_message)
        """
        return self.mongodb.get_portfolio()
