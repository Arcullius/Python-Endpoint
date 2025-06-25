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


# Specify what subpath should trigger this function
@app.post("/add_welcome_note")
def add_welcome_note(request: Request):

  # Extract query parameters
  query_params = dict(request.query_params)
  job_id = query_params.get("job_id")
  node_id = query_params.get("node_id")
  api_key = query_params.get("api_key")

  # If any parameters are not defined, respond with an error 400 response
  if not (job_id and node_id and api_key):
    return Response(content="Missing parameters", status_code=400)

  new_request_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes/{node_id}/?api_key={api_key}"

  # The data we want to send to the Katapult Pro API
  request_body = {
    "add_attributes": {
      "note": "This is a note from my new awesome python API tool!"
    }
  }

  # The request header
  header = {
    "Content-Type": "application/json",
  }

  # Make the POST request
  katapult_response = requests.post(new_request_url, json=request_body, headers=header)
  
  # Return the response
  return Reponse(
    content = katapult_response.text,
    status_code = katapult_response.status_code
  )



      
