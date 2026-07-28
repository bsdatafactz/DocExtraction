from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router

app = FastAPI(title="Invoice Extraction API")

app.add_middleware(
    CORSMiddleware,
    # Regex, not a fixed port: the Vite dev server's port varies (5173,
    # remapped ports when it's taken, ad-hoc ports during testing).
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
