import json
import paramiko
import logging
from pathlib import Path
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.apps import apps

# Set up a logger for this module
logger = logging.getLogger('myapp')

# Define paths for configuration and booking files
app_base_dir = Path(apps.get_app_config('slot_booking').path)
CONFIG_DIR = app_base_dir / 'config'
BOOKINGS_FILE = CONFIG_DIR / 'bookings.json'


def calendar_view(request):
    logger.debug("Rendering calendar view")

    owners_file_path = CONFIG_DIR / 'owners.json'
    owners = []
    
    if owners_file_path.exists():
        logger.debug(f"Loading owners from {owners_file_path}")
        with owners_file_path.open('r') as file:
            try:
                owners = json.load(file)
                logger.info("Owners data loaded successfully")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from {owners_file_path}")
                owners = []

    servers_file_path = CONFIG_DIR / 'servers.json'
    servers = []
    
    if servers_file_path.exists():
        logger.debug(f"Loading servers from {servers_file_path}")
        with servers_file_path.open('r') as file:
            try:
                servers = json.load(file)
                logger.info("Servers data loaded successfully")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from {servers_file_path}")
                servers = []

    istparam_file_path = CONFIG_DIR / 'istparam.cfg'
    scheme_types = []
    
    if istparam_file_path.exists():
        logger.debug(f"Loading scheme types from {istparam_file_path}")
        with istparam_file_path.open('r') as file:
            for line in file:
                line = line.strip()

                if line.startswith('#') or not line:
                    continue

                parts = line.split()
                if len(parts) >= 4 and parts[0] == "port.name":
                    port_name = parts[1]
                    
                    for part in parts:
                        if part.startswith('cmmt:'):
                            cmmt_parts = part.split('.')
                            if len(cmmt_parts) >= 5:
                                ip_address = '.'.join(cmmt_parts[1:5])
                                scheme_types.append(f"{port_name} - {ip_address}")
                                logger.debug(f"Extracted IP address: {ip_address} for port: {port_name}")
                                break

    logger.info("Calendar view data loaded successfully")
    return_data = render(request, 'slot_booking/calendar.html', {
        'owners': owners, 
        'servers': servers, 
        'scheme_types': scheme_types
    })
    logger.debug("Returning calendar view response")
    return return_data


import json
from datetime import datetime

def save_booking(request):
    logger.debug("Saving booking")

    if request.method == 'POST':
        try:
            # Check if "dateRange" is missing, treat as open slot
            date_range = request.POST.get('dateRange', None)
            is_open_slot = date_range is None or date_range == '*'

            # Handle open slot case
            if is_open_slot:
                start_date = "*"
                end_date = "*"
                new_repeat_days = request.POST.getlist('repeatBooking', ['Tuesday', 'Thursday'])  # Use default repeat days for open slot
                new_time_slots = ['AM']  # Default time slot for open slots
            else:
                # If date range is provided, split into start and end dates
                start_date, end_date = date_range.split(' - ')
                start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
                end_date = datetime.strptime(end_date, '%d/%m/%Y').date()

                # Get time slots and repeat days for a normal booking
                new_time_slots = request.POST.getlist('timeSlot')  # Time slots (AM, PM, Overnight)
                new_repeat_days = request.POST.getlist('repeatBooking')  # Repeat days (e.g., Tuesday)

            # Get scheme types from the form
            scheme_types = request.POST.getlist('schemeType')  # Scheme types

            # Load the existing bookings data from the JSON file (if exists)
            if BOOKINGS_FILE.exists():
                with BOOKINGS_FILE.open('r') as file:
                    try:
                        bookings = json.load(file)
                    except json.JSONDecodeError:
                        bookings = []  # In case the file is empty or invalid
            else:
                bookings = []

            # Generate a new booking ID (increment the last one)
            if bookings:
                booking_id = max(b['booking_id'] for b in bookings) + 1
            else:
                booking_id = 1

            # Generate cron expressions
            cron_entries = generate_cron_expression(start_date, end_date, new_repeat_days, new_time_slots, scheme_types, booking_id, is_open_slot)

            # Collect other form data to store in the booking
            booking_data = {
                'project_name': request.POST.get('projectName'),
                'psp_name': request.POST.get('pspName'),
                'owner': request.POST.get('owner'),
                'server': request.POST.get('server'),
                'scheme_types': scheme_types,  # Scheme types
                'start_date': start_date.strftime('%d/%m/%Y') if start_date != '*' else '',  # Convert date to string or empty if it's an open slot
                'end_date': end_date.strftime('%d/%m/%Y') if end_date != '*' else '',  # Convert date to string or empty if it's an open slot
                'time_slots': new_time_slots,
                'repeat_days': new_repeat_days,
                'cron_jobs': cron_entries,  # Save the cron expressions
                'booking_id': booking_id  # Save the booking ID
            }

            # Add the new booking to the list
            bookings.append(booking_data)

            # Write the updated list back to the JSON file
            with BOOKINGS_FILE.open('w') as file:
                json.dump(bookings, file, indent=4)

            logger.info(f"Booking {booking_id} saved successfully")

            # Return the generated cron jobs as part of the response
            return JsonResponse({
                "message": "Booking saved successfully!",
                "cron_jobs": cron_entries  # This will be shown in the pop-up screen
            })
        except Exception as e:
            logger.exception("Error saving booking")
            return HttpResponseBadRequest(f"Error saving booking: {str(e)}")

    logger.warning("Invalid request method for saving booking")
    return HttpResponseBadRequest("Invalid request method.")

