#!/bin/bash
#############################################################################################
# Script Name: bookings.sh
#
# Description: This script processes a configuration file (`istparam.cfg`) based on
#              provided search terms and IP address. It performs the following actions:
#
#              1. Backup the configuration file.
#              2. Hash lines containing the search terms but not the IP address.
#              3. Replace the original file with the modified file.
#              4. Run `mbportcmd` commands to stop, add, and start a service based on the search terms.
#              5. Send an email notification after all jobs have completed.
#
# Usage: ./bookings.sh <search_term1> <search_term2> ... <ip_address>
#
# Example: ./bookings.sh Visa Mastercard Diners 10.77.6.248  # For routing Visa, Mastercard, and Diners to Astrex
#
# Dependencies:
#    - mbportcmd
#    - mail (or a mail server setup for sending emails)
#
# Author: Durgesh Singh (F94GDOS)
# Date: 02 September 2024
#
# Version History:
#    - Version 1.0 (2023-09-02) - Durgesh Singh - Initial version
#    - Version 1.1 (2024-09-05) - Modified to accept multiple search terms
##############################################################################################

# Check if at least two arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <search_term1> <search_term2> ... <ip_address>"
    exit 1
fi

# Get the IP address (the last argument)
IP_ADDRESS="${@: -1}"

# Get all search terms (all arguments except the last one)
SEARCH_TERMS=("${@:1:$#-1}")

FILE_PATH="$OSITE_ROOT/cfg/istparam.cfg"
BACKUP_DIR="$OSITE_ROOT/cfg/"
TEMP_FILE="/tmp/bookings_status_$USER"  # Temporary file to keep track of job completions

# Create a backup with the current date and time
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/istparam.cfg.bak_${TIMESTAMP}"
cp "$FILE_PATH" "$BACKUP_FILE"

# Remove old backups, keeping only the latest 5
ls -tp "${BACKUP_DIR}/istparam.cfg.bak_"* | grep -v '/$' | tail -n +6 | xargs -I {} rm -- {}

# Process the file for each search term
while IFS= read -r line; do
    MODIFIED_LINE="$line"
    for SEARCH_TERM in "${SEARCH_TERMS[@]}"; do
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
for SEARCH_TERM in "${SEARCH_TERMS[@]}"; do
    mbportcmd stop "$SEARCH_TERM"
    mbportcmd add port "$SEARCH_TERM"
    mbportcmd start "$SEARCH_TERM"
    echo "$SEARCH_TERM" >> "$TEMP_FILE"
done

# Check if all jobs are done
ALL_DONE=true
for SEARCH_TERM in "${SEARCH_TERMS[@]}"; do
    if ! grep -q "$SEARCH_TERM" "$TEMP_FILE"; then
        ALL_DONE=false
        break
    fi
done

if [ "$ALL_DONE" = true ]; then
    # All jobs are completed; send an email notification
    sender=oasis77@fiserv.com
    username=$(id -un)

    # Mail list should be without any space
    maillist=niall.gilmartin@fiserv.com,arkadiusz.forycki@fiserv.com,syed.muhammad@fiserv.com,adelina.vasamivasami@fiserv.com,durgesh.singh@fiserv.com
    # maillist=durgesh.singh@fiserv.com

    subject="Open Slot Completed | $username | All Jobs Processed"

    echo "****************Open Slot Completed. Routed $username for ${SEARCH_TERMS[*]} to Astrex ****************" | mail -s "$subject" $maillist

    # Clean up the temporary file
    rm "$TEMP_FILE"
fi
