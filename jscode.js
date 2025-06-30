// Cloudflare Worker for Katapult Pro API endpoints
// This worker provides JavaScript equivalents of the Python FastAPI endpoints

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // Add CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': 'https://dcs.katapultpro.com',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Route requests to appropriate handlers
    switch (path) {
      case '/':
        return handleHealthCheck(corsHeaders);
      case '/filter_nodes':
        return handleFilterNodes(request, corsHeaders);
      case '/create_job':
        return handleCreateJob(request, corsHeaders);
      case '/get_nodes_with_photos':
        return handleGetNodesWithPhotos(request, corsHeaders);
      case '/update_node_attributes':
        return handleUpdateNodeAttributes(request, corsHeaders);
      case '/delete_nodes_by_attribute':
        return handleDeleteNodesByAttribute(request, corsHeaders);
      default:
        return new Response('Not Found', { 
          status: 404, 
          headers: corsHeaders 
        });
    }
  },
};

// Health check endpoint
function handleHealthCheck(corsHeaders) {
  const response = {
    status: 'ok',
    message: 'Cloudflare Worker is running',
    endpoints: [
      '/add_welcome_note',
      '/filter_nodes',
      '/create_job',
      '/get_nodes_with_photos',
      '/update_node_attributes',
      '/delete_nodes_by_attribute'
    ]
  };
  
  return new Response(JSON.stringify(response, null, 2), {
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders
    }
  });
}

// Filter nodes endpoint - returns filtered nodes without creating a note
async function handleFilterNodes(request, corsHeaders) {
  

  const url = new URL(request.url);
  const api_key = url.searchParams.get('api_key');
  const job_id = url.searchParams.get('job_id') || '-OT77Az4JJlgEgQOASe0';
  const node_id = url.searchParams.get('node_id');

  if (!api_key) {
    return new Response('Missing api_key parameter', { 
      status: 400, 
      headers: corsHeaders 
    });
  }

  try {
    // Hardcode attribute filters for node_type
    const attribute_filters = { node_type: 'pole' };
    const nodes_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/nodes?api_key=${api_key}`;

    // Get nodes from the Katapult Pro API
    const nodes_response = await fetch(nodes_url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!nodes_response.ok) {
      return new Response(await nodes_response.text(), { 
        status: nodes_response.status, 
        headers: corsHeaders 
      });
    }

    const data = await nodes_response.json();
    const nodes = data.data || [];
    const matching_nodes = [];

    // Filter nodes
    for (const node of nodes) {
      let match = true;
      for (const [key, filter_value] of Object.entries(attribute_filters)) {
        const node_attributes = node.attributes || {};
        const attribute_value = Object.values(node_attributes[key] || {})[0] || node_attributes[key];
        if (attribute_value !== filter_value) {
          match = false;
          break;
        }
      }
      if (match) {
        matching_nodes.push(node);
      }
    }

    console.log(`Data: ${matching_nodes.length} nodes found\nFilters applied: ${JSON.stringify(attribute_filters)}\nJob ID: ${job_id}\nNodes: ${JSON.stringify(matching_nodes)}`);

    // Create result
    const result = {
      data: matching_nodes,
      total: matching_nodes.length,
      filters_applied: attribute_filters,
      job_id: job_id
    };

    return new Response(JSON.stringify(result, null, 2), {
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });

  } catch (error) {
    return new Response(`Error processing request: ${error.message}`, { 
      status: 500, 
      headers: corsHeaders 
    });
  }
}

// Create job endpoint
async function handleCreateJob(request, corsHeaders) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { 
      status: 405, 
      headers: corsHeaders 
    });
  }

  const url = new URL(request.url);
  const api_key = url.searchParams.get('api_key');
  const job_name = url.searchParams.get('job_name');
  const model_type = url.searchParams.get('model_type') || 'default';
  const metadata = url.searchParams.get('metadata');

  if (!api_key || !job_name) {
    return new Response('Missing required parameters: api_key and job_name', { 
      status: 400, 
      headers: corsHeaders 
    });
  }

  try {
    const jobs_url = `https://dcs.katapultpro.com/api/v3/jobs?api_key=${api_key}`;
    const request_body = {
      name: job_name,
      model: model_type,
      metadata: metadata ? JSON.parse(metadata) : null
    };

    const response = await fetch(jobs_url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request_body)
    });

    if (response.ok) {
      const result = await response.json();
      return new Response(JSON.stringify(result, null, 2), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } else {
      return new Response(await response.text(), { 
        status: response.status, 
        headers: corsHeaders 
      });
    }

  } catch (error) {
    return new Response(`Error processing request: ${error.message}`, { 
      status: 500, 
      headers: corsHeaders 
    });
  }
}

