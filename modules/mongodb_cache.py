"""MongoDB-based cache for stock analysis"""

import os
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
import modules.logger as logger

if not logger.is_initialized():
    logger.init("mongodb_cache")


class MongoDBCache:
    """MongoDB cache for stock analysis with aggregation support"""

    def __init__(self, connection_string=None, database_name="stock_analysis"):
        """
        Initialize MongoDB cache

        Args:
            connection_string: MongoDB connection string (defaults to localhost)
            database_name: Database name (default: stock_analysis)
        """
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.analysis_collection = self.db["analysis"]

        # Create indexes for efficient querying
        self.analysis_collection.create_index([("symbol", ASCENDING)])
        self.analysis_collection.create_index([("video_url", ASCENDING)])

        logger.info(f"MongoDB cache initialized: {database_name}")

    def store_analysis(
        self,
        symbol,
        video_url,
        video_title,
        video_date,
        recommendation,
        confidence,
        reasons,
        summary,
    ):
        """
        Store a stock analysis from a video

        Args:
            symbol: Stock symbol
            video_url: YouTube video URL
            video_title: Video title
            video_date: Video publication date (ISO format string)
            recommendation: BUY/SELL/HOLD
            confidence: HIGH/MEDIUM/LOW
            reasons: List of reasons for the recommendation
            summary: Video summary

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            document = {
                "symbol": symbol.upper(),
                "video_url": video_url,
                "video_title": video_title,
                "date": video_date,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasons": reasons,
                "summary": summary,
                "created_at": datetime.utcnow(),
            }

            # Use update_one with upsert to avoid duplicates
            result = self.analysis_collection.update_one(
                {"symbol": symbol.upper(), "video_url": video_url},
                {"$set": document},
                upsert=True,
            )

            if result.upserted_id:
                logger.info(f"Inserted new analysis for {symbol} from {video_url}")
                return True, "Analysis stored successfully"
            else:
                logger.info(f"Updated existing analysis for {symbol} from {video_url}")
                return True, "Analysis already exists (no duplicate)"

        except Exception as e:
            logger.error(f"Error storing analysis for {symbol}: {str(e)}")
            return False, f"Error storing analysis: {str(e)}"

    def get_stock_analysis(self, symbol):
        """
        Get all analysis mentions for a stock, sorted by date (newest first)

        Args:
            symbol: Stock symbol

        Returns:
            tuple: (success: bool, list of mentions or error_message)
        """
        try:
            cursor = self.analysis_collection.find({"symbol": symbol.upper()}).sort(
                "date", DESCENDING
            )

            mentions = []
            for doc in cursor:
                # Remove MongoDB _id field
                doc.pop("_id", None)
                doc.pop("created_at", None)
                mentions.append(doc)

            logger.info(f"Retrieved {len(mentions)} analyses for {symbol}")
            return True, mentions

        except Exception as e:
            logger.error(f"Error retrieving analyses for {symbol}: {str(e)}")
            return False, f"Error retrieving: {str(e)}"

    def get_portfolio(self):
        """
        Get portfolio summary: all stocks with their most recent analysis

        Returns:
            tuple: (success: bool, list of stocks or error_message)
        """
        try:
            pipeline = [
                # Sort by date within each symbol
                {"$sort": {"symbol": ASCENDING, "date": DESCENDING}},
                # Group by symbol and get the most recent analysis
                {
                    "$group": {
                        "_id": "$symbol",
                        "symbol": {"$first": "$symbol"},
                        "latest_date": {"$first": "$date"},
                        "recommendation": {"$first": "$recommendation"},
                        "confidence": {"$first": "$confidence"},
                        "video_title": {"$first": "$video_title"},
                        "video_url": {"$first": "$video_url"},
                        "total_mentions": {"$sum": 1},
                    }
                },
                # Sort by symbol
                {"$sort": {"symbol": ASCENDING}},
            ]

            result = list(self.analysis_collection.aggregate(pipeline))

            # Remove MongoDB _id field
            for item in result:
                item.pop("_id", None)

            logger.info(f"Retrieved portfolio with {len(result)} stocks")
            return True, result

        except Exception as e:
            logger.error(f"Error retrieving portfolio: {str(e)}")
            return False, f"Error retrieving portfolio: {str(e)}"

    def get_all_symbols(self):
        """
        Get list of all stock symbols that have been analyzed

        Returns:
            list: Stock symbols
        """
        try:
            symbols = self.analysis_collection.distinct("symbol")
            return sorted(symbols)
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return []

    def remove_analysis(self, symbol, video_url):
        """
        Remove a specific analysis

        Args:
            symbol: Stock symbol
            video_url: Video URL to identify which analysis to remove

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            result = self.analysis_collection.delete_one(
                {"symbol": symbol.upper(), "video_url": video_url}
            )

            if result.deleted_count > 0:
                logger.info(f"Removed analysis for {symbol} from {video_url}")
                return True, f"Removed analysis successfully"
            else:
                return False, "Analysis not found"

        except Exception as e:
            logger.error(f"Error removing analysis: {str(e)}")
            return False, f"Error removing: {str(e)}"

    def clear_all(self):
        """
        Clear all analyses (use with caution!)

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            result = self.analysis_collection.delete_many({})
            logger.info(f"Cleared all analyses: {result.deleted_count} documents")
            return True, f"Cleared {result.deleted_count} analyses"
        except Exception as e:
            logger.error(f"Error clearing analyses: {str(e)}")
            return False, f"Error clearing: {str(e)}"

    def get_analysis_stats(self):
        """
        Get statistics about the analysis collection

        Returns:
            dict: Statistics including total analyses, stocks count, etc.
        """
        try:
            total_analyses = self.analysis_collection.count_documents({})
            total_stocks = len(self.analysis_collection.distinct("symbol"))

            # Get recommendation distribution
            pipeline = [
                {"$group": {"_id": "$recommendation", "count": {"$sum": 1}}},
                {"$sort": {"count": DESCENDING}},
            ]
            recommendations = list(self.analysis_collection.aggregate(pipeline))

            return {
                "total_analyses": total_analyses,
                "total_stocks": total_stocks,
                "recommendations": {
                    item["_id"]: item["count"] for item in recommendations
                },
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_analysis_by_video_url(self, video_url):
        """
        Get existing analysis for a video (reconstruct from all stock mentions)

        Args:
            video_url: YouTube video URL

        Returns:
            tuple: (success: bool, analysis dict or None)
        """
        try:
            # Find all stock mentions from this video
            cursor = self.analysis_collection.find({"video_url": video_url})

            stocks_mentioned = []
            summary = ""

            for doc in cursor:
                stocks_mentioned.append(
                    {
                        "symbol": doc.get("symbol"),
                        "recommendation": doc.get("recommendation"),
                        "confidence": doc.get("confidence"),
                        "reasons": doc.get("reasons", []),
                    }
                )
                # Get summary from first document (they should all have the same summary)
                if not summary:
                    summary = doc.get("summary", "")

            if not stocks_mentioned:
                return False, None

            # Reconstruct the analysis format
            analysis = {
                "stocks_mentioned": stocks_mentioned,
                "summary": summary,
                "other_insights": [],  # Not stored separately in MongoDB
            }

            logger.info(f"Reconstructed analysis from MongoDB for video: {video_url}")
            return True, analysis

        except Exception as e:
            logger.error(f"Error getting analysis by video URL: {str(e)}")
            return False, None
