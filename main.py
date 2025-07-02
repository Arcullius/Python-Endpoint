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



@app.get("/filter_nodes")
def filter_nodes(request: Request = None, api_key: str = None, job_id: str = "-OTcBEj966ESJQ7vQSvE", custom_filters=None):
  # Handle parameters from either GET request or direct function call
  if request is not None:
    # Extract query parameters from the incoming GET request
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_id = query_params.get("job_id", "-OTcBEj966ESJQ7vQSvE")  # Default job ID if not provided
    node_id = query_params.get("node_id")
  # For direct function calls, use the provided parameters
  elif api_key is None:
    # If called internally without proper parameters, raise exception
    raise Exception("Missing api_key parameter for internal call")
    
  # Validate required API key parameter
  if not api_key:
    if custom_filters is not None:
      # For internal calls, raise exception to be handled by calling function
      raise Exception("Missing api_key parameter")
    # For external API calls, return HTTP 400 error response
    return Response(content="Missing api_key parameter", status_code=400)
  
  # Determine which filters to use: custom filters (for internal calls) or default pole filter (for API calls)
  attribute_filters = custom_filters if custom_filters is not None else {"node_type": "pole"}
  
  # Build the API URL to fetch all nodes from the specified job
  nodes_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes?api_key={api_key}"
  
  # Set up HTTP headers for the API request
  header = {
      "Content-Type": "application/json",
  }
  
  # Make API call to Katapult Pro to get all nodes for the job
  nodes_response = requests.get(nodes_url, headers=header)
  
  # Check if the API call was successful
  if nodes_response.status_code != 200:
      if custom_filters is not None:
          # For internal calls, raise exception with detailed error info
          raise Exception(f"Failed to fetch nodes: {nodes_response.status_code} {nodes_response.text}")
      # For external API calls, return the error response from upstream API
      return Response(
          content=nodes_response.text,
          status_code=nodes_response.status_code
      )
      
  # Parse the JSON response and extract the nodes list
  data = nodes_response.json()
  nodes = data.get("data", [])
  matching_nodes = []
    
  # Apply filtering logic to find nodes that match all specified attribute criteria
  for node in nodes:
      match = True
      
      # Check each filter criteria against the node's attributes
      for key, filter_value in attribute_filters.items():
          node_attributes = node.get("attributes", {})
          # Handle both direct attribute values and nested attribute objects with instance IDs
          # Use next() to get the first value from nested dicts, or fall back to direct value
          attribute_value = next(iter(node_attributes.get(key, {}).values()), node_attributes.get(key))
          
          # If any filter criteria doesn't match, exclude this node
          if attribute_value != filter_value:
              match = False
              break
              
      # Add node to results if it matches all filter criteria
      if match:
          matching_nodes.append(node)
  
  # For internal function calls, return just the filtered nodes list
  if custom_filters is not None:
      return matching_nodes
  
  # Log results for debugging and monitoring
  print(f"Data: {len(matching_nodes)} nodes found\nFilters applied: {attribute_filters}\nJob ID: {job_id}\nNodes: {matching_nodes}")
  
  # For external API calls, format and return a complete JSON response
  results_json = {
    "data": matching_nodes,              # List of nodes that matched the filter criteria
    "total": len(matching_nodes),        # Count of matching nodes
    "filters_applied": attribute_filters, # The filter criteria that were used
    "job_id": job_id                     # The job ID that was queried
  }
  
  # Return the formatted JSON response
  return Response(
    content=json.dumps(results_json, indent=2),
    media_type="application/json",
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
    """
    Update node attributes endpoint - modifies attributes on nodes matching specified filters
    
    Args:
        request: FastAPI Request object containing query parameters
    """
    
    # Extract all required parameters from the request query string
    query_params = dict(request.query_params)
    api_key = query_params.get("api_key")
    job_id = query_params.get("job_id")
    attribute_filters = query_params.get("attribute_filters")  # JSON string of filter criteria
    new_attributes = query_params.get("new_attributes")        # JSON string of attributes to add/update/remove
    operation = query_params.get("operation", "add")           # Default to 'add' operation
    
    # Validate that all required parameters are present
    if not api_key or not job_id or not attribute_filters or not new_attributes:
        return Response(content="Missing required parameters: api_key, job_id, attribute_filters, new_attributes", status_code=400)
    
    try:
        # Parse JSON parameters from query strings into Python objects
        attribute_filters = json.loads(attribute_filters)
        new_attributes = json.loads(new_attributes)
        
        # Reuse the filtering logic from filter_nodes to find matching nodes
        # Pass the parsed filters to get nodes that match the specified criteria
        matching_nodes = filter_nodes(request, attribute_filters)
        
        # Set up HTTP headers for API requests to Katapult Pro
        headers = {
            "Content-Type": "application/json",
        }
        
        # Process each matching node to apply the requested attribute changes
        results = []
        for node in matching_nodes:
            update_body = {}
            
            # Build the update request body based on the specified operation type
            if operation == 'add':
                # Add new attributes to the node (will create new or overwrite existing)
                update_body['add_attributes'] = new_attributes
            elif operation == 'update':
                # Update existing attributes while preserving the current structure
                current_attributes = node.get('attributes', {})
                updated_attributes = current_attributes.copy()
                
                # Update each specified attribute, handling both direct values and nested objects
                for key, value in new_attributes.items():
                    if key in current_attributes:
                        if isinstance(current_attributes[key], dict):
                            # For nested attribute objects (with instance IDs), update all instances
                            for instance_id in current_attributes[key]:
                                updated_attributes[key][instance_id] = value
                        else:
                            # For direct attribute values, simply replace the value
                            updated_attributes[key] = value
                            
                # Only include attributes in the update if there are changes to make
                if updated_attributes:
                    update_body['attributes'] = updated_attributes
            elif operation == 'remove':
                # Remove specified attributes that currently exist on the node
                update_body['remove_attributes'] = [attr for attr in new_attributes if node.get('attributes', {}).get(attr) is not None]
            else:
                # Skip nodes if operation type is unrecognized
                continue
                
            # Only make API call if there are actual changes to apply
            if update_body:
                # Build the API URL for updating this specific node
                update_url = f"https://dcs.katapultpro.com/api/v3/jobs/{job_id}/nodes/{node['id']}?api_key={api_key}"
                
                # Make API call to Katapult Pro to update the node
                response = requests.post(update_url, json=update_body, headers=headers)
                
                # Parse the response and add to results
                results.append(response.json())
            else:
                # If no changes needed, include the original node data in results
                results.append(node)
        
        # Format the final response with summary information
        result = {
            "updated_nodes": results,        # List of updated node data or API responses
            "total_updated": len(results),   # Count of nodes that were processed
            "operation": operation,          # The operation type that was performed
            "job_id": job_id                # The job ID that was modified
        }
        
        # Return the formatted JSON response
        return Response(
            content=json.dumps(result, indent=2),
            media_type="application/json"
        )
        
    except Exception as e:
        # Handle any errors that occurred during processing
        return Response(
            content=f"Error processing request: {str(e)}",
            status_code=500
        )