def get_bookings(request):
    bookings = []
    
    if BOOKINGS_FILE.exists():
        try:
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)
        except (json.JSONDecodeError, ValueError):
            bookings = []  # If the file is empty or contains invalid JSON

    events = []
    
    # Map repeat_days (e.g., "Tuesday") to crontab day of week numbers
    day_map = {
        "Sunday": 6, "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5
    }

    for booking in bookings:
        try:
            # If no start and end date, handle as open slot with repeat days
            if not booking['start_date'] and not booking['end_date']:
                # Open slot: create events throughout the year for repeat days
                repeat_days = booking.get('repeat_days', [])
                for month in range(1, 13):  # Loop through months
                    for day in range(1, 32):  # Loop through days in the month
                        try:
                            date = datetime(year=datetime.now().year, month=month, day=day)
                        except ValueError:
                            continue  # Skip invalid dates

                        if date.weekday() in [day_map[day] for day in repeat_days]:
                            events.append({
                                'id': booking['booking_id'],
                                'title': booking['project_name'],
                                'start': date.strftime('%Y-%m-%d'),
                                'allDay': True
                            })
            else:
                # Handle normal bookings with a specific date range
                start_date = datetime.strptime(booking['start_date'], '%d/%m/%Y')
                end_date = datetime.strptime(booking['end_date'], '%d/%m/%Y')
                events.append({
                    'id': booking['booking_id'],
                    'title': booking['project_name'],
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'allDay': True
                })
        except ValueError as e:
            logger.error(f"Error parsing date for booking {booking['project_name']}: {str(e)}")

    return JsonResponse(events, safe=False)


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


from calendar import monthrange

from calendar import monthrange

