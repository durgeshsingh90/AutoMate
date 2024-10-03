import json
import paramiko
import logging
from pathlib import Path
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.apps import apps
from calendar import monthrange

# Set up a logger for this module
logger = logging.getLogger('slot_booking')

# Define paths for configuration and booking files
app_base_dir = Path(apps.get_app_config('slot_booking').path)
CONFIG_DIR = app_base_dir / 'config'
BOOKINGS_FILE = CONFIG_DIR / 'bookings.json'


def calendar_view(request):
    logger.info("entering calendar_view")
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
    logger.info("Exiting calendar_view")

    return return_data

def save_booking(request):
    logger.info("entering save_booking")
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

            # Get server from the form
            server = request.POST.get('server')

            # Load the existing bookings data from the JSON file (if exists)
            if BOOKINGS_FILE.exists():
                with BOOKINGS_FILE.open('r') as file:
                    try:
                        bookings = json.load(file)
                    except json.JSONDecodeError:
                        bookings = []  # In case the file is empty or invalid
            else:
                bookings = []

            # Check for date range and time slot conflicts
            for existing_booking in bookings:
                # Convert existing booking's start and end dates to datetime
                existing_start_date = datetime.strptime(existing_booking['start_date'], '%d/%m/%Y').date()
                existing_end_date = datetime.strptime(existing_booking['end_date'], '%d/%m/%Y').date()

                # Check if server, scheme types, and date range overlap
                if (existing_booking['server'] == server and
                    set(existing_booking['scheme_types']) == set(scheme_types) and
                    # Check if date ranges overlap
                    not (end_date < existing_start_date or start_date > existing_end_date)):
                    
                    # Check for any overlapping time slots between the new booking and existing bookings
                    existing_time_slots = set(existing_booking['time_slots'])
                    if existing_time_slots & set(new_time_slots):  # Check if there's an intersection of time slots
                        logger.error("Booking conflict detected: One or more time slots and date ranges are already booked.")
                        return JsonResponse({
                            "error": "Booking conflict: The selected time slots and/or date range are already booked."
                        }, status=400)

            # Generate a new booking ID (increment the last one)
            if bookings:
                booking_id = max(b['booking_id'] for b in bookings) + 1
            else:
                booking_id = 1

            # Generate cron expressions
            cron_entries = generate_cron_expression(start_date, end_date, new_repeat_days, new_time_slots, scheme_types, booking_id, server, is_open_slot)

            # Collect other form data to store in the booking
            booking_data = {
                'project_name': request.POST.get('projectName'),
                'psp_name': request.POST.get('pspName'),
                'owner': request.POST.get('owner'),
                'server': server,
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
    logger.info("exiting save_booking")
    return HttpResponseBadRequest("Invalid request method.")

def get_bookings(request):
    logger.info("entering get_bookings")
    bookings = []
    
    if BOOKINGS_FILE.exists():
        try:
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)
        except (json.JSONDecodeError, ValueError):
            bookings = []  # If the file is empty or contains invalid JSON

    events = []
    
    # Load the servers with color coding
    servers = {}
    if CONFIG_DIR.joinpath('servers.json').exists():
        with open(CONFIG_DIR.joinpath('servers.json'), 'r') as servers_file:
            servers_list = json.load(servers_file)
            servers = {server['hostname']: server['color'] for server in servers_list}

    # Map repeat_days (e.g., "Tuesday") to crontab day of week numbers
    day_map = {
        "Sunday": 6, "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5
    }

    for booking in bookings:
        try:
            # Handle open slot where start_date and end_date are empty strings
            if booking['start_date'] == "" and booking['end_date'] == "":
                # Open slot booking logic (based on repeat_days)
                repeat_days = booking.get('repeat_days', [])
                time_slots = ', '.join(booking['time_slots']) if isinstance(booking['time_slots'], list) else booking['time_slots']
                scheme_types = ', '.join(booking['scheme_types']) if isinstance(booking['scheme_types'], list) else booking['scheme_types']

                # Retrieve the color based on the server hostname
                server_color = servers.get(booking['server'], '#000000')  # Default to black if no color is found

                # For each month, generate events for the specified repeat days
                for month in range(1, 13):  # Loop through all months
                    for day in range(1, 32):  # Loop through days in each month
                        try:
                            # Create a date object for each day
                            date = datetime(year=datetime.now().year, month=month, day=day)
                        except ValueError:
                            # Skip invalid dates (e.g., February 30th)
                            continue
                        
                        # Check if the current date's weekday matches any of the repeat days
                        if date.weekday() in [day_map[day] for day in repeat_days]:
                            events.append({
                                'id': booking['booking_id'],
                                'title': f"Open Slot - {time_slots} - {scheme_types}",
                                'start': date.strftime('%Y-%m-%d'),  # Use the date for the event
                                'end': None,  # No end date for each event
                                'color': server_color,  # Assign color based on the server
                                'allDay': True,
                                'extendedProps': {
                                    'booking_id': booking['booking_id'],
                                    'project_name': booking['project_name'],
                                    'owner': booking['owner'],
                                    'server': booking['server'],
                                    'scheme_types': scheme_types,
                                    'timeslot': time_slots,
                                    'start_date': 'Open',  # Represent as open
                                    'end_date': 'Open',    # Represent as open
                                    'cron_jobs': booking.get('cron_jobs', []),  # Cron jobs
                                    'repeat_days': repeat_days,  # Repeat days
                                }
                            })

            else:
                # Handle normal bookings with a specific date range
                start_date = datetime.strptime(booking['start_date'], '%d/%m/%Y')
                end_date = datetime.strptime(booking['end_date'], '%d/%m/%Y')

                server_color = servers.get(booking['server'], '#000000')  # Default to black if no color is found

                time_slots = ', '.join(booking['time_slots']) if isinstance(booking['time_slots'], list) else booking['time_slots']
                scheme_types = ', '.join(booking['scheme_types']) if isinstance(booking['scheme_types'], list) else booking['scheme_types']

                events.append({
                    'id': booking['booking_id'],
                    'title': f"{time_slots} - {scheme_types}",
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'color': server_color,  # Assign color based on the server
                    'allDay': True,
                    'extendedProps': {
                        'booking_id': booking['booking_id'],
                        'project_name': booking['project_name'],
                        'psp_name': booking.get('psp_name', 'N/A'),  # Include PSP name if available
                        'owner': booking['owner'],
                        'server': booking['server'],
                        'scheme_types': scheme_types,
                        'timeslot': time_slots,
                        'start_date': booking['start_date'],
                        'end_date': booking['end_date'],
                        'cron_jobs': booking.get('cron_jobs', []),  # Cron jobs
                        'repeat_days': booking.get('repeat_days', []),  # Repeat days
                    }
                })
        except ValueError as e:
            logger.error(f"Error parsing date for booking {booking['project_name']}: {str(e)}")
    
    logger.info("exiting get_bookings")
    return JsonResponse(events, safe=False)

