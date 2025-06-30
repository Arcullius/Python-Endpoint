from fastapi import FastAPI, Request, Response
import requests
import json
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dcs.katapultpro.com"],  # or ["*"] for testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/filter_nodes")
def filter_nodes(request: Request):

  # Extract query parameters
  query_params = dict(request.query_params)
  api_key = query_params.get("api_key")
  job_id = query_params.get("job_id", "-OT77Az4JJlgEgQOASe0")
  node_id = query_params.get("node_id")
    
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
    print(f"Data: {len(matching_nodes)} nodes found\nFilters applied: {attribute_filters}\nJob ID: {job_id}\nNodes: {matching_nodes}")
    
    # Create JSON string of the results
    results_json = {
      "data": matching_nodes,
      "total": len(matching_nodes),
      "filters_applied": attribute_filters,
      "job_id": job_id
    }
    
    return Response(
      content=json.dumps(results_json, indent=2),
      media_type="application/json",
    
    )
  except Exception as e:
    return Response(
      content=f"Error processing request: {str(e)}",
      status_code=500
    )

@app.post("/create_job")
def create_job_endpoint(request: Request):
    # Extract query parameters
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_name = query_params.get("job_name")
    model_type = query_params.get("model_type", "default")
    metadata = query_params.get("metadata")
    
    # If any required parameters are not defined, respond with an error 400 response
    if not api_key or not job_name:
        return Response(content="Missing required parameters: api_key and job_name", status_code=400)
    
    try:
        url = f"https://dcs.katapultpro.com/api/v3/jobs?api_key={api_key}"
        request_body = {
            'name': job_name,
            'model': model_type,
            'metadata': json.loads(metadata) if metadata else None,
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        response = requests.post(url, json=request_body, headers=headers)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return Response(
                content=response.text,
                status_code=response.status_code
            )
            
    except Exception as e:
        return Response(
            content=f"Error processing request: {str(e)}",
            status_code=500
        )

@app.post("/get_nodes_with_photos")
def get_nodes_with_photos_endpoint(request: Request):
    # Extract query parameters
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_id = query_params.get("job_id")
    
    # If any required parameters are not defined, respond with an error 400 response
    if not api_key or not job_id:
        return Response(content="Missing required parameters: api_key and job_id", status_code=400)
    
    try:
        nodes_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes?api_key={api_key}"
        photos_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/photos?api_key={api_key}"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Get nodes and photos
        nodes_response = requests.get(nodes_url, headers=headers)
        photos_response = requests.get(photos_url, headers=headers)
        
        if nodes_response.status_code != 200:
            return Response(
                content=nodes_response.text,
                status_code=nodes_response.status_code
            )
            
        if photos_response.status_code != 200:
            return Response(
                content=photos_response.text,
                status_code=photos_response.status_code
            )
        
        nodes_data = nodes_response.json()
        photos_data = photos_response.json()
        
        nodes = [
            {
                'id': node_data.get('id'),
                'latitude': node_data.get('latitude'),
                'longitude': node_data.get('longitude'),
                'attributes': node_data.get('attributes', {}),
                'photos': [
                    {
                        'photoId': photo_id,
                        'name': (photos_data['data'][i].get('filename') if 'data' in photos_data and i < len(photos_data['data']) else None),
                        'date': datetime.fromtimestamp(photos_data['data'][i]['date_taken']).isoformat() if 'data' in photos_data and i < len(photos_data['data']) and 'date_taken' in photos_data['data'][i] else None,
                        'associated': True,
                        'metadata': {
                            'camera': photos_data['data'][i].get('camera_model'),
                            'width': photos_data['data'][i].get('image_width'),
                            'height': photos_data['data'][i].get('image_height'),
                            'orientation': photos_data['data'][i].get('orientation'),
                            'uploaded_by': photos_data['data'][i].get('uploaded_by'),
                        }
                    }
                    for i, photo_id in enumerate(node_data.get('photos', {}).keys())
                ],
                'total_photos': len(node_data.get('photos', {}))
            }
            for node_data in (nodes_data.get('data', []) if isinstance(nodes_data.get('data', []), list) else [])
        ]
        
        result = {
            "data": nodes,
            "total": len(nodes),
            "job_id": job_id
        }
        print(f"Data: {result}")
        
        return Response(
            content=json.dumps(result, indent=2),
            media_type="application/json"
        )
        
    except Exception as e:
        return Response(
            content=f"Error processing request: {str(e)}",
            status_code=500
        )

@app.post("/update_node_attributes")
def update_node_attributes_endpoint(request: Request):
    # Extract query parameters
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_id = query_params.get("job_id")
    attribute_filters = query_params.get("attribute_filters")
    new_attributes = query_params.get("new_attributes")
    operation = query_params.get("operation", "add")
    
    # If any required parameters are not defined, respond with an error 400 response
    if not api_key or not job_id or not attribute_filters or not new_attributes:
        return Response(content="Missing required parameters: api_key, job_id, attribute_filters, new_attributes", status_code=400)
    
    try:
        # Parse JSON parameters
        attribute_filters = json.loads(attribute_filters)
        new_attributes = json.loads(new_attributes)
        
        # First get nodes with the specified filters
        nodes_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes?api_key={api_key}"
        headers = {
            "Content-Type": "application/json",
        }
        
        nodes_response = requests.get(nodes_url, headers=headers)
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
        
        results = []
        for node in matching_nodes:
            update_body = {}
            if operation == 'add':
                update_body['add_attributes'] = new_attributes
            elif operation == 'update':
                current_attributes = node.get('attributes', {})
                updated_attributes = current_attributes.copy()
                for key, value in new_attributes.items():
                    if key in current_attributes:
                        if isinstance(current_attributes[key], dict):
                            for instance_id in current_attributes[key]:
                                updated_attributes[key][instance_id] = value
                        else:
                            updated_attributes[key] = value
                if updated_attributes:
                    update_body['attributes'] = updated_attributes
            elif operation == 'remove':
                update_body['remove_attributes'] = [attr for attr in new_attributes if node.get('attributes', {}).get(attr) is not None]
            else:
                continue
                
            if update_body:
                update_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes/{node['id']}?api_key={api_key}"
                response = requests.post(update_url, json=update_body, headers=headers)
                results.append(response.json())
            else:
                results.append(node)
        
        result = {
            "updated_nodes": results,
            "total_updated": len(results),
            "operation": operation,
            "job_id": job_id
        }
        
        return Response(
            content=json.dumps(result, indent=2),
            media_type="application/json"
        )
        
    except Exception as e:
        return Response(
            content=f"Error processing request: {str(e)}",
            status_code=500
        )

@app.post("/delete_nodes_by_attribute")
def delete_nodes_by_attribute_endpoint(request: Request):
    # Extract query parameters
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_id = query_params.get("job_id")
    attribute_filters = query_params.get("attribute_filters")
    
    # If any required parameters are not defined, respond with an error 400 response
    if not api_key or not job_id or not attribute_filters:
        return Response(content="Missing required parameters: api_key, job_id, attribute_filters", status_code=400)
    
    try:
        # Parse JSON parameters
        attribute_filters = json.loads(attribute_filters)
        
        # First get nodes with the specified filters
        nodes_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes?api_key={api_key}"
        headers = {
            "Content-Type": "application/json",
        }
        
        nodes_response = requests.get(nodes_url, headers=headers)
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
        
        results = []
        for node in matching_nodes:
            delete_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes/{node['id']}?api_key={api_key}"
            response = requests.delete(delete_url, headers=headers)
            results.append({'deleted_node': node, 'response': response.json() if response.status_code in [200, 204] else response.text})
        
        result = {
            "deleted_nodes": results,
            "total_deleted": len(results),
            "job_id": job_id
        }
        
        return Response(
            content=json.dumps(result, indent=2),
            media_type="application/json"
        )
        
    except Exception as e:
        return Response(
            content=f"Error processing request: {str(e)}",
            status_code=500
        )

@app.post("/add_welcome_note")
def add_welcome_note(request: Request):
    # Extract query parameters
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_id = query_params.get("job_id", "-OT77Az4JJlgEgQOASe0")
    node_id = query_params.get("node_id")

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
