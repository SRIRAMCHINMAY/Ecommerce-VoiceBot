import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "app.server:app", 
        host="0.0.0.0", 
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True
    )