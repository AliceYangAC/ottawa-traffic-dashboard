# traffic_refresher/tests/test_traffic_refresher.py
import pytest
from unittest.mock import patch, MagicMock
from traffic_refresher.function_app import traffic_refresher
import azure.functions as func
import os
from dotenv import load_dotenv
from azure.functions import EventGridEvent

# Load environment variables
load_dotenv(dotenv_path="traffic_refresher/.env")

def test_traffic_refresher_generates_and_uploads_map():
    # Fake entity from Table Storage
    fake_entity = {
        "PartitionKey": "OttawaTraffic",
        "RowKey": "123-Collision",
        "GeoCoordinates": "[-75.69, 45.40]",
        "Location": "Accident on Highway 417",
        "EventType": "Collision",
        "Priority": "High",
        "Status": "ACTIVE"
    }

    with patch("traffic_refresher.function_app.TableServiceClient") as mock_tsc, \
         patch("traffic_refresher.function_app.BlobServiceClient") as mock_bsc, \
         patch("traffic_refresher.function_app.px.density_mapbox") as mock_px:

        # Mock Table client 
        mock_table_client = MagicMock()
        mock_table_client.list_entities.return_value = [fake_entity]
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # Mock Blob client 
        mock_blob_client = MagicMock()
        mock_bsc.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client

        # Mock Plotly figure 
        mock_fig = MagicMock()
        mock_fig.to_image.return_value = b"fake-image-bytes"
        mock_px.return_value = mock_fig

        dummy_event = EventGridEvent(
            id="test-id",
            data={"message": "New traffic events ingested"},
            topic="/subscriptions/fake-sub/resourceGroups/fake-rg/providers/Microsoft.EventGrid/topics/fake-topic",
            subject="traffic/ingestion",
            event_type="Traffic.Ingested",
            event_time="2025-10-21T14:00:00Z",
            data_version="1.0"
        )

        traffic_refresher(dummy_event)

        # Assert: Table queried and blob uploaded
        mock_table_client.list_entities.assert_called_once()
        mock_px.assert_called_once()
        mock_blob_client.upload_blob.assert_called_once_with(b"fake-image-bytes", overwrite=True)
