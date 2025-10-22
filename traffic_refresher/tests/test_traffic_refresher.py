import pytest
from unittest.mock import patch, MagicMock
import traffic_refresher.function_app as function_app

class DummyEvent:
    def get_json(self):
        return {"id": "test-id", "eventType": "Traffic.Ingested"}

def test_traffic_refresher_uploads_blob():
    # Fake entity with all required fields
    fake_entity = {
        "PartitionKey": "OttawaTraffic",
        "RowKey": "123",
        "GeoCoordinates": "[-75.69, 45.40]",
        "Location": "Accident on Highway 417",
        "EventType": "Collision",
        "Priority": "High",
        "Status": "ACTIVE"
    }

    with patch("traffic_refresher.function_app.TableServiceClient") as mock_tsc, \
         patch("traffic_refresher.function_app.BlobServiceClient") as mock_bsc, \
         patch("traffic_refresher.function_app.px.density_mapbox") as mock_px:

        # --- Mock Table ---
        mock_table_client = MagicMock()
        mock_table_client.list_entities.return_value = [fake_entity]
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # --- Mock Blob ---
        mock_blob_client = MagicMock()
        mock_bsc.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client

        # --- Mock Plotly ---
        mock_fig = MagicMock()
        mock_fig.to_image.return_value = b"fake-bytes"
        mock_px.return_value = mock_fig

        # Run the function
        function_app.traffic_refresher(DummyEvent())

        # Assert: Plotly was called with expected args
        mock_px.assert_called_once()
        # Assert: upload_blob was called with the fake image bytes
        mock_blob_client.upload_blob.assert_called_once_with(b"fake-bytes", overwrite=True)
