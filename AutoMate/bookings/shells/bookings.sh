#!/bin/bash
#############################################################################################
# Script Name: bookings.sh
#
# Description: This script processes a configuration file (`istparam.cfg`) based on
#              provided search term and IP address. It performs the following actions:
#
#              1. Backup the configuration file.
#              2. Hash lines containing the search term but not the IP address.
#              3. Replace the original file with the modified file.
#              4. Run `mbportcmd` commands to stop, add, and start a service based on the search term.
#              5. Send an email notification.
#
# Usage: ./bookings.sh <search_term> <ip_address>
#
# Example: ./bookings.sh VisaRoute 10.77.6.248  #For routing visa to Astrex
#
# Dependencies:
#    - mbportcmd
#    - mail (or a mail server setup for sending emails)
#
# Author: Durgesh Singh (F94GDOS)
# Date: 02 September 2024
#
# Version History:
#    - Version 1.0 (2023-10-27) - Durgesh Singh - Initial version
##############################################################################################

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <search_term> <ip_address>"
    exit 1
fi

SEARCH_TERM=$1
IP_ADDRESS=$2
FILE_PATH="$OSITE_ROOT/cfg/istparam.cfg"
BACKUP_DIR="$OSITE_ROOT/cfg/"

# Create a backup with the current date and time
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/istparam.cfg.bak_${TIMESTAMP}"
cp "$FILE_PATH" "$BACKUP_FILE"

# Remove old backups, keeping only the latest 5
ls -tp "${BACKUP_DIR}/istparam.cfg.bak_"* | grep -v '/$' | tail -n +6 | xargs -I {} rm -- {}

# Process the file
while IFS= read -r line; do
    if [[ "$line" =~ (^|[[:space:]])"$SEARCH_TERM"($|[[:space:]]) ]]; then
        if [[ "$line" == *"$IP_ADDRESS"* ]]; then
            # Line contains both search term and IP address, ensure it's not hashed
            echo "${line/#\#/}"
        elif [[ "$line" != "#"* ]]; then
            # Line contains search term but not IP address, and is not already hashed, so hash it
            echo "#$line"
        else
            # Line contains search term but is already hashed
            echo "$line"
        fi
		    else
        # Line does not contain the search term, leave it as is
        echo "$line"
    fi
done < "$FILE_PATH" > "${FILE_PATH}.tmp"

# Replace the original file with the modified file
mv "${FILE_PATH}.tmp" "$FILE_PATH"

# Run mbportcmd commands
mbportcmd stop "$SEARCH_TERM"
mbportcmd add port "$SEARCH_TERM"
mbportcmd start "$SEARCH_TERM"

echo "File processed successfully. Backup saved as ${BACKUP_FILE}."

#Sending mail for notification
sender=oasis77@fiserv.com
username=$(id -un)

#Mailist should be without any space
maillist=niall.gilmartin@fiserv.com,arkadiusz.forycki@fiserv.com,syed.muhammad@fiserv.com,adelina.vasamivasami@fiserv.com,durgesh.singh@fiserv.com
#maillist=durgesh.singh@fiserv.com

subject="Open Slot Started | $username | Routed Schemes to Astrex"

echo "****************Open Slot Started. Routed $username Mastercard, Visa and Diners to Astrex ****************" | mail -s "$subject" $maillist
                   