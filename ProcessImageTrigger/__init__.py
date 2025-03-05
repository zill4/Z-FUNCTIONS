import logging
import json
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
from azure.storage.table import TableClient
from azure.identity import DefaultAzureCredential
import datetime
import uuid

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Python HTTP trigger function processing request.')
        
        # Parse request
        try:
            req_body = req.get_json()
            job_id = req_body.get('job_id') or str(uuid.uuid4())
            image_url = req_body.get('image_url')
        except ValueError as e:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )

        if not image_url:
            return func.HttpResponse(
                json.dumps({"error": "image_url is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Initialize Azure clients using managed identity
        credential = DefaultAzureCredential()
        storage_account_url = f"https://{os.environ['STORAGE_ACCOUNT']}.blob.core.windows.net"
        
        # Create blob client
        blob_service_client = BlobServiceClient(
            account_url=storage_account_url,
            credential=credential
        )

        # Create queue client
        queue_client = QueueClient(
            account_url=storage_account_url.replace('blob', 'queue'),
            queue_name="processing-queue",
            credential=credential
        )

        # Create table client
        table_client = TableClient(
            endpoint=storage_account_url.replace('blob', 'table'),
            table_name="jobstatus",
            credential=credential
        )

        # Store job status in Table Storage
        table_client.create_entity({
            'PartitionKey': 'jobs',
            'RowKey': job_id,
            'status': 'pending',
            'created': datetime.datetime.utcnow().isoformat(),
            'image_url': image_url
        })

        # Queue the job message
        message = {
            'job_id': job_id,
            'image_url': image_url
        }
        queue_client.send_message(json.dumps(message))

        return func.HttpResponse(
            json.dumps({
                "success": True,
                "job_id": job_id,
                "status": "pending",
                "message": "Job queued successfully"
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f'Error: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )