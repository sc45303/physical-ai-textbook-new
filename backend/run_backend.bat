# Install backend dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with your OpenAI API key (optional)
# OPENAI_API_KEY=your_openai_api_key_here

# Run the backend server
uvicorn src.main:app --reload --port 8000