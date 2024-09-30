#!/bin/bash
#############################################################################################
# Script Name: bookings.sh
#
# Description: This script processes a configuration file (`istparam.cfg`) based on
#              provided search terms and IP addresses. It performs the following actions:
#
#              1. Backup the configuration file.
#              2. Hash lines containing the search terms but not the associated IP address.
#              3. Replace the original file with the modified file.
#              4. Run `mbportcmd` commands to stop, add, and start a service based on the search terms.
#              5. Send an email notification after all jobs have completed, with different messages based on the day and time.
#
# Usage: ./bookings.sh <search_term1:ip_address1> <search_term2:ip_address2> ...
#
# Example: ./bookings.sh VisaRoute:10.77.6.248 MasterCardRoute:10.77.6.249
#
# Dependencies:
#    - mbportcmd
#    - mail (or a mail server setup for sending emails)
#
# Author: Durgesh Singh (F94GDOS)
# Date: 02 September 2024
#
# Version History:
#    - Version 1.0 (2024-09-02) - Durgesh Singh - Initial version
#    - Version 1.1 (2024-09-05) - Durgesh Singh - Modified to accept multiple search terms and added Conditional email
#    - Version 1.2 (2024-09-30) - Durgesh Singh - Modified to accept search_term:ip_address pairs and added custom email logic
#    - Version 1.3 (2024-09-30) - Durgesh Singh - Email sent only once, summarizing all parameters
##############################################################################################

# Check if at least one argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <search_term1:ip_address1> <search_term2:ip_address2> ..."
    exit 1
fi

FILE_PATH="$OSITE_ROOT/cfg/istparam.cfg"
BACKUP_DIR="$OSITE_ROOT/cfg/"
TEMP_FILE="$OSITE_ROOT/cfg/bookings_status_$USER"  # Temporary file to keep track of job completions

# Create a backup with the current date and time
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/istparam.cfg.bak_${TIMESTAMP}"
cp "$FILE_PATH" "$BACKUP_FILE"

# Remove old backups, keeping only the latest 5
ls -tp "${BACKUP_DIR}/istparam.cfg.bak_"* | grep -v '/$' | tail -n +6 | xargs -I {} rm -- {}

# Process the file for each search_term:ip_address pair
while IFS= read -r line; do
    MODIFIED_LINE="$line"
    for PAIR in "$@"; do
        # Split the pair into search term and IP address
        SEARCH_TERM=$(echo "$PAIR" | cut -d':' -f1)
        IP_ADDRESS=$(echo "$PAIR" | cut -d':' -f2)
        
        if [[ "$line" =~ (^|[[:space:]])"$SEARCH_TERM"($|[[:space:]]) ]]; then
            if [[ "$line" == *"$IP_ADDRESS"* ]]; then
                # Line contains both search term and IP address, ensure it's not hashed
                MODIFIED_LINE="${MODIFIED_LINE/#\#/}"
            elif [[ "$line" != "#"* ]]; then
                # Line contains search term but not IP address, and is not already hashed, so hash it
                MODIFIED_LINE="#$MODIFIED_LINE"
            fi
        fi
    done
    echo "$MODIFIED_LINE"
done < "$FILE_PATH" > "${FILE_PATH}.tmp"

# Replace the original file with the modified file
mv "${FILE_PATH}.tmp" "$FILE_PATH"

# Run mbportcmd commands for each search term
for PAIR in "$@"; do
    SEARCH_TERM=$(echo "$PAIR" | cut -d':' -f1)
    
    mbportcmd stop "$SEARCH_TERM"
    mbportcmd add port "$SEARCH_TERM"
    mbportcmd start "$SEARCH_TERM"
    echo "$SEARCH_TERM" >> "$TEMP_FILE"
done

# Get the current day of the week and hour
DAY_OF_WEEK=$(date +%u) # 2 for Tuesday, 4 for Thursday
CURRENT_HOUR=$(date +%H) # Gets the current hour in 24-hour format (08 for 8 AM)

# Check if all jobs are done
ALL_DONE=true
for PAIR in "$@"; do
    SEARCH_TERM=$(echo "$PAIR" | cut -d':' -f1)
    if ! grep -q "$SEARCH_TERM" "$TEMP_FILE"; then
        ALL_DONE=false
        break
    fi
done

if [ "$ALL_DONE" = true ]; then
    sender=oasis77@fiserv.com
    username=$(id -un)
    maillist=niall.gilmartin@fiserv.com,arkadiusz.forycki@fiserv.com,syed.muhammad@fiserv.com,adelina.vasamivasami@fiserv.com,durgesh.singh@fiserv.com

    if { [ "$DAY_OF_WEEK" -eq 2 ] || [ "$DAY_OF_WEEK" -eq 4 ]; } && [ "$CURRENT_HOUR" -ge 06 ] && [ "$CURRENT_HOUR" -le 11 ]; then
        # If today is Tuesday (2) or Thursday (4) and the time is between 6 AM and 11 AM
        subject="Open Slot Started | $username | All Jobs Processed"
        body="****************Open Slot Started. Routed $username for ${SEARCH_TERMS[*]} to Astrex ****************"
        
        # Send email for Open Slot
        echo "$body" | mail -s "$subject" $maillist

    else
        # Send email for other times with search term and IP routing information
        subject="Routing $username"
        body="Routed $username for the following:\n"
        
        for PAIR in "$@"; do
            SEARCH_TERM=$(echo "$PAIR" | cut -d':' -f1)
            IP_ADDRESS=$(echo "$PAIR" | cut -d':' -f2)
            body+="Search Term: $SEARCH_TERM, IP Address: $IP_ADDRESS\n"
        done

        # Send the custom email notification
        echo -e "$body" | mail -s "$subject" $maillist
    fi

    # Clean up the temporary file
    rm "$TEMP_FILE"
fi
