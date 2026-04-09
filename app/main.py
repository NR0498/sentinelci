from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "SentinelCI is running 🚀"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "test_user"}