from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Booking, SchemeType
from .forms import BookingForm
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
import re
from sender.models import ServerConfig
import paramiko
import logging

# Set up logging
logger = logging.getLogger(__name__)

def calendar_view(request):
    logger.info("Accessed the calendar view")
    success_message = None
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = "Booking was done successfully"
            logger.info("Booking saved successfully")
            return redirect('calendar')
    else:
        form = BookingForm()

    bookings = Booking.objects.all()
    events = []
    
    for booking in bookings:
        scheme_names = ', '.join([scheme.name for scheme in booking.scheme.all()])
        scheme_types = []
        for scheme_type in booking.scheme_type.all():
            match = re.search(r'port\.name\s+(\S+)\s+CurrentNode', scheme_type.type_name)
            if match:
                route_name = match.group(1)
                ip_port_match = re.search(r'cmmt:\S+\.(\d+\.\d+\.\d+\.\d+\.\d+)', scheme_type.type_name)
                if ip_port_match:
                    ip_port = ip_port_match.group(1)
                    formatted_name = f"{route_name}: {ip_port}"
                    scheme_types.append(formatted_name)

        scheme_types_str = ', '.join(scheme_types)
        event = {
            "id": booking.id,
            "title": f"{booking.project_name}-{booking.server.name}-{booking.time_slot}-{scheme_types_str}",
            "start": booking.start_date.strftime("%Y-%m-%d"),
            "end": (booking.end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "description": (
                f"Booking ID: {booking.booking_id}<br>"
                f"Project Name: {booking.project_name}<br>"
                f"PSP Name: {booking.psp_name}<br>"
                f"Owner: {booking.owner}<br>"
                f"Time Slots: {booking.time_slot}<br>"
                f"Server: {booking.server.name}<br>"
                f"Scheme Names: {scheme_names}<br>"
                f"Scheme Types: {scheme_types_str}"
            ),
        }
        events.append(event)

    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    current_year = datetime.now().year
    current_month = datetime.now().month - 1
    years = list(range(current_year - 10, current_year + 11))

    context = {
        'form': form,
        'events': json.dumps(events, cls=DjangoJSONEncoder),
        'success_message': success_message,
        'months': months,
        'years': years,
        'current_month': current_month,
        'current_year': current_year,
    }
    logger.debug("Rendering calendar with events")
    return render(request, 'bookings/calendar.html', context)

def delete_booking(request, booking_id):
    logger.info(f"Received delete request for Booking ID: {booking_id}")
    
    if request.method == 'POST' and request.POST.get('_method') == 'DELETE':
        try:
            booking = Booking.objects.get(id=booking_id)
            logger.info(f"Preparing to delete Booking with internal ID: {booking.id} - Owner: {booking.owner}")

            server_name = booking.server.name
            owner = booking.owner
            server_config = ServerConfig.objects.get(name=server_name)
            hostname = server_config.hostname
            ssh_command = f"ssh {owner}@{hostname}"
            logger.info(f"SSH Command: {ssh_command}")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=owner)

            list_cmd = f"crontab -l | grep 'Booking ID: {booking.booking_id}'"
            stdin, stdout, stderr = ssh.exec_command(list_cmd)
            matching_cron_entries = stdout.read().decode().strip()

            if matching_cron_entries:
                logger.info(f"Cron entries to be deleted for Booking ID {booking.booking_id}:\n{matching_cron_entries}")
                delete_cmd = f"crontab -l | grep -v 'Booking ID: {booking.booking_id}' | crontab -"
                stdin, stdout, stderr = ssh.exec_command(delete_cmd)
                if stderr.read().decode():
                    logger.error("Error in deleting cron jobs")
                    ssh.close()
                    return JsonResponse({"error": "Failed to update crontab"}, status=500)
            else:
                logger.info(f"No cron entries found for deletion for Booking ID {booking.booking_id}")

            ssh.close()
            booking.delete()
            logger.info(f"Successfully deleted Booking with internal ID: {booking.booking_id}")
            return JsonResponse({"status": "success", "id": booking.booking_id})
        except Booking.DoesNotExist:
            logger.error(f"No booking found with ID: {booking_id}")
            return JsonResponse({"error": "Booking not found"}, status=404)
        except ServerConfig.DoesNotExist:
            logger.error(f"Server configuration not found for {server_name}")
            return JsonResponse({"error": "Server configuration not found"}, status=404)
        except Exception as e:
            logger.error(f"Error during deletion process: {str(e)}")
            return JsonResponse({"error": "Deletion failed", "details": str(e)}, status=500)

    return JsonResponse({"status": "failed", "reason": "Invalid method or parameters"}, status=400)

def check_availability(request):
    date_range = request.GET.get('date_range')
    time_slot = request.GET.get('time_slot').split(',')
    try:
        start_date_str, end_date_str = date_range.split(' - ')
        start_date = datetime.strptime(start_date_str, '%m/%d/%Y').date()
        end_date = datetime.strptime(end_date_str, '%m/%d/%Y').date()
        logger.info(f"Checking availability from {start_date} to {end_date}")
    except ValueError:
        logger.error("Invalid date format")
        return JsonResponse({"error": "Invalid date format"}, status=400)
    
    existing_bookings = Booking.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    
    booked_schemes = set()
    for booking in existing_bookings:
        for slot in time_slot:
            if slot in booking.time_slot.split(','):
                booked_schemes.update(booking.schemes.split(','))

    logger.info("Availability check completed")
    return JsonResponse({"status": "success"})

def book_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            logger.info("New booking created successfully")
            return JsonResponse({"status": "success"})
        else:
            logger.error("Failed to create booking")
            return JsonResponse({"status": "failed", "errors": form.errors})
    logger.warning("Invalid request method for booking")
    return JsonResponse({"status": "invalid_method"}, status=405)

def load_scheme_types(request):
    scheme_ids = request.GET.get('scheme_ids').split(',')
    scheme_types = SchemeType.objects.filter(scheme_id__in=scheme_ids).order_by('type_name')
    
    options_html = ''
    
    for scheme_type in scheme_types:
        match = re.search(r'port\.name\s+(\S+)\s+CurrentNode', scheme_type.type_name)
        if match:
            route_name = match.group(1)
            ip_port_match = re.search(r'cmmt:\S+\.(\d+\.\d+\.\d+\.\d+\.\d+)', scheme_type.type_name)
            if ip_port_match:
                ip_port = ip_port_match.group(1)
                formatted_name = f"{route_name}: {ip_port}"
                options_html += f'<option value="{scheme_type.id}">{formatted_name}</option>'
            else:
                logger.error(f"Failed to extract IP:Port for {scheme_type.type_name}")

    return HttpResponse(options_html)
