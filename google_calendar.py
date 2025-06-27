from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from datetime import datetime, timedelta
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def authenticate_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def get_events(service, time_min, time_max):
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

def create_event(service, summary, start, end):
    event = {
        'summary': summary,
        'start': {'dateTime': start, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end, 'timeZone': 'Asia/Kolkata'},
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

def is_time_slot_free(service, date_str, time_str, duration_str="30m", timezone="Asia/Kolkata"):
    from dateutil import parser

    now = datetime.now(pytz.timezone(timezone))

    if date_str.lower() == "tomorrow":
        target_date = now + timedelta(days=1)
    else:
        try:
            target_date = parser.parse(date_str)
        except Exception:
            return False, None, None

    if time_str.lower() == "afternoon":
        hour = 15
    elif time_str.lower() == "morning":
        hour = 10
    elif time_str.lower() == "evening":
        hour = 18
    else:
        try:
            parsed_time = parser.parse(time_str)
            hour = parsed_time.hour
        except:
            return False, None, None

    start_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
    if start_time.tzinfo is None:
        start_time = pytz.timezone(timezone).localize(start_time)

    # Duration
    minutes = int(duration_str.strip("m"))
    end_time = start_time + timedelta(minutes=minutes)

    # Query Calendar
    events = get_events(service, start_time.isoformat(), end_time.isoformat())

    if len(events) == 0:
        print(f"checking slot: {start_time} -> {end_time}")
        return True, start_time, end_time, None
    else:
        print(f"Events found: {len(events)}")
        suggested = None
        max_attempts = 8  # up to 4 hours ahead in 30-minute intervals
        for i in range(1, max_attempts + 1):
            new_start = start_time + timedelta(minutes=30 * i)
            new_end = new_start + timedelta(minutes=minutes)
    
            # Query for conflicts
            conflict = get_events(service, new_start.isoformat(), new_end.isoformat())
            if len(conflict) == 0:
                suggested = (new_start, new_end)
                break
        
        if suggested:
            print(f"Suggested free slot: {suggested[0]} → {suggested[1]}")
            return False, start_time, end_time, suggested 
        else:
            print("No free fallback slot found.")
            return False, start_time, end_time, None 

    