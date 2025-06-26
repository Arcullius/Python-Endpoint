from fastapi import FastAPI, Request, Response
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dcs.katapultpro.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/get_nodes_with_attribute_filter")
def get_nodes_with_attribute_filter_endpoint(request: Request):

  query_params = dict(request.query_params)
  api_key = query_params.get("api_key")
  
  job_id = query_params.get("job_id", "-OT77Az4JJlgEgQOASe0")
  
  attribute_filters = {}
  for key, value in query_params.items():
    if key not in ["api_key", "job_id"]:
      attribute_filters[key] = value

  if not api_key:
    return Response(content="Missing api_key parameter", status_code=400)

  BASE_URL = "https://dcs.katapultpro.com/api/v3/jobs"
  nodes_url = f"{BASE_URL}/{job_id}/nodes?api_key={api_key}"

  try:
    nodes_response = requests.get(nodes_url)
    
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
    
    print(f"Data: {matching_nodes}\nTotal: {len(matching_nodes)}\nFilters applied: {attribute_filters}\nJob ID: {job_id}")
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



      
