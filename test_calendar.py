from google_calendar import authenticate_google, get_events, create_event
import datetime

# Authenticate and get service
service = authenticate_google()

# List next 5 events
now = datetime.datetime.utcnow().isoformat() + 'Z'
end_of_week = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
events = get_events(service, now, end_of_week)

print("\nUpcoming events:")
for event in events:
    print(event['start'].get('dateTime', event['start'].get('date')), "-", event['summary'])

# test booking an event
# event_link = create_event(service, "Test Meeting", "2025-06-27T15:00:00", "2025-06-27T15:30:00")
# print("Event created:", event_link)
