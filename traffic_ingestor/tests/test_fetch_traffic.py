# import pytest
# from unittest.mock import patch
# from traffic_ingestor.function_app import fetch_traffic_events

# @patch("traffic_ingestor.function_app.requests.get")
# @patch("traffic_ingestor.function_app.store_event_in_table")
# @patch("traffic_ingestor.function_app.cleanup_inactive_events")
# def test_fetch_traffic_events(mock_cleanup, mock_store, mock_get, mock_traffic_response):
#     mock_get.return_value = mock_traffic_response

#     req = None
#     response = fetch_traffic_events(req)

#     assert response.status_code == 200
#     assert "Collision" in response.get_body().decode()

#     # The function should be called once for the high-priority event
#     mock_store.assert_called_once()
#     mock_cleanup.assert_called_once()