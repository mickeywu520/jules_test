from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware Configuration
origins = [
    "http://localhost",       # For local development if frontend is served directly
    "http://localhost:4200",  # Default Angular development server
    # Add any other origins if necessary, e.g., your deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    # allow_origins=["*"], # Allows all origins (less secure, for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI backend!"}

@app.get("/api/data")
async def get_data():
    return {"sample_data": ["value1", "value2", "value3"], "status": "success"}
