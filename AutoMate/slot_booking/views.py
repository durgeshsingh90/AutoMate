from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import json
import os

BASE_DIR = settings.BASE_DIR
CONFIG_PATH = os.path.join(BASE_DIR, 'slot_booking', 'static', 'slot_booking', 'config.json')
SUBMISSIONS_FILE = os.path.join(BASE_DIR, 'slot_booking', 'static', 'slot_booking', 'submissions.json')
COUNTER_FILE = os.path.join(BASE_DIR, 'slot_booking', 'static', 'slot_booking', 'counter.json')

def ensure_files_exist():
    os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)
    if not os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, 'w') as file:
            json.dump({"submissions": []}, file)
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as file:
            json.dump({"last_booking_id": 0}, file)

def read_counter():
    with open(COUNTER_FILE, 'r') as file:
        data = json.load(file)
        return data.get('last_booking_id', 0)

def write_counter(counter):
    with open(COUNTER_FILE, 'w') as file:
        json.dump({'last_booking_id': counter}, file)

def index(request):
    return render(request, 'slot_booking/index.html')

def admin(request):
    return render(request, 'slot_booking/admin.html')

def config(request):
    if request.method == 'GET':
        try:
            with open(CONFIG_PATH, 'r') as file:
                config_data = json.load(file)
                return JsonResponse(config_data, safe=False)
        except FileNotFoundError:
            return HttpResponse("Config file not found", status=404)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            with open(CONFIG_PATH, 'w') as file:
                json.dump(data, file, indent=4)
            return HttpResponse("Config saved successfully", status=200)
        except Exception as e:
            return HttpResponse(f"Failed to save config: {str(e)}", status=500)

def is_date_range_overlap(start1, end1, start2, end2):
    from datetime import datetime
    start1 = datetime.strptime(start1, "%d/%m/%Y")
    end1 = datetime.strptime(end1, "%d/%m/%Y")
    start2 = datetime.strptime(start2, "%d/%m/%Y")
    end2 = datetime.strptime(end2, "%d/%m/%Y")
    return max(start1, start2) <= min(end1, end2)

def is_duplicate_submission(data):
    with open(SUBMISSIONS_FILE, 'r') as file:
        submissions_data = json.load(file)["submissions"]
        for submission in submissions_data:
            if (submission["server"] == data["server"] and
                any(scheme in submission["schemeType"] for scheme in data["schemeType"]) and
                set(submission["timeSlot"]) == set(data["timeSlot"]) and
                is_date_range_overlap(
                    submission["dateRange"]["start"],
                    submission["dateRange"]["end"],
                    data["dateRange"]["start"],
                    data["dateRange"]["end"]
                ) and
                submission.get("openSlot") == data.get("openSlot")): 
                return True, submission["bookingID"]
    return False, None

def is_open_slot_duplicate(data):
    if not data.get("openSlot"):
        return False, None
    with open(SUBMISSIONS_FILE, 'r') as file:
        submissions_data = json.load(file)["submissions"]
        for submission in submissions_data:
            if (submission.get("openSlot") and
                is_date_range_overlap(
                    submission["dateRange"]["start"],
                    submission["dateRange"]["end"],
                    data["dateRange"]["start"],
                    data["dateRange"]["end"]
                )):
                return True, submission["bookingID"]
    return False, None

def save_submission(request):
    ensure_files_exist()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Check for open slot duplicate booking if open slot is true
            is_open_slot, open_slot_booking_id = is_open_slot_duplicate(data)
            if is_open_slot:
                return JsonResponse({"error": f"Open slot booking already exists (Booking ID: {open_slot_booking_id})"}, status=409)
            
            # Check for duplicate submission for openSlot = False
            is_duplicate, booking_id = is_duplicate_submission(data)
            if is_duplicate:
                return JsonResponse({"error": f"Duplicate booking found (Booking ID: {booking_id})"}, status=409)

            # Get the next booking ID
            last_booking_id = read_counter()
            new_booking_id = last_booking_id + 1
            
            # Update the counter
            write_counter(new_booking_id)
            
            data["bookingID"] = new_booking_id
            data["status"] = "Booked"

            # Append the submission to the submissions file
            with open(SUBMISSIONS_FILE, 'r+') as file:
                submissions_data = json.load(file)
                submissions_data['submissions'].append(data)
                file.seek(0)
                json.dump(submissions_data, file, indent=4)

            return JsonResponse({"message": "Submission saved successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return HttpResponse(status=405)  # Method not allowed