@require_http_methods(["DELETE"])
def delete_booking(request, booking_id):
    logger.info("entering delete_booking")
    logger.debug(f"Received request to delete Booking ID: {booking_id}")

    try:
        # Load the existing bookings from the JSON file
        if BOOKINGS_FILE.exists():
            with BOOKINGS_FILE.open('r') as file:
                bookings = json.load(file)

            # Find the booking with the given booking_id
            booking_to_delete = None
            for booking in bookings:
                if booking['booking_id'] == int(booking_id):
                    booking_to_delete = booking
                    break

            if not booking_to_delete:
                logger.warning(f"Booking ID {booking_id} not found.")
                return HttpResponseBadRequest(f"Booking ID {booking_id} not found.")

            # Extract server and owner from the booking information
            server = booking_to_delete.get('server')
            owner = booking_to_delete.get('owner')

            if not server or not owner:
                logger.error(f"Server or owner information missing for Booking ID {booking_id}.")
                return JsonResponse({'success': False, 'error': 'Server or owner information missing.'}, status=400)

            # Filter out the booking from the list and update the JSON file
            updated_bookings = [booking for booking in bookings if booking['booking_id'] != int(booking_id)]

            # Write the updated bookings back to the JSON file
            with BOOKINGS_FILE.open('w') as file:
                json.dump(updated_bookings, file, indent=4)

            logger.info(f"Booking ID {booking_id} successfully deleted from the database.")

            # Now, login to the server and remove the cron jobs with the booking ID
            logger.info(f"Attempting to remove cron jobs for Booking ID {booking_id} from server {server}.")

            # Use paramiko to SSH into the server and remove cron jobs for the deleted booking
            result = remove_cron_jobs_from_server(booking_id, owner, server)

            if result.get('success'):
                logger.info(f"Cron jobs for Booking ID {booking_id} successfully removed from server {server}.")
                return JsonResponse({"message": "Booking and cron jobs deleted successfully!"})
            else:
                logger.error(f"Error removing cron jobs for Booking ID {booking_id}: {result.get('error')}")
                return JsonResponse(result, status=500)

        else:
            logger.error("Booking file not found.")
            return HttpResponseBadRequest("Booking file not found.")

    except Exception as e:
        logger.exception(f"Error deleting Booking ID {booking_id}: {str(e)}")
        logger.info("exiting delete_booking")
        return HttpResponseBadRequest(f"Error deleting booking: {str(e)}")


