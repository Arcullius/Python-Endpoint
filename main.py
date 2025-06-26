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
  # node_id = query_params.get("node_id")
  api_key = query_params.get("api_key")

  # If any parameters are not defined, respond with an error 400 response
  if not (job_id and node_id and api_key):
    return Response(content="Missing parameters", status_code=400)
 attribute_filters = {"node_type": "pole"}
  new_request_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes/?api_key={api_key}"


   

  # The request header
  header = {
    "Content-Type": "application/json",
  }
  # The data we want to send to the Katapult Pro API
  nodes_response = requests.get(new_request_url, headers=header)
    if nodes_response.status_code != 200:
      return Response(
        content=nodes_response.text,
        status_code=nodes_response.status_code
      )
    
    data = nodes_response.json()
    nodes = data.get('data', [])
    matching_nodes = []
    
    for node in nodes:
      match = True
      for key, filter_value in attribute_filters.items():
        node_attributes = node.get('attributes', {})
        attribute_value = next(iter(node_attributes.get(key, {}).values()), node_attributes.get(key))
        if attribute_value != filter_value:
          match = False
          break
      if match:
        matching_nodes.append(node)
    
  # Make the POST request
  # katapult_response = requests.post(new_request_url, json=request_body, headers=header)
  
  # Return the response
print(f"Data: {matching_nodes}\nTotal: {len(matching_nodes)}\nFilters applied: {attribute_filters}\nJob ID: {job_id}")
   
  return Response(
      
      "data": matching_nodes,
      "total": len(matching_nodes),
      "filters_applied": attribute_filters,
      "job_id": job_id
    }
    content = katapult_response.text,
    status_code = katapult_response.status_code
  )


