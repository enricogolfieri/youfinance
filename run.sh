#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Stock Analysis Application..."
echo ""

# Function to check if MongoDB is running
check_mongodb() {
    if pgrep -x "mongod" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start MongoDB
start_mongodb() {
    echo "📦 Starting MongoDB..."
    
    # Check if MongoDB is installed
    if ! command -v mongod &> /dev/null; then
        echo -e "${RED}❌ MongoDB is not installed!${NC}"
        echo ""
        echo "Please install MongoDB first:"
        echo "  macOS:  brew install mongodb-community"
        echo "  Linux:  sudo apt-get install mongodb-org"
        echo ""
        echo "Or visit: https://www.mongodb.com/try/download/community"
        exit 1
    fi
    
    # Try to start MongoDB using brew services (macOS)
    if command -v brew &> /dev/null; then
        echo "  Using Homebrew to start MongoDB..."
        brew services start mongodb-community 2>/dev/null
        sleep 2
        
        if check_mongodb; then
            echo -e "${GREEN}✅ MongoDB started successfully${NC}"
            return 0
        fi
    fi
    
    # Try to start MongoDB using systemctl (Linux)
    if command -v systemctl &> /dev/null; then
        echo "  Using systemctl to start MongoDB..."
        sudo systemctl start mongod 2>/dev/null
        sleep 2
        
        if check_mongodb; then
            echo -e "${GREEN}✅ MongoDB started successfully${NC}"
            return 0
        fi
    fi
    
    # Try to start MongoDB directly
    echo "  Starting MongoDB directly..."
    mkdir -p ./data/db
    mongod --dbpath ./data/db --fork --logpath ./data/mongodb.log 2>/dev/null
    sleep 2
    
    if check_mongodb; then
        echo -e "${GREEN}✅ MongoDB started successfully${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Could not start MongoDB automatically${NC}"
        echo "Please start MongoDB manually and run this script again."
        exit 1
    fi
}

# Check if MongoDB is running
if check_mongodb; then
    echo -e "${GREEN}✅ MongoDB is already running${NC}"
else
    echo -e "${YELLOW}⚠️  MongoDB is not running${NC}"
    start_mongodb
fi

echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found${NC}"
    echo "Continuing with system Python..."
fi

echo ""

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not installed${NC}"
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Test MongoDB connection
echo "🔌 Testing MongoDB connection..."
if python -c "from modules.mongodb_cache import MongoDBCache; MongoDBCache()" 2>/dev/null; then
    echo -e "${GREEN}✅ MongoDB connection successful${NC}"
else
    echo -e "${RED}❌ Could not connect to MongoDB${NC}"
    echo "Please check your MongoDB installation and try again."
    exit 1
fi

echo ""
echo "🎬 Starting Streamlit application..."
echo "   Access the app at: http://localhost:8501"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop the application${NC}"
echo ""

# Run Streamlit
streamlit run app.py