def generate_cron_expression(start_date, end_date, repeat_days, time_slots, scheme_types, booking_id, is_open_slot=False):
    logger.debug("Generating cron expressions with script parameters")
    cron_entries = []

    # Define the path to your script
    script_path = "/app/f94gdos/booking.sh"

    # Map repeat_days (e.g., "Tuesday") to crontab day of week numbers
    day_map = {
        "Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3,
        "Thursday": 4, "Friday": 5, "Saturday": 6
    }

    # Time slot start and end times
    time_slot_times = {
        "AM": (8, 13),  # Start at 8 AM, end at 1 PM
        "PM": (13, 18),  # Start at 1 PM, end at 6 PM
        "Overnight": (18, 8)  # Start at 6 PM, end at 8 AM the next day
    }

    # Concatenate all selected scheme types (port_name and ip_address pairs) into a single string
    scheme_params = ' '.join([f"{port_name}:{ip_address}" for scheme_type in scheme_types for port_name, ip_address in [scheme_type.split(' - ')]])

    # Handle open slot case, where start_date and end_date are '*'
    if is_open_slot:
        day_part = "*"
        month_part = "*"
        cron_days_of_week = "*"
        if repeat_days:
            cron_days_of_week = ','.join(str(day_map[day]) for day in repeat_days)

        # Create a cron job with * for day and month
        for time_slot in time_slots:
            start_time = time_slot_times[time_slot][0]
            cron_entry = f"0 {start_time} * * {cron_days_of_week} {script_path} {scheme_params} # Booking ID: {booking_id}"
            cron_entries.append(cron_entry)

    else:
        # Generate cron jobs for each month between start_date and end_date
        current_date = start_date
        while current_date <= end_date:
            # Get the last day of the current month
            last_day_of_month = monthrange(current_date.year, current_date.month)[1]

            if current_date == start_date and current_date == end_date:
                # If start_date and end_date are the same, use a single day
                day_part = f"{start_date.day}"
            elif current_date.month == start_date.month and current_date.month == end_date.month:
                # If the booking starts and ends in the same month, use a day range
                day_part = f"{start_date.day}-{end_date.day}"
            elif current_date.month == start_date.month:
                # If it's the starting month, use start_date.day as the starting day
                day_part = f"{start_date.day}-{last_day_of_month}"
            elif current_date.month == end_date.month:
                # If it's the ending month, use end_date.day as the ending day
                day_part = f"1-{end_date.day}"
            else:
                # Otherwise, it's a full month, so use 1 to the last day of the month
                day_part = f"1-{last_day_of_month}"

            # Set the month part
            month_part = f"{current_date.month}"

            # Set the cron days of the week if repeat_days are selected
            cron_days_of_week = "*"
            if repeat_days:
                cron_days_of_week = ','.join(str(day_map[day]) for day in repeat_days)

            # Create cron jobs for each time slot
            for time_slot in time_slots:
                start_time = time_slot_times[time_slot][0]
                cron_entry = f"0 {start_time} {day_part} {month_part} {cron_days_of_week} {script_path} {scheme_params} # Booking ID: {booking_id}"
                cron_entries.append(cron_entry)

            # Move to the next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)

    logger.info(f"Cron expressions with booking ID {booking_id} generated successfully")
    return cron_entries

@require_http_methods(["POST"])
def add_cron_job(request):
    logger.debug("Adding cron job via SSH")
    
    try:
        data = json.loads(request.body)
        cron_jobs = data.get('cron_jobs', [])
        owner = data.get('owner', '')
        server = data.get('server', '')

        if not owner or not server:
            logger.warning("Missing owner or server in request data")
            return JsonResponse({'success': False, 'error': 'Owner or server information missing.'}, status=400)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(server, username=owner)
            logger.info(f"SSH connection established to {server} with user {owner}")

            cron_job_commands = "\n".join([f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -' for cron_job in cron_jobs])

            command = f"""
            sudo su - f94gdos -c 'bash -s' <<EOF
            {cron_job_commands}
            EOF
            """
            logger.debug(f"Executing SSH command: {command}")

            stdin, stdout, stderr = ssh.exec_command(command)

            output = stdout.read().decode()
            error = stderr.read().decode()

            if error:
                logger.error(f"Error during SSH execution: {error}")
                return JsonResponse({'success': False, 'error': error}, status=500)

            ssh.close()
            logger.info("SSH session closed")

            return_data = JsonResponse({'success': True, 'output': output})
            logger.debug("Returning success response for add cron job")
            return return_data

        except paramiko.AuthenticationException:
            logger.error("SSH authentication failed")
            return JsonResponse({'success': False, 'error': 'Authentication failed.'}, status=403)
        except Exception as e:
            logger.exception("Error during SSH connection")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    except Exception as e:
        logger.exception("Error processing cron job addition")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
