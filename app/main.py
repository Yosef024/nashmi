from fastapi import FastAPI
# uvicorn app.main:app --reload

app = FastAPI(title="Agentic Government Services MVP")

@app.get("/health")
def health():
    return {"status": "ok"}
