#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <search_term> <ip_address>"
    exit 1
fi

SEARCH_TERM=$1
IP_ADDRESS=$2
FILE_PATH="/home/runner/CheerfulMeanCensorware/istparam.cfg"
BACKUP_DIR="/home/runner/CheerfulMeanCensorware/"

# Create the backup directory if it does not exist
mkdir -p "$BACKUP_DIR"

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

echo "File processed successfully. Backup saved as ${BACKUP_FILE}."