# Function to remove cron jobs based on the booking ID
def remove_cron_jobs_from_server(booking_id, owner, server):
    logger.info("entering remove_cron_jobs_from_server")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the server using paramiko
        ssh.connect(server, username=owner)
        logger.info(f"SSH connection established to {server} with user {owner} for Booking ID {booking_id}.")

        # Fetch current crontab entries for the user f94gdos
        command = "sudo su - f94gdos -c 'crontab -l'"
        stdin, stdout, stderr = ssh.exec_command(command)

        # Capture the current crontab
        crontab_output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            logger.error(f"Error fetching crontab for server {server}: {error}")
            return {'success': False, 'error': error}

        logger.debug(f"Crontab for server {server} fetched successfully.")

        # Filter out cron jobs related to the given booking_id
        updated_crontab = []
        for line in crontab_output.splitlines():
            if f"Booking ID: {booking_id}" not in line:  # If line does not contain the booking ID, keep it
                updated_crontab.append(line)
            else:
                logger.debug(f"Removing cron job: {line}")

        # Prepare the updated crontab (join list into a single string)
        updated_crontab_string = "\n".join(updated_crontab)

        # Update the crontab with the modified entries (excluding the deleted booking’s cron jobs)
        update_command = f"echo \"{updated_crontab_string}\" | sudo su - f94gdos -c 'crontab -'"
        stdin, stdout, stderr = ssh.exec_command(update_command)

        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            logger.error(f"Error updating crontab for server {server}: {error}")
            return {'success': False, 'error': error}

        logger.info(f"Cron jobs for Booking ID {booking_id} successfully removed from server {server}.")

        return {'success': True}

    except paramiko.AuthenticationException:
        logger.error(f"SSH authentication failed for server {server}.")
        return {'success': False, 'error': 'Authentication failed.'}
    except Exception as e:
        logger.error(f"SSH connection error for server {server}: {str(e)}")
        return {'success': False, 'error': str(e)}
    finally:
        ssh.close()
        logger.info("SSH session closed.")
        logger.info("exiting remove_cron_jobs_from_server")

        


