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
import traceback
import sys

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Set up detailed logging
        logging.info('Python HTTP trigger function processing request.')
        logging.info(f'Request method: {req.method}')
        logging.info(f'Request URL: {req.url}')
        logging.info(f'Request headers: {dict(req.headers)}')
        body = req.get_body().decode()
        logging.info(f'Request body: {body}')

        # Get job ID from request
        try:
            req_body = req.get_json()
            logging.info(f'Parsed request body: {req_body}')
        except ValueError as e:
            logging.error(f'JSON parsing error: {str(e)}')
            return func.HttpResponse(
                json.dumps({
                    "error": "Invalid JSON",
                    "details": str(e)
                }),
                status_code=400,
                mimetype="application/json"
            )

        job_id = req_body.get('job_id')
        image_url = req_body.get('image_url')
        
        logging.info(f'Extracted job_id: {job_id}, image_url: {image_url}')

        # Validate required environment variables
        required_vars = [
            "AzureWebJobsStorage",
            "SUBSCRIPTION_ID",
            "RESOURCE_GROUP",
            "FUNCTION_APP_NAME",
            "CONTAINER_IMAGE",
            "LOCATION"
        ]
        
        env_vars = {}
        missing_vars = []
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            env_vars[var] = 'present' if value else 'missing'
        
        logging.info(f'Environment variables status: {env_vars}')
        
        if missing_vars:
            error_msg = f'Missing required environment variables: {missing_vars}'
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({
                    "error": error_msg
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Connect to Azure Storage
        try:
            connection_string = os.environ["AzureWebJobsStorage"]
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            logging.info('Successfully connected to Azure Storage')
        except Exception as e:
            error_msg = f'Failed to connect to Azure Storage: {str(e)}'
            logging.error(error_msg)
            logging.error(f'Storage error details: {traceback.format_exc()}')
            return func.HttpResponse(
                json.dumps({
                    "error": error_msg,
                    "details": traceback.format_exc()
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Continue with your existing code...
        # But wrap each major operation in try/except blocks with logging

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        
        error_details = {
            "error_type": error_type,
            "error_message": error_msg,
            "stack_trace": stack_trace,
            "python_version": sys.version,
        }
        
        logging.error(f'Unhandled error in function:')
        logging.error(json.dumps(error_details, indent=2))
        
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": error_details
            }),
            status_code=500,
            mimetype="application/json"
        )