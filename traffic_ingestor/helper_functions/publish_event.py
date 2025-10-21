import os
import requests
from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from azure.core.credentials import AzureKeyCredential

def publish_event(EVENTGRID_TOPIC_ENDPOINT, EVENTGRID_TOPIC_KEY, LOCAL_DEV, REFRESHER_URL):
    if LOCAL_DEV:
        # Checks if you are running locally instead of in containers
        if os.path.exists("/.dockerenv") == False:
            REFRESHER_URL = "http://127.0.0.1:7072/runtime/webhooks/EventGrid?functionName=TrafficRefresher"

        payload = [{
            "id": "local-test",
            "eventType": "Traffic.Ingested",
            "subject": "traffic/ingestion",
            "eventTime": "2025-10-21T14:00:00Z",
            "data": {"message": "New traffic events ingested"},
            "dataVersion": "1.0"
        }]
        headers = {
            "aeg-event-type": "Notification",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(REFRESHER_URL, json=payload, headers=headers, timeout=5)
            print(f"Mock Event Grid POST -> refresher: {resp.status_code}")
        except Exception as e:
            print(f"Failed to POST mock event to refresher: {e}")
    else:
        # Real Event Grid publish
        credential = AzureKeyCredential(EVENTGRID_TOPIC_KEY)
        client = EventGridPublisherClient(EVENTGRID_TOPIC_ENDPOINT, credential)
        event = EventGridEvent(
            subject="traffic/ingestion",
            data={"message": "New traffic events ingested"},
            event_type="Traffic.Ingested",
            data_version="1.0"
        )
        client.send([event])
        print("Published Event Grid notification: Traffic.Ingested")