// Get nodes with photos endpoint
async function handleGetNodesWithPhotos(request, corsHeaders) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { 
      status: 405, 
      headers: corsHeaders 
    });
  }

  const url = new URL(request.url);
  const api_key = url.searchParams.get('api_key');
  const job_id = url.searchParams.get('job_id');

  if (!api_key || !job_id) {
    return new Response('Missing required parameters: api_key and job_id', { 
      status: 400, 
      headers: corsHeaders 
    });
  }

  try {
    const nodes_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/nodes?api_key=${api_key}`;
    const photos_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/photos?api_key=${api_key}`;

    // Get nodes and photos
    const [nodes_response, photos_response] = await Promise.all([
      fetch(nodes_url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      }),
      fetch(photos_url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
    ]);

    if (!nodes_response.ok) {
      return new Response(await nodes_response.text(), { 
        status: nodes_response.status, 
        headers: corsHeaders 
      });
    }

    if (!photos_response.ok) {
      return new Response(await photos_response.text(), { 
        status: photos_response.status, 
        headers: corsHeaders 
      });
    }

    const nodes_data = await nodes_response.json();
    const photos_data = await photos_response.json();

    // Process nodes with photos
    const nodes = Object.values(nodes_data.data || {}).map(node_data => {
      const associated_photo_ids = Object.keys(node_data.photos || {});
      
      const node_photos = associated_photo_ids.map((photo_id, i) => {
        const photo_data = (photos_data.data || []).find(photo => photo.id === photo_id) || {};
        
        return {
          photoId: photo_id,
          name: photo_data.filename || null,
          date: photo_data.date_taken ? new Date(photo_data.date_taken * 1000).toISOString() : null,
          associated: true,
          metadata: {
            camera: photo_data.camera_model,
            width: photo_data.image_width,
            height: photo_data.image_height,
            orientation: photo_data.orientation,
            uploaded_by: photo_data.uploaded_by
          }
        };
      });

      return {
        id: node_data.id,
        latitude: node_data.latitude,
        longitude: node_data.longitude,
        attributes: node_data.attributes || {},
        photos: node_photos,
        total_photos: node_photos.length
      };
    });

    const result = {
      data: nodes,
      total: nodes.length,
      job_id: job_id
    };

    return new Response(JSON.stringify(result, null, 2), {
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });

  } catch (error) {
    return new Response(`Error processing request: ${error.message}`, { 
      status: 500, 
      headers: corsHeaders 
    });
  }
}

// Update node attributes endpoint
async function handleUpdateNodeAttributes(request, corsHeaders) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { 
      status: 405, 
      headers: corsHeaders 
    });
  }

  const url = new URL(request.url);
  const api_key = url.searchParams.get('api_key');
  const job_id = url.searchParams.get('job_id');
  const attribute_filters = url.searchParams.get('attribute_filters');
  const new_attributes = url.searchParams.get('new_attributes');
  const operation = url.searchParams.get('operation') || 'add';

  if (!api_key || !job_id || !attribute_filters || !new_attributes) {
    return new Response('Missing required parameters: api_key, job_id, attribute_filters, new_attributes', { 
      status: 400, 
      headers: corsHeaders 
    });
  }

  try {
    // Parse JSON parameters
    const parsed_filters = JSON.parse(attribute_filters);
    const parsed_attributes = JSON.parse(new_attributes);

    // First get nodes with the specified filters
    const nodes_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/nodes?api_key=${api_key}`;
    const nodes_response = await fetch(nodes_url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!nodes_response.ok) {
      return new Response(await nodes_response.text(), { 
        status: nodes_response.status, 
        headers: corsHeaders 
      });
    }

    const data = await nodes_response.json();
    const nodes = data.data || [];
    const matching_nodes = [];

    // Filter nodes based on attribute filters
    for (const node of nodes) {
      let match = true;
      for (const [key, filter_value] of Object.entries(parsed_filters)) {
        const node_attributes = node.attributes || {};
        const attribute_value = Object.values(node_attributes[key] || {})[0] || node_attributes[key];
        if (attribute_value !== filter_value) {
          match = false;
          break;
        }
      }
      if (match) {
        matching_nodes.push(node);
      }
    }

    const results = [];
    for (const node of matching_nodes) {
      let update_body = {};
      
      if (operation === 'add') {
        update_body.add_attributes = parsed_attributes;
      } else if (operation === 'update') {
        const current_attributes = node.attributes || {};
        const updated_attributes = { ...current_attributes };
        
        for (const [key, value] of Object.entries(parsed_attributes)) {
          if (current_attributes[key]) {
            if (typeof current_attributes[key] === 'object') {
              for (const instance_id of Object.keys(current_attributes[key])) {
                updated_attributes[key][instance_id] = value;
              }
            } else {
              updated_attributes[key] = value;
            }
          }
        }
        
        if (Object.keys(updated_attributes).length > 0) {
          update_body.attributes = updated_attributes;
        }
      } else if (operation === 'remove') {
        update_body.remove_attributes = Object.keys(parsed_attributes).filter(
          attr => node.attributes && node.attributes[attr] !== undefined
        );
      } else {
        continue;
      }

      if (Object.keys(update_body).length > 0) {
        const update_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/nodes/${node.id}?api_key=${api_key}`;
        const response = await fetch(update_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(update_body)
        });
        
        const response_data = await response.json();
        results.push(response_data);
      } else {
        results.push(node);
      }
    }

    const result = {
      updated_nodes: results,
      total_updated: results.length,
      operation: operation,
      job_id: job_id
    };

    return new Response(JSON.stringify(result, null, 2), {
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });

  } catch (error) {
    return new Response(`Error processing request: ${error.message}`, { 
      status: 500, 
      headers: corsHeaders 
    });
  }
}

// Delete nodes by attribute endpoint
async function handleDeleteNodesByAttribute(request, corsHeaders) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { 
      status: 405, 
      headers: corsHeaders 
    });
  }

  const url = new URL(request.url);
  const api_key = url.searchParams.get('api_key');
  const job_id = url.searchParams.get('job_id');
  const attribute_filters = url.searchParams.get('attribute_filters');

  if (!api_key || !job_id || !attribute_filters) {
    return new Response('Missing required parameters: api_key, job_id, attribute_filters', { 
      status: 400, 
      headers: corsHeaders 
    });
  }

  try {
    // Parse JSON parameters
    const parsed_filters = JSON.parse(attribute_filters);

    // First get nodes with the specified filters
    const nodes_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/nodes?api_key=${api_key}`;
    const nodes_response = await fetch(nodes_url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!nodes_response.ok) {
      return new Response(await nodes_response.text(), { 
        status: nodes_response.status, 
        headers: corsHeaders 
      });
    }

    const data = await nodes_response.json();
    const nodes = data.data || [];
    const matching_nodes = [];

    // Filter nodes based on attribute filters
    for (const node of nodes) {
      let match = true;
      for (const [key, filter_value] of Object.entries(parsed_filters)) {
        const node_attributes = node.attributes || {};
        const attribute_value = Object.values(node_attributes[key] || {})[0] || node_attributes[key];
        if (attribute_value !== filter_value) {
          match = false;
          break;
        }
      }
      if (match) {
        matching_nodes.push(node);
      }
    }

    const results = [];
    for (const node of matching_nodes) {
      const delete_url = `https://dcs.katapultpro.com/api/v3/jobs/${job_id}/nodes/${node.id}?api_key=${api_key}`;
      const response = await fetch(delete_url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const response_data = response.ok ? await response.json() : await response.text();
      results.push({ 
        deleted_node: node, 
        response: response_data 
      });
    }

    const result = {
      deleted_nodes: results,
      total_deleted: results.length,
      job_id: job_id
    };

    return new Response(JSON.stringify(result, null, 2), {
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });

  } catch (error) {
    return new Response(`Error processing request: ${error.message}`, { 
      status: 500, 
      headers: corsHeaders 
    });
  }
}
