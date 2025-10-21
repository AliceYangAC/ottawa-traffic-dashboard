import pytest
from unittest.mock import patch
from traffic_ingestor.helper_functions import publish_event

@pytest.mark.parametrize(
    "in_docker, expected_url",
    [
        (False, "127.0.0.1:7072"),       # host machine, override to localhost
        (True, "http://fake-refresher"), # inside Docker, keep provided URL
    ],
)
def test_publish_event_local_dev(in_docker, expected_url):
    with patch("traffic_ingestor.helper_functions.publish_event.requests.post") as mock_post, \
         patch("os.path.exists") as mock_exists:

        # Simulate Docker presence/absence
        mock_exists.return_value = in_docker
        mock_post.return_value.status_code = 200

        publish_event(
            EVENTGRID_TOPIC_ENDPOINT="unused",
            EVENTGRID_TOPIC_KEY="unused",
            LOCAL_DEV=True,
            REFRESHER_URL="http://fake-refresher"
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert expected_url in args[0]
