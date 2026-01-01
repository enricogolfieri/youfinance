import streamlit as st
from modules.agents.ceo_agent import CeoAgent
from modules.agents.dcf_agent import DCFAgent
from modules.agents.youtube_agent import YouTubeAgent
from modules.fetchers.fmp_fetcher import FinancialModelingPrep
from modules.deepseek import DeepSeek, DeepSeekModels
from dotenv import load_dotenv
import modules.key as keys
import modules.logger as logger

logger.init("GUI")

# Initialize clients and agents
engine = DeepSeek(
    deepseek_api_key=keys.DeepSeekKey(),
    deepseek_model=DeepSeekModels.DEEPSEEK_CHAT,
)

fmp_client = FinancialModelingPrep(key=keys.FinancialModelingPrepKey())
ceo_agent = CeoAgent(fmp_client=fmp_client, ai_engine=engine)
dcf_agent = DCFAgent(fmp_client=fmp_client, ai_engine=engine)
youtube_agent = YouTubeAgent(ai_engine=engine)


def main():
    st.set_page_config(page_title="Stock Analysis", page_icon="📈", layout="wide")

    st.title("📈 Stock Analysis Tool")

    # Sidebar for configuration
    st.sidebar.header("API Keys")
    for key in keys.iterate_keys():
        if key.exists():
            st.sidebar.success(f"✅ {key.description}")
        else:
            st.sidebar.error(f"❌ {key.description}")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "👔 CEO Evaluation",
            "💰 DCF Valuation",
            "🎥 YouTube Analysis",
            "📝 Manual Transcript",
        ]
    )

    # TAB 1: CEO Evaluation
    with tab1:
        st.header("CEO Evaluation")

        col1, col2 = st.columns([1, 3])

        with col1:
            symbol = st.text_input(
                "Stock Symbol",
                placeholder="e.g., AAPL, TSLA",
                help="Enter stock ticker",
                key="ceo_symbol",
            ).upper()

            analyze_ceo_button = st.button("🔍 Analyze CEO", type="primary")

        with col2:
            if analyze_ceo_button and symbol:
                st.subheader(f"CEO Analysis for {symbol}")

                with st.spinner("Analyzing CEO..."):
                    success, ceo_result = ceo_agent.run_analysis(symbol)

                if success:
                    ceo_info = ceo_result["ceo_info"]
                    ceo_analysis = ceo_result["analysis"]

                    # CEO Info
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("CEO", ceo_info.get("name", "N/A"))
                        if ceo_info.get("age"):
                            st.write(f"**Age:** {ceo_info['age']}")

                    with col_b:
                        st.metric("Fit Score", f"{ceo_analysis.get('fit_score', 0)}/10")
                        st.write(f"**Level:** {ceo_analysis.get('fit_level', 'N/A')}")

                    with col_c:
                        if ceo_info.get("compensation"):
                            st.metric(
                                "Compensation", f"${ceo_info['compensation']:,.0f}"
                            )
                        st.write(f"**Source:** {ceo_info.get('source', 'N/A')}")

                    st.markdown("---")

                    # Analysis details
                    col_d, col_e = st.columns(2)

                    with col_d:
                        st.write("### 💪 Strengths")
                        for s in ceo_analysis.get("strengths", []):
                            st.write(f"• {s}")

                    with col_e:
                        st.write("### ⚠️ Concerns")
                        for c in ceo_analysis.get("concerns", []):
                            st.write(f"• {c}")

                    st.markdown("---")
                    st.write("### 📝 Summary")
                    st.write(ceo_analysis.get("summary", "No summary available"))

                else:
                    st.error(f"❌ CEO Analysis Failed: {ceo_result}")

    # TAB 2: DCF Valuation
    with tab2:
        st.header("DCF Valuation")

        col1, col2 = st.columns([1, 3])

        with col1:
            symbol_dcf = st.text_input(
                "Stock Symbol",
                placeholder="e.g., AAPL, TSLA",
                help="Enter stock ticker",
                key="dcf_symbol",
            ).upper()

            st.markdown("---")
            st.subheader("YouTube Context (Optional)")

            channel_url = st.text_input(
                "Channel URL",
                placeholder="https://youtube.com/@channel",
                help="Optional: Add context from YouTube channel",
                key="dcf_youtube_channel",
            )

            num_videos = st.slider(
                "Number of videos",
                min_value=1,
                max_value=10,
                value=5,
                help="How many recent videos to analyze",
                key="dcf_num_videos",
            )

            st.markdown("---")
            analyze_dcf_button = st.button("📊 Calculate DCF", type="primary")

        with col2:
            if analyze_dcf_button and symbol_dcf:
                st.subheader(f"DCF Valuation for {symbol_dcf}")

                # Fetch YouTube context if provided
                youtube_context = None
                if channel_url:
                    with st.spinner(f"Fetching {num_videos} videos from YouTube..."):
                        success, videos = youtube_agent.get_channel_videos(
                            channel_url, num_videos
                        )

                        if success:
                            st.info(
                                f"✓ Found {len(videos)} videos, fetching transcripts..."
                            )
                            transcripts = []

                            for video in videos:
                                success, transcript = youtube_agent.get_transcript(
                                    video["id"]
                                )
                                if success:
                                    transcripts.append(
                                        f"Video: {video['title']}\n{transcript}"
                                    )

                            if transcripts:
                                youtube_context = "\n\n---\n\n".join(transcripts)
                                st.success(
                                    f"✓ Fetched {len(transcripts)} transcripts ({len(youtube_context)} chars)"
                                )
                            else:
                                st.warning("No transcripts available from videos")
                        else:
                            st.warning(f"Could not fetch YouTube videos: {videos}")

                # Calculate DCF
                with st.spinner("Calculating DCF valuation..."):
                    success, dcf_result = dcf_agent.run_valuation(
                        symbol_dcf, youtube_context
                    )

                if success:
                    dcf_data = dcf_result["dcf"]
                    ai_assumptions = dcf_result["ai_assumptions"]

                    # Main metrics
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric(
                            "Intrinsic Value", f"${dcf_data['intrinsic_value']:.2f}"
                        )
                    with col_b:
                        st.metric("Current Price", f"${dcf_data['current_price']:.2f}")
                    with col_c:
                        upside = dcf_data["upside_downside"]
                        st.metric(
                            "Upside/Downside", f"{upside:.1f}%", delta=f"{upside:.1f}%"
                        )

                    # Recommendation
                    st.markdown("---")
                    rec = dcf_data["recommendation"]
                    if "Strong Buy" in rec or "Buy" in rec:
                        st.success(f"🟢 **{rec}**")
                    elif "Hold" in rec:
                        st.info(f"🟡 **{rec}**")
                    else:
                        st.warning(f"🔴 **{rec}**")

                    st.markdown("---")

                    # AI Reasoning
                    st.write("### 🤖 AI Reasoning")
                    st.write(ai_assumptions.get("reasoning", "No reasoning available"))

                    # Technical details
                    with st.expander("📊 Technical Details"):
                        assumptions = dcf_data["assumptions"]
                        col_f, col_g = st.columns(2)
                        with col_f:
                            st.write("**Assumptions:**")
                            st.write(f"• WACC: {assumptions['wacc']:.2%}")
                            st.write(
                                f"• FCF Growth Rate: {assumptions['fcf_growth_rate']:.2%}"
                            )
                            st.write(
                                f"• Terminal Growth: {assumptions['terminal_growth_rate']:.2%}"
                            )
                            st.write(f"• Beta: {assumptions['beta']:.2f}")
                        with col_g:
                            st.write("**Valuation Components:**")
                            st.write(
                                f"• Enterprise Value: ${dcf_data['enterprise_value']:,.0f}"
                            )
                            st.write(
                                f"• Terminal Value: ${dcf_data['terminal_value']:,.0f}"
                            )

                else:
                    st.error(f"❌ DCF Valuation Failed: {dcf_result}")

    # TAB 3: YouTube Analysis
    with tab3:
        st.header("YouTube Channel Analysis")

        col1, col2 = st.columns([1, 2])

        with col1:
            channel_url = st.text_input(
                "YouTube Channel URL",
                placeholder="https://youtube.com/@channel",
                help="Enter channel URL",
            )

            num_videos = st.slider("Number of videos", 1, 10, 5)

            analyze_yt_button = st.button("🎥 Analyze Channel", type="primary")

        with col2:
            if analyze_yt_button and channel_url:
                # Step 1: Get videos
                st.subheader("Step 1: Fetching Videos")
                with st.spinner("Getting channel videos..."):
                    success, videos = youtube_agent.get_channel_videos(
                        channel_url, num_videos
                    )

                if not success:
                    st.error(f"❌ Failed to fetch videos: {videos}")
                else:
                    st.success(f"✅ Found {len(videos)} videos")
                    with st.expander("Video List"):
                        for i, video in enumerate(videos, 1):
                            st.write(f"{i}. {video['title']}")

                    st.markdown("---")

                    # Step 2 & 3: Process each video
                    for i, video in enumerate(videos, 1):
                        st.subheader(f"Video {i}/{len(videos)}: {video['title']}")
                        st.write(f"🔗 [Watch on YouTube]({video['url']})")

                        # Step 2: Get transcript
                        st.write("**Step 2: Fetching Transcript**")
                        with st.spinner("Downloading transcript..."):
                            success, transcript = youtube_agent.get_transcript(
                                video["id"]
                            )

                        if not success:
                            st.warning(f"⚠️ Transcript not available: {transcript}")
                            st.markdown("---")
                            continue

                        st.success(
                            f"✅ Transcript downloaded ({len(transcript)} characters)"
                        )
                        with st.expander("View Transcript"):
                            st.text(
                                transcript[:1000] + "..."
                                if len(transcript) > 1000
                                else transcript
                            )

                        # Step 3: AI Analysis
                        st.write("**Step 3: AI Analysis**")
                        with st.spinner("Analyzing with AI..."):
                            success, analysis = youtube_agent.analyze_transcript(
                                video["title"], transcript
                            )

                        if not success:
                            st.error(f"❌ Analysis failed: {analysis}")
                            st.markdown("---")
                            continue

                        st.success("✅ Analysis complete")

                        # Display results
                        st.write("**📋 Summary**")
                        st.write(analysis.get("summary", "No summary available"))

                        # Stock mentions
                        stocks = analysis.get("stocks_mentioned", [])
                        if stocks:
                            st.write(f"**📊 Stocks Mentioned: {len(stocks)}**")
                            for stock in stocks:
                                col_s1, col_s2, col_s3 = st.columns([1, 1, 3])
                                with col_s1:
                                    st.write(f"**{stock.get('symbol')}**")
                                with col_s2:
                                    rec = stock.get("recommendation", "N/A")
                                    conf = stock.get("confidence", "N/A")
                                    color = {
                                        "BUY": "🟢",
                                        "SELL": "🔴",
                                        "HOLD": "🟡",
                                    }.get(rec, "⚪")
                                    st.write(f"{color} {rec}")
                                    st.caption(f"Confidence: {conf}")
                                with col_s3:
                                    st.write("**Reasons:**")
                                    reasons = stock.get("reasons", [])
                                    for reason in reasons:
                                        st.write(f"• {reason}")
                        else:
                            st.info("ℹ️ No stocks mentioned in this video")

                        # Other insights
                        insights = analysis.get("other_insights", [])
                        if insights:
                            with st.expander("💡 Other Insights"):
                                for insight in insights:
                                    st.write(f"• {insight}")

                        st.markdown("---")

    # TAB 4: Manual Transcript Entry
    with tab4:
        st.header("📝 Manual Transcript Entry")
        st.write("Manually add transcripts to cache to avoid YouTube API limits")

        col1, col2 = st.columns([1, 2])

        with col1:
            video_id = st.text_input(
                "Video ID",
                placeholder="e.g., dQw4w9WgXcQ",
                help="YouTube video ID (not full URL)",
                key="manual_video_id",
            )

            st.info("💡 Get video ID from URL: youtube.com/watch?v=**VIDEO_ID**")

        with col2:
            transcript_text = st.text_area(
                "Transcript",
                placeholder="Paste the transcript here...",
                height=300,
                help="Paste the full video transcript",
            )

            save_button = st.button("💾 Save to Cache", type="primary")

            if save_button:
                if not video_id:
                    st.error("❌ Please enter a video ID")
                elif not transcript_text:
                    st.error("❌ Please paste a transcript")
                else:
                    # Save to cache via youtube_agent
                    success, message = youtube_agent.save_transcript(
                        video_id, transcript_text
                    )

                    if success:
                        st.success(
                            f"✅ Transcript saved! ({len(transcript_text)} characters)"
                        )
                        st.info(f"Video ID: {video_id}")
                    else:
                        st.error(f"❌ Failed to save: {message}")

        # Show cached transcripts
        st.markdown("---")
        st.subheader("Cached Transcripts")

        cached_keys = youtube_agent.cache.list_keys()

        if cached_keys:
            st.write(f"**{len(cached_keys)} transcripts cached:**")

            cols = st.columns(3)
            for i, key in enumerate(cached_keys):
                with cols[i % 3]:
                    st.code(key, language=None)
        else:
            st.info("No transcripts cached yet")

    # Footer
    st.markdown("---")
    st.markdown("**Disclaimer:** Educational purposes only. Not financial advice.")


if __name__ == "__main__":
    main()