def generate_cron_expression(start_date, end_date, repeat_days, time_slots, scheme_types, booking_id, server, is_open_slot=False):
    logger.info("entering generate_cron_expression")
    logger.debug("Generating cron expressions with script parameters")
    cron_entries = []

    # Define the path to your script and rollback script
    script_path = "/app/f94gdos/booking.sh"
    rollback_script_path = "/app/f94gdos/booking.sh"  # Same script path for rollback

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

    # Determine the rollback IP based on the server
    if server == "dev77":
        rollback_ip = "10.1.1.1"
    elif server == "test77":
        rollback_ip = "10.1.1.2"
    else:
        rollback_ip = "10.1.1.1"

    # For the rollback cron job, all port names should map to the rollback IP
    rollback_scheme_params = ' '.join([f"{port_name}:{rollback_ip}" for scheme_type in scheme_types for port_name, _ in [scheme_type.split(' - ')]])

    # Concatenate all selected scheme types (port_name and ip_address pairs) into a single string for the start script
    scheme_params = ' '.join([f"{port_name}:{ip_address}" for scheme_type in scheme_types for port_name, ip_address in [scheme_type.split(' - ')]])

    # Determine the earliest start time and latest end time based on selected time slots
    earliest_start_time = min([time_slot_times[slot][0] for slot in time_slots])
    latest_end_time = max([time_slot_times[slot][1] for slot in time_slots])

    # Handle open slot case, where only the start cron job must be created
    if is_open_slot:
        day_part = "*"
        month_part = "*"
        cron_days_of_week = "*"
        if repeat_days:
            cron_days_of_week = ','.join(str(day_map[day]) for day in repeat_days)

        # Create only the start cron job and omit the rollback job
        cron_entry = f"0 {earliest_start_time} * * {cron_days_of_week} {script_path} {scheme_params} # Booking ID: {booking_id}"
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

            # Create the start cron job at the earliest start time
            cron_entry = f"0 {earliest_start_time} {day_part} {month_part} {cron_days_of_week} {script_path} {scheme_params} # Booking ID: {booking_id}"
            cron_entries.append(cron_entry)

            # Add the rollback cron job at the latest end time
            rollback_entry = f"0 {latest_end_time} {day_part} {month_part} {cron_days_of_week} {rollback_script_path} {rollback_scheme_params} # Rollback Booking ID: {booking_id}"
            cron_entries.append(rollback_entry)

            # Move to the next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)

    logger.info(f"Cron expressions with booking ID {booking_id} generated successfully")
    logger.info("exiting generate_cron_expression")
    return cron_entries


@require_http_methods(["POST"])
def add_cron_job(request):
    logger.info("entering add_cron_job")

    try:
        data = json.loads(request.body)
        cron_jobs = data.get('cron_jobs', [])
        owner = data.get('owner', '')  # SSH username (owner)
        server = data.get('server', '')  # Server hostname

        if not owner or not server:
            return JsonResponse({'success': False, 'error': 'Owner or server information missing.'}, status=400)

        # Setup SSH connection using paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Use the default private key (~/.ssh/id_rsa) for SSH connection
            ssh.connect(server, username=owner)

            logger.info(f"SSH connection established to {server} with user {owner}")

            # Prepare and execute cron job commands one by one
            for cron_job in cron_jobs:
                # Prepare the command to add a cron job for user f94gdos
                cron_command = f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -'
                command = f"sudo su - f94gdos -c '{cron_command}'"
                
                logger.debug(f"Executing command: {command}")
                
                # Execute the command to add the cron job
                stdin, stdout, stderr = ssh.exec_command(command)

                # Capture output and errors
                output = stdout.read().decode()
                error = stderr.read().decode()

                if error:
                    return JsonResponse({'success': False, 'error': error}, status=500)

            ssh.close()
            logger.info("SSH session closed.")

            return JsonResponse({'success': True, 'output': 'Cron jobs successfully added to the server.'})

        except paramiko.AuthenticationException:
            return JsonResponse({'success': False, 'error': 'Authentication failed.'}, status=403)
        except Exception as e:
            logger.exception("SSH connection error.")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    except Exception as e:
        logger.exception("Error adding cron jobs via SSH.")
        logger.info("exiting add_cron_job")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


