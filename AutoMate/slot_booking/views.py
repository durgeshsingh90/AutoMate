import json
import paramiko
from pathlib import Path
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.apps import apps

# Define paths for configuration and booking files
app_base_dir = Path(apps.get_app_config('slot_booking').path)
CONFIG_DIR = app_base_dir / 'config'
BOOKINGS_FILE = CONFIG_DIR / 'bookings.json'

# View to render the calendar and load owners, servers, and scheme types from files
def calendar_view(request):
    # Load owners from the JSON file
    owners_file_path = CONFIG_DIR / 'owners.json'
    owners = []
    if owners_file_path.exists():
        with owners_file_path.open('r') as file:
            try:
                owners = json.load(file)
            except json.JSONDecodeError:
                owners = []

    # Load servers from the JSON file
    servers_file_path = CONFIG_DIR / 'servers.json'
    servers = []
    if servers_file_path.exists():
        with servers_file_path.open('r') as file:
            try:
                servers = json.load(file)
            except json.JSONDecodeError:
                servers = []

    # Load the scheme types from the istparam.cfg file
    istparam_file_path = CONFIG_DIR / 'istparam.cfg'
    scheme_types = []

    if istparam_file_path.exists():
        with istparam_file_path.open('r') as file:
            for line in file:
                line = line.strip()

                # Ignore comments (lines that start with '#') and empty lines
                if line.startswith('#') or not line:
                    continue

                # Split by space to extract the port.name and check for 'cmmt:'
                parts = line.split()
                if len(parts) >= 4 and parts[0] == "port.name":
                    port_name = parts[1]  # The second part is the port name
                    
                    # Look for the 'cmmt:' section and extract the IP from it
                    for part in parts:
                        if part.startswith('cmmt:'):
                            # Extract the IP part from cmmt: (cmmt:MASTERCARD_INSTANCE.10.20.7.208.2000)
                            cmmt_parts = part.split('.')
                            if len(cmmt_parts) >= 5:
                                ip_address = '.'.join(cmmt_parts[1:5])  # Extract only the IP (10.20.7.208)
                                scheme_types.append(f"{port_name} - {ip_address}")
                                break

    # Pass the owners, servers, and filtered scheme types data to the template
    return render(request, 'slot_booking/calendar.html', {
        'owners': owners, 
        'servers': servers, 
        'scheme_types': scheme_types
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
            new_scheme_types = request.POST.getlist('schemeType')  # Scheme types
            new_time_slots = request.POST.getlist('timeSlot')  # Time slots (AM, PM, Overnight)
            new_repeat_days = request.POST.getlist('repeatBooking')  # Repeat days (e.g., Tuesday)

            # Generate the cron expressions
            cron_entries = generate_cron_expression(start_date, end_date, new_repeat_days, new_time_slots)

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

            # Return the generated cron jobs as part of the response
            return JsonResponse({
                "message": "Booking saved successfully!",
                "cron_jobs": cron_entries
            })
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

def generate_cron_expression(start_date, end_date, repeat_days, time_slots):
    cron_entries = []

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
    if start_date.month == end_date.month:
        # If the start and end dates are within the same month
        cron_start = f"0 {earliest_start} {start_date.day}-{end_date.day} {start_date.month} {cron_days_of_week}"
        cron_end = f"0 {latest_end} {start_date.day}-{end_date.day} {start_date.month} {cron_days_of_week}"
    else:
        # For the start month (run from the start date to the end of the month)
        cron_start = f"0 {earliest_start} {start_date.day}-31 {start_date.month} {cron_days_of_week}"
        cron_end = f"0 {latest_end} {start_date.day}-31 {start_date.month} {cron_days_of_week}"

        # For the end month (run from the 1st day to the end date)
        cron_start_next_month = f"0 {earliest_start} 1-{end_date.day} {end_date.month} {cron_days_of_week}"
        cron_end_next_month = f"0 {latest_end} 1-{end_date.day} {end_date.month} {cron_days_of_week}"

        cron_entries.append(cron_start_next_month)
        cron_entries.append(cron_end_next_month)

    # Add the cron expressions for both the start and end times
    cron_entries.append(cron_start)
    cron_entries.append(cron_end)

    return cron_entries



import paramiko
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["POST"])
def add_cron_job(request):
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

            print(f"SSH connection established to {server} with user {owner}")

            # Prepare the cron job commands
            cron_job_commands = "\n".join([f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -' for cron_job in cron_jobs])

            # Prepare the full command to switch to 'f94gdos' user and add the cron jobs
            command = f"""
            sudo su - f94gdos -c 'bash -s' <<EOF
            {cron_job_commands}
            EOF
            """

            print(f"Executing command: {command}")

            # Execute the combined command to switch users and add cron jobs
            stdin, stdout, stderr = ssh.exec_command(command)

            # Capture the output and errors
            output = stdout.read().decode()
            error = stderr.read().decode()

            if error:
                return JsonResponse({'success': False, 'error': error}, status=500)

            ssh.close()
            print("SSH session closed.")

            return JsonResponse({'success': True, 'output': output})

        except paramiko.AuthenticationException:
            return JsonResponse({'success': False, 'error': 'Authentication failed.'}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
