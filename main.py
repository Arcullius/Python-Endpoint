from fastapi import FastAPI, Request, Response
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dcs.katapultpro.com"],  # or ["*"] for testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v3/jobs")
def proxy_katapult(request: Request):
    # Extract query parameters
    query_params = dict(request.query_params)
    job_id = query_params.get("job_id")
    node_id = query_params.get("node_id")
    api_key = query_params.get("api_key")

    if not (job_id and node_id and api_key):
        return Response(content="Missing parameters", status_code=400)

    # Construct the request to Katapult Pro API
    new_request_url = f"https://dcs.katapultpro.com/api/v2/jobs/{job_id}/nodes/{node_id}?api_key={api_key}"

    request_body = {
        "add_attributes": {
            "note": "This is a note from my new awesome python API tool!"
        }
    }

    headersS = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://dcs.katapultpro.com"
    }

    katapult_response = requests.post(new_request_url, json=request_body, headers=headersS)

    return Response(
        content=katapult_response.text,
        status_code=katapult_response.status_code,
        headers=headersS
    )
