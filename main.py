from fastapi import FastAPI, Request, Response
import requests
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dcs.katapultpro.com"],  # or ["*"] for testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/add_welcome_note")
def add_welcome_note(request: Request):

  # Extract query parameters
  query_params = dict(request.query_params)
  api_key = query_params.get("api_key")
  job_id = query_params.get("job_id", "-OT77Az4JJlgEgQOASe0")

  # If any parameters are not defined, respond with an error 400 response
  if not api_key:
    return Response(content="Missing api_key parameter", status_code=400)
  
  # Hardcode attribute filters for node_type
  attribute_filters = {"node_type": "pole"}
  nodes_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes?api_key={api_key}"

  try:
    # The request header
    headers = {
      "Content-Type": "application/json",
    }
    
    # Get nodes from the Katapult Pro API
    nodes_response = requests.get(nodes_url, headers=headers)
    
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
    
    # Return the response
    print(f"Data: {len(matching_nodes)} nodes found\nFilters applied: {attribute_filters}\nJob ID: {job_id}")
    
    # Create JSON string of the results
    results_json = {
      "data": matching_nodes,
      "total": len(matching_nodes),
      "filters_applied": attribute_filters,
      "job_id": job_id
    }
    
    # Convert to formatted JSON string for the note
    note_text = json.dumps(results_json, indent=2)
    
    # Create a map note with the JSON data
    note_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/notes?api_key={api_key}"
    
    note_data = {
      "text": note_text,
      "type": "info",
      "title": f"Filtered Nodes Result ({len(matching_nodes)} poles found)"
    }
    
    # Post the note to the map
    note_response = requests.post(note_url, json=note_data, headers=headers)
    
    if note_response.status_code in [200, 201]:
      return {
        "success": True,
        "message": f"Map note created with {len(matching_nodes)} matching nodes",
        "note_id": note_response.json().get("id"),
        "total_nodes_found": len(matching_nodes),
        "filters_applied": attribute_filters,
        "job_id": job_id
      }
    else:
      return Response(
        content=f"Failed to create note: {note_response.text}",
        status_code=note_response.status_code
      )
    
  except Exception as e:
    return Response(
      content=f"Error processing request: {str(e)}",
      status_code=500
    )


