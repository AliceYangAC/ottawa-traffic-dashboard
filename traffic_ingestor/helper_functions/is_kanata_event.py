KANATA_KEYWORDS = [
    "Kanata", "March Road", "Terry Fox Drive", "Eagleson Road",
    "Carling Avenue", "Legget Drive", "Solandt Road", "Campeau Drive",
    "Innovation Drive", "Klondike Road", "Huntmar Drive"
]

# Helper function to see if the traffic event if near a Kanata street
def is_kanata_event(event):
    location = event.get("location", {})
    description = location.get("description", "").lower()
    return any(keyword.lower() in description for keyword in KANATA_KEYWORDS)