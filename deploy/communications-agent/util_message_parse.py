import re

def parse_booking_message(message):
    """
    Extract organiser name and attendee names from a booking message string.
    Returns organiser_name, attendee_names (list)
    """
    # Example message format:
    # "Event booked by John Doe for members of the UCL AI Society: Alice Smith, Bob Lee, Carol Jones"
    organiser_match = re.search(r'booked by ([\w .-]+)', message)
    organiser_name = organiser_match.group(1).strip() if organiser_match else None

    attendees_match = re.search(r'members? of [\w .-]+: (.+)', message)
    if attendees_match:
        attendees_str = attendees_match.group(1)
        attendee_names = [name.strip() for name in attendees_str.split(',')]
    else:
        attendee_names = []
    return organiser_name, attendee_names
