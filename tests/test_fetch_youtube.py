import unit_test as u

from modules.agents.youtube_agent import YouTubeAgent


@u.unit_test("Test YouTube Channel Videos Fetch")
def test_youtube_fetch():
    """Test fetching videos from a YouTube channel"""

    # YouTubeAgent doesn't need AI engine for get_channel_videos
    youtube_agent = YouTubeAgent(ai_engine=None)

    # Test with a popular finance YouTube channel
    # Example: Meet Kevin channel (finance/investing content)
    test_channel_url = "https://www.youtube.com/@MeetKevin/videos"
    max_videos = 3

    print(f"Testing YouTube channel fetch: {test_channel_url}")
    print(f"Fetching latest {max_videos} videos...")
    print("-" * 60)

    # Test: Get channel videos
    print("\n1. Fetching Channel Videos")
    print("-" * 40)
    success, result = youtube_agent.get_channel_videos(test_channel_url, max_videos)

    if not success:
        print(f"❌ Failed to fetch channel videos: {result}")
        return False

    videos = result
    print(f"✓ Successfully fetched {len(videos)} videos\n")

    # Display video information
    for i, video in enumerate(videos, 1):
        print(f"Video {i}:")
        print(f"  Title: {video.get('title')}")
        print(f"  ID: {video.get('id')}")
        print(f"  URL: {video.get('url')}")
        print()

    print("=" * 60)
    print(f"✓ Channel fetch test completed successfully - found {len(videos)} videos")

    return True


@u.unit_test("Test YouTube Video Transcript Fetch")
def test_youtube_transcript():
    """Test fetching transcript for a specific video"""

    # YouTubeAgent doesn't need AI engine for get_transcript
    youtube_agent = YouTubeAgent(ai_engine=None)

    # Test with a known video that has transcripts
    # Example: Use the first video from a known channel with transcripts
    test_video_id = "dQw4w9WgXcQ"  # Replace with actual finance video ID

    print(f"Testing YouTube transcript fetch for video ID: {test_video_id}")
    print("-" * 60)

    # Test: Get video transcript
    print("\n1. Fetching Video Transcript")
    print("-" * 40)
    success, result = youtube_agent.get_transcript(test_video_id)

    if not success:
        print(f"❌ Failed to fetch transcript: {result}")
        print("\nNote: This video may not have transcripts available.")
        print("Try using a video ID from a channel that has captions enabled.")
        return False

    transcript = result
    print(f"✓ Successfully fetched transcript")
    print(f"  Length: {len(transcript)} characters")
    print(f"  Word count (approx): {len(transcript.split())} words")
    print(f"\n  Preview (first 300 chars):")
    print(f"  {transcript[:300]}...")

    if len(transcript) > 500:
        print(f"\n  Preview (last 200 chars):")
        print(f"  ...{transcript[-200:]}")

    print("\n" + "=" * 60)
    print("✓ Transcript fetch test completed successfully")

    return True


if __name__ == "__main__":
    test_youtube_fetch()
    test_youtube_transcript()
