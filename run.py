import asyncio
import sys
import uvicorn

# This script is the new entry point to run the application.
# It ensures the asyncio policy is set correctly on Windows before Uvicorn starts.

if __name__ == "__main__":
    # Apply the asyncio policy fix for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Programmatically run the Uvicorn server
    uvicorn.run(
        "app.main:app",  # Path to your FastAPI app
        host="0.0.0.0",
        port=8000,
        reload=True
    )