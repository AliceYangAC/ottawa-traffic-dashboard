import os
import requests
from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from azure.core.credentials import AzureKeyCredential
from datetime import datetime, timezone
import uuid

def publish_events(events):
    REFRESHER_URL = "http://localhost:7072/runtime/webhooks/eventgrid?functionName=TrafficRefresher"

    payload = [{
        "id": str(uuid.uuid4()),
        "eventType": "Traffic.Ingested",
        "subject": "traffic/ingestion",
        "eventTime": datetime.now(timezone.utc).isoformat(),
        "data": {"events": events},
        "dataVersion": "1.0",
        "metadataVersion": "1"
    }]


    headers = {
        "aeg-event-type": "Notification",
        "Content-Type": "application/json"
    }

    #print("Sample event:", payload[0]["data"]["events"][0])


    try:
        resp = requests.post(REFRESHER_URL, json=payload, headers=headers, timeout=5)
        print(f"Mock Event Grid POST -> refresher: {resp}")
    except Exception as e:
        print(f"Failed to POST mock event to refresher: {e}")

    # else:
    #     # Real Event Grid publish
    #     credential = AzureKeyCredential(EVENTGRID_TOPIC_KEY)
    #     client = EventGridPublisherClient(EVENTGRID_TOPIC_ENDPOINT, credential)
    #     event = EventGridEvent(
    #         subject="traffic/ingestion",
    #         data={"message": "New traffic events ingested"},
    #         event_type="Traffic.Ingested",
    #         data_version="1.0"
    #     )
    #     client.send([event])
    #     print("Published Event Grid notification: Traffic.Ingested")