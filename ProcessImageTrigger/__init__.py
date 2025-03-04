import logging
import json
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (
    ContainerGroup, Container, ResourceRequirements, 
    ResourceRequests, EnvironmentVariable, GpuResource
)
from azure.identity import DefaultAzureCredential
import datetime
import traceback  # Add this import

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Python HTTP trigger function processing request.')
        
        # Log the request details
        logging.info(f'Request method: {req.method}')
        logging.info(f'Request headers: {dict(req.headers)}')
        logging.info(f'Request body: {req.get_body().decode()}')

        # Get job ID from request
        req_body = req.get_json()
        job_id = req_body.get('job_id')
        image_url = req_body.get('image_url')
        
        logging.info(f'Received job_id: {job_id}, image_url: {image_url}')

        if not job_id or not image_url:
            return func.HttpResponse(
                json.dumps({
                    "error": "Missing required parameters",
                    "job_id": bool(job_id),
                    "image_url": bool(image_url)
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Log environment variables (excluding sensitive data)
        logging.info('Checking environment variables...')
        required_vars = [
            "AzureWebJobsStorage",
            "SUBSCRIPTION_ID",
            "RESOURCE_GROUP",
            "FUNCTION_APP_NAME",
            "CONTAINER_IMAGE",
            "LOCATION"
        ]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            logging.error(f'Missing environment variables: {missing_vars}')
            return func.HttpResponse(
                json.dumps({
                    "error": "Missing environment variables",
                    "missing": missing_vars
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Rest of your existing code...
        
        # Return success response
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "status": "queued",
                "message": "Job queued successfully",
                "status_url": f"https://{os.environ['FUNCTION_APP_NAME']}.azurewebsites.net/api/GetJobStatus?job_id={job_id}"
            }),
            mimetype="application/json"
        )

    except Exception as e:
        # Log the full error details
        logging.error(f'Error in function: {str(e)}')
        logging.error(f'Traceback: {traceback.format_exc()}')
        
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }),
            status_code=500,
            mimetype="application/json"
        )