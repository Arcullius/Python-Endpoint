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
@app.get("/get_nodes_with_attribute_filter")
def get_nodes_with_attribute_filter_endpoint(request: Request):

  # Extract query parameters
  query_params = dict(request.query_params)
  api_key = query_params.get("api_key")
  
  # Use demo job ID as default (same as the demo)
  job_id = query_params.get("job_id", "-OT77Az4JJlgEgQOASe0")
  
  # Extract attribute filters from query parameters
  attribute_filters = {}
  for key, value in query_params.items():
    if key not in ["api_key", "job_id"]:
      attribute_filters[key] = value

  # If API key is not defined, respond with an error 400 response
  if not api_key:
    return Response(content="Missing api_key parameter", status_code=400)

  BASE_URL = "https://dcs.katapultpro.com/api/v3/jobs"
  nodes_url = f"{BASE_URL}/{job_id}/nodes?api_key={api_key}"

  try:
    # Make the GET request to fetch nodes
    nodes_response = requests.get(nodes_url)
    
    if nodes_response.status_code != 200:
      return Response(
        content=nodes_response.text,
        status_code=nodes_response.status_code
      )
    
    data = nodes_response.json()
    nodes = data.get('data', [])
    matching_nodes = []
    
    # Filter nodes based on attribute filters
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
    
    # Return the filtered results
    return {
      "data": matching_nodes,
      "total": len(matching_nodes),
      "filters_applied": attribute_filters,
      "job_id": job_id
    }
    
  except Exception as e:
    return Response(
      content=f"Error processing request: {str(e)}",
      status_code=500
    )



      
