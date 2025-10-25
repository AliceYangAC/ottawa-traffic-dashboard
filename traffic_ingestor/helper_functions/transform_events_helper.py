from datetime import datetime

def transform_events(events):
    entities = []

    for event in events:
        try:
            row_key = str(event.get("id", "unknown"))
            event_type = event.get("eventType", "UNKNOWN")
            location = event.get("headline", "Unknown location")
            priority = event.get("priority", "UNKNOWN")
            status = event.get("status", "UNKNOWN")

            # Extract start/end times from schedule
            schedule = event.get("schedule", [])
            start_time = schedule[0].get("startDateTime") if schedule else None
            end_time = schedule[0].get("endDateTime") if schedule else None

            # Normalize geodata
            geodata = event.get("geodata", {}).get("coordinates", None)

            entity = {
                "PartitionKey": "OttawaTraffic",
                "RowKey": row_key,
                "EventType": event_type,
                "Location": location,
                "StartTime": start_time,
                "EndTime": end_time,
                "Priority": priority,
                "Status": status,
                "GeoCoordinates": geodata
            }

            entities.append(entity)
        except Exception as e:
            print(f"Failed to transform event {event.get('id', 'unknown')}: {e}")

    return entities
