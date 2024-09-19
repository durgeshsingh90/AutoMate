import json
from pathlib import Path
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.apps import apps
from django.conf import settings

# Define paths for configuration and booking files
app_base_dir = Path(apps.get_app_config('slot_booking').path)
CONFIG_DIR = app_base_dir / 'config'
BOOKINGS_FILE = CONFIG_DIR / 'bookings.json'

# View to render the calendar and load owners, servers, and scheme types from files
def calendar_view(request):
    # Load owners from owners.json
    owners_file_path = CONFIG_DIR / 'owners.json'
    owners = []
    if owners_file_path.exists():
        with owners_file_path.open('r') as file:
            try:
                owners = json.load(file)
            except json.JSONDecodeError:
                owners = []

    # Load servers from servers.json
    servers_file_path = CONFIG_DIR / 'servers.json'
    servers = []
    if servers_file_path.exists():
        with servers_file_path.open('r') as file:
            try:
                servers = json.load(file)
            except json.JSONDecodeError:
                servers = []

    # Load scheme types from istparam.cfg
    istparam_file_path = CONFIG_DIR / 'istparam.cfg'
    scheme_types = []
    if istparam_file_path.exists():
        with istparam_file_path.open('r') as file:
            scheme_types = [line.strip() for line in file if line.strip()]

    # Pass the owners, servers, and scheme types data to the template
    return render(request, 'slot_booking/calendar.html', {
        'owners': owners,
        'servers': servers,
        'scheme_types': scheme_types,
    })

# View to save bookings with an incrementing booking_id
def save_booking(request):
    if request.method == 'POST':
        try:
            # Get the date range from the form and split it into start and end dates
            date_range = request.POST.get('dateRange')
            start_date, end_date = date_range.split(' - ')
            start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
            end_date = datetime.strptime(end_date, '%d/%m/%Y').date()

            # Collect other form data
            new_scheme_types = request.POST.getlist('schemeType')  # Multiple selected scheme types
            new_time_slots = request.POST.getlist('timeSlot')  # Multiple checkboxes for time slots
            new_repeat_days = request.POST.getlist('repeatBooking')  # Repeat days (if applicable)

            # Load the existing bookings data from the JSON file (if exists)
            if BOOKINGS_FILE.exists():
                with BOOKINGS_FILE.open('r') as file:
                    try:
                        bookings = json.load(file)
                    except json.JSONDecodeError:
                        bookings = []  # In case the file is empty or invalid
            else:
                bookings = []

            # Check for double bookings (same scheme type, overlapping date range, and same time slot)
            for booking in bookings:
                booking_start_date = datetime.strptime(booking['start_date'], '%d/%m/%Y').date()
                booking_end_date = datetime.strptime(booking['end_date'], '%d/%m/%Y').date()

                # Check if date ranges overlap
                if not (end_date < booking_start_date or start_date > booking_end_date):
                    # Check if scheme type and time slot overlap
                    if any(scheme in new_scheme_types for scheme in booking['scheme_types']) and any(slot in new_time_slots for slot in booking['time_slots']):
                        return HttpResponseBadRequest("Error: A booking with the same Scheme Type, Date Range, and Time Slot already exists.")

            # No conflict found, proceed to save the new booking
            booking_data = {
                'project_name': request.POST.get('projectName'),
                'psp_name': request.POST.get('pspName'),
                'owner': request.POST.get('owner'),  # Captures the selected owner ID
                'server': request.POST.get('server'),  # Captures the selected server hostname
                'scheme_types': new_scheme_types,  # Captures multiple selected scheme types
                'start_date': start_date.strftime('%d/%m/%Y'),
                'end_date': end_date.strftime('%d/%m/%Y'),
                'time_slots': new_time_slots,  # Multiple checkboxes
                'repeat_days': new_repeat_days,  # Multiple checkboxes
            }

            # Generate a new booking ID (increment the last one)
            if bookings:
                booking_id = max(b['booking_id'] for b in bookings) + 1
            else:
                booking_id = 1
            booking_data['booking_id'] = booking_id

            # Add the new booking to the list
            bookings.append(booking_data)

            # Write the updated list back to the JSON file
            with BOOKINGS_FILE.open('w') as file:
                json.dump(bookings, file, indent=4)

            return HttpResponse("Booking saved successfully!")
        except Exception as e:
            return HttpResponseBadRequest(f"Error saving booking: {str(e)}")

    return HttpResponseBadRequest("Invalid request method.")

# View to return bookings for FullCalendar
def get_bookings(request):
    bookings = []
    if BOOKINGS_FILE.exists():
        try:
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)
        except (json.JSONDecodeError, ValueError):
            bookings = []  # If the file is empty or contains invalid JSON

    # Convert bookings into events for FullCalendar
    events = []
    for booking in bookings:
        try:
            # Convert 'DD/MM/YYYY' to 'YYYY-MM-DD' for FullCalendar
            start_date = datetime.strptime(booking['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
            end_date = datetime.strptime(booking['end_date'], '%d/%m/%Y').strftime('%Y-%m-%d')

            # Create an event object for FullCalendar
            event = {
                'id': booking['booking_id'],
                'title': booking['project_name'],
                'start': start_date,
                'end': end_date,
                'allDay': True  # FullCalendar default for full-day events
            }
            events.append(event)
        except ValueError as e:
            print(f"Error parsing date for booking: {booking['project_name']}. Error: {str(e)}")

    # Return the events in JSON format to FullCalendar
    return JsonResponse(events, safe=False)

# View to delete a booking
@require_http_methods(["DELETE"])
def delete_booking(request, booking_id):
    if BOOKINGS_FILE.exists():
        try:
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)

            # Filter out the booking with the given booking_id
            updated_bookings = [booking for booking in bookings if booking['booking_id'] != int(booking_id)]

            # Write the updated bookings back to the JSON file
            with BOOKINGS_FILE.open('w') as file:
                json.dump(updated_bookings, file, indent=4)

            return JsonResponse({"message": "Booking deleted successfully!"})
        except Exception as e:
            return HttpResponseBadRequest(f"Error deleting booking: {str(e)}")
    
    return HttpResponseBadRequest("Booking file not found.")
