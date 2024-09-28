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


def save_booking(request):
    logger.debug("Saving booking")

    if request.method == 'POST':
        try:
            # Get the date range from the form and split it into start and end dates
            date_range = request.POST.get('dateRange')
            start_date, end_date = date_range.split(' - ')
            start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
            end_date = datetime.strptime(end_date, '%d/%m/%Y').date()

            # Collect other form data
            new_scheme_types = request.POST.getlist('schemeType')  # Scheme types (port names with IPs)
            new_time_slots = request.POST.getlist('timeSlot')  # Time slots (AM, PM, Overnight)
            new_repeat_days = request.POST.getlist('repeatBooking')  # Repeat days (e.g., Tuesday)

            # Generate the cron expressions with the script and parameters
            cron_entries = generate_cron_expression(start_date, end_date, new_repeat_days, new_time_slots, new_scheme_types)

            # Collect other form data to store in the booking
            booking_data = {
                'project_name': request.POST.get('projectName'),
                'psp_name': request.POST.get('pspName'),
                'owner': request.POST.get('owner'),
                'server': request.POST.get('server'),
                'scheme_types': new_scheme_types,
                'start_date': start_date.strftime('%d/%m/%Y'),
                'end_date': end_date.strftime('%d/%m/%Y'),
                'time_slots': new_time_slots,
                'repeat_days': new_repeat_days,
                'cron_jobs': cron_entries  # Save the cron expressions
            }

            # Ensure the config directory exists
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

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
            booking_data['booking_id'] = booking_id

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
    logger.debug("Getting bookings for FullCalendar")
    bookings = []
    
    if BOOKINGS_FILE.exists():
        try:
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)
                logger.info("Bookings data loaded successfully")
        except (json.JSONDecodeError, ValueError):
            logger.error(f"Error loading bookings from {BOOKINGS_FILE}")
            bookings = []

    events = []
    for booking in bookings:
        try:
            start_date = datetime.strptime(booking['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
            end_date = datetime.strptime(booking['end_date'], '%d/%m/%Y').strftime('%Y-%m-%d')

            event = {
                'id': booking['booking_id'],
                'title': booking['project_name'],
                'start': start_date,
                'end': end_date,
                'allDay': True
            }
            events.append(event)
            logger.debug(f"Added booking event for {booking['project_name']}")
        except ValueError as e:
            logger.error(f"Error parsing date for booking {booking['project_name']}: {str(e)}")

    logger.info("Bookings successfully converted to events for FullCalendar")
    return_data = JsonResponse(events, safe=False)
    logger.debug("Returning bookings data for FullCalendar")
    return return_data


@require_http_methods(["DELETE"])
def delete_booking(request, booking_id):
    logger.debug(f"Deleting booking with ID {booking_id}")
    
    if BOOKINGS_FILE.exists():
        try:
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)

            updated_bookings = [booking for booking in bookings if booking['booking_id'] != int(booking_id)]

            with BOOKINGS_FILE.open('w') as file:
                json.dump(updated_bookings, file, indent=4)

            logger.info(f"Booking {booking_id} deleted successfully")
            return_data = JsonResponse({"message": "Booking deleted successfully!"})
            logger.debug("Returning success response for delete booking")
            return return_data
        except Exception as e:
            logger.exception(f"Error deleting booking {booking_id}")
            return HttpResponseBadRequest(f"Error deleting booking: {str(e)}")
    
    logger.warning(f"Booking file not found while trying to delete booking {booking_id}")
    return HttpResponseBadRequest("Booking file not found.")


def generate_cron_expression(start_date, end_date, repeat_days, time_slots, scheme_types):
    logger.debug("Generating cron expressions with script parameters")
    cron_entries = []

    # Define a path to your script
    script_path = "/app/f94gdos/booking.sh"

    # Extract port names and IP addresses from the selected scheme types
    port_names = []
    ip_addresses = []

    for scheme in scheme_types:
        if ' - ' in scheme:
            port_name, ip_address = scheme.split(' - ')
            port_names.append(port_name)
            ip_addresses.append(ip_address)

    # Join port names and IP addresses into a single string for the cron job parameters
    port_names_str = ' '.join(port_names)
    ip_addresses_str = ' '.join(ip_addresses)

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

    # Determine the earliest start time and the latest end time based on selected time slots
    start_times = []
    end_times = []

    for time_slot in time_slots:
        start_time, end_time = time_slot_times[time_slot]
        start_times.append(start_time)
        end_times.append(end_time)

    # Get the earliest start time and the latest end time
    earliest_start = min(start_times)
    latest_end = max(end_times)

    # Handle repeat days: If empty, assume job should run every day
    cron_days_of_week = "*"
    if repeat_days:
        cron_days_of_week = ','.join(str(day_map[day]) for day in repeat_days)

    # Handle the case where start and end dates span across different months
    cron_entry_format = f"0 {{start_hour}} {{start_day}}-{{end_day}} {{start_month}} {{cron_days}} {script_path} {port_names_str} {ip_addresses_str}"
    
    if start_date.month == end_date.month:
        cron_start = cron_entry_format.format(
            start_hour=earliest_start,
            start_day=start_date.day,
            end_day=end_date.day,
            start_month=start_date.month,
            cron_days=cron_days_of_week
        )
        cron_end = cron_entry_format.format(
            start_hour=latest_end,
            start_day=start_date.day,
            end_day=end_date.day,
            start_month=start_date.month,
            cron_days=cron_days_of_week
        )
    else:
        cron_start = cron_entry_format.format(
            start_hour=earliest_start,
            start_day=start_date.day,
            end_day=31,
            start_month=start_date.month,
            cron_days=cron_days_of_week
        )
        cron_end = cron_entry_format.format(
            start_hour=latest_end,
            start_day=start_date.day,
            end_day=31,
            start_month=start_date.month,
            cron_days=cron_days_of_week
        )

        cron_start_next_month = cron_entry_format.format(
            start_hour=earliest_start,
            start_day=1,
            end_day=end_date.day,
            start_month=end_date.month,
            cron_days=cron_days_of_week
        )
        cron_end_next_month = cron_entry_format.format(
            start_hour=latest_end,
            start_day=1,
            end_day=end_date.day,
            start_month=end_date.month,
            cron_days=cron_days_of_week
        )

        cron_entries.append(cron_start_next_month)
        cron_entries.append(cron_end_next_month)

    # Add the cron expressions for both the start and end times
    cron_entries.append(cron_start)
    cron_entries.append(cron_end)

    logger.info("Cron expressions with script and parameters generated successfully")
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
