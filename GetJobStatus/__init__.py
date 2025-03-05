import logging
import json
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
from azure.storage.table import TableClient
from azure.identity import DefaultAzureCredential

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Get job_id
        job_id = req.params.get('job_id')
        if not job_id:
            try:
                req_body = req.get_json()
                job_id = req_body.get('job_id')
            except ValueError:
                job_id = None

        if not job_id:
            return func.HttpResponse(
                "Please provide job_id parameter",
                status_code=400
            )

        # Use managed identity
        credential = DefaultAzureCredential()
        storage_account_url = f"https://{os.environ['STORAGE_ACCOUNT']}.table.core.windows.net"
        
        # Get status from Table Storage
        table_client = TableClient(
            endpoint=storage_account_url,
            table_name="jobstatus",
            credential=credential
        )

        try:
            status_entity = table_client.get_entity('jobs', job_id)
            return func.HttpResponse(
                json.dumps(dict(status_entity)),
                mimetype="application/json"
            )
        except Exception as e:
            return func.HttpResponse(
                json.dumps({
                    "job_id": job_id,
                    "status": "unknown",
                    "error": f"Could not retrieve job status: {str(e)}"
                }),
                status_code=404,
                mimetype="application/json"
            )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        ) 