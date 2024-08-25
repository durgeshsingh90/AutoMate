#AutoMate\binblocking\views.py
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .db_utils import run_sqlplus_query
from .models import DatabaseConnection
from django.http import HttpResponseRedirect

@csrf_exempt
def process_bins(request):
    result = None
    log = []
    total_values = 0
    duplicates_removed = 0
    unique_values = 0
    consecutive_values = 0
    
    if request.method == 'POST':
        bins = request.POST.get('bins', '')
        bin_list = bins.splitlines()
        total_values = len(bin_list)
        
        log.append(f"Total input values: {total_values}")
        
        # Remove duplicates
        bin_set = set(bin_list)
        duplicates_removed = total_values - len(bin_set)
        log.append(f"Duplicates removed: {duplicates_removed}")
        
        # Sort bins
        sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
        
        # Remove subsets
        final_bins = []
        for bin in sorted_bins:
            if not any(bin.startswith(existing_bin) for existing_bin in final_bins):
                final_bins.append(bin)
        
        unique_values = len(final_bins)
        log.append(f"Unique values after removing subsets: {unique_values}")
        
        # Combine consecutive numbers
        combined_bins, consecutive_count = combine_consecutives(final_bins, log)
        consecutive_values = consecutive_count
        
        log.append(f"Final unique values: {unique_values}")
        log.append(f"Consecutive values combined: {consecutive_values}")
        log.append(f"Number of lines after processing consecutive values: {len(combined_bins)}")
        
        # Assuming final processed BINs are in `combined_bins`
        processed_bins = '\n'.join(combined_bins)
        print("Debug Processed Bins:", processed_bins)  # This will print in your console where the server is running

        # Store the processed data in session
        request.session['processed_bins'] = processed_bins
        
        # Redirect to the view that displays the processed bins
        return render(request, 'binblocking/binblocker_output.html', {'processed_bins': processed_bins})

        # return render(request, 'binblocking/binblocker_output.html', {'processed_bins': 'Test data to display in textarea'})

    else:
        return render(request, 'binblocking/binblocker.html')


def display_processed_bins(request):
    # This view captures the redirected data and displays it
    processed_bins = request.GET.get('processed_bins', '')
    return render(request, 'binblocking/binblocker_output.html', {
        'processed_bins': processed_bins
    })

def combine_consecutives(bins, log):
    combined = []
    consecutive_count = 0
    i = 0
    while i < len(bins):
        current_bin = bins[i]
        start_bin = current_bin
        end_bin = current_bin
        while i + 1 < len(bins) and is_consecutive(current_bin, bins[i + 1]):
            end_bin = bins[i + 1]
            current_bin = bins[i + 1]
            i += 1
            consecutive_count += 1
        if start_bin == end_bin:
            combined.append(start_bin)
        else:
            combined.append(f"{start_bin}-{end_bin}")
        i += 1
    return combined, consecutive_count

def is_consecutive(bin1, bin2):
    # Check if bin2 is the next consecutive number of bin1
    if len(bin1) != len(bin2):
        return False
    try:
        return int(bin2) == int(bin1) + 1
    except ValueError:
        return False

def query_view(request):
    # Fetch connection details for PROD and UAT from the DatabaseConnection model
    try:
        prod_connection = DatabaseConnection.objects.get(environment='PROD')
        uat_connection = DatabaseConnection.objects.get(environment='UAT')
    except DatabaseConnection.DoesNotExist as e:
        return render(request, 'your_template.html', {
            'prod_results': 'No connection details found for PROD environment',
            'uat_results': 'No connection details found for UAT environment'
        })

    # Extract connection details
    prod_username = prod_connection.username
    prod_password = prod_connection.password
    prod_connection_string = prod_connection.DatabaseTNS  # Assuming `DatabaseTNS` field holds the connection string

    uat_username = uat_connection.username
    uat_password = uat_connection.password
    uat_connection_string = uat_connection.DatabaseTNS  # Assuming `DatabaseTNS` field holds the connection string

    # Define your queries
    prod_query = "SELECT * FROM your_production_table WHERE ROWNUM <= 10"
    uat_query = "SELECT * FROM your_uat_table WHERE ROWNUM <= 10"

    # Run the queries using sqlplus
    prod_results = run_sqlplus_query(prod_username, prod_password, prod_connection_string, prod_query)
    uat_results = run_sqlplus_query(uat_username, uat_password, uat_connection_string, uat_query)

    return render(request, 'your_template.html', {
        'prod_results': prod_results,
        'uat_results': uat_results
    })
