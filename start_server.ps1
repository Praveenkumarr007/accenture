$env:DATABASE_URL="sqlite:///./data/bi_intelligence.db"
cd "C:\Users\Administrator\OneDrive\Desktop\businessintelligence-ai\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
