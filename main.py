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
def get_nodes_with_attribute_filter_endpoint(request: Request):

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
    
    # Post notes to matching nodes
    note_results = []
    note_text = "This is a note from my new awesome python API tool!"
    
    for node in matching_nodes:
      node_id = node.get('id')
      if node_id:
        # Create URL for updating this specific node
        update_node_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes/{node_id}?api_key={api_key}"
        
        # The data we want to send to add a note
        request_body = {
          "add_attributes": {
            "note": note_text
          }
        }
        
        try:
          # Make the POST request to add the note
          update_response = requests.post(update_node_url, json=request_body, headers=headers)
          
          note_results.append({
            "node_id": node_id,
            "status_code": update_response.status_code,
            "success": update_response.status_code == 200,
            "response": update_response.text if update_response.status_code != 200 else "Note added successfully"
          })
          
        except Exception as node_error:
          note_results.append({
            "node_id": node_id,
            "status_code": 500,
            "success": False,
            "response": f"Error updating node: {str(node_error)}"
          })
    
    # Return the response
    print(f"Found {len(matching_nodes)} matching nodes, attempted to add notes to all of them")
    
    return {
      "matching_nodes_found": len(matching_nodes),
      "notes_attempted": len(note_results),
      "successful_updates": len([r for r in note_results if r["success"]]),
      "failed_updates": len([r for r in note_results if not r["success"]]),
      "filters_applied": attribute_filters,
      "job_id": job_id,
      "note_results": note_results
    }
    
  except Exception as e:
    return Response(
      content=f"Error processing request: {str(e)}",
      status_code=500
    )


