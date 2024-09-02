def remove_duplicates_and_subsets(bin_list):
    """
    Remove duplicate and subset bins from the list.
    """
    # Convert list to a set to remove duplicates
    bin_set = set(bin_list)
    
    # Sort bins first by length and then lexicographically
    sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
    final_bins = []
    
    # Remove bins that are subsets of any other bin
    for bin in sorted_bins:
        if not any(bin.startswith(existing_bin) for existing_bin in final_bins):
            final_bins.append(bin)

    return final_bins

def combine_consecutives(bins):
    """
    Combine consecutive bin ranges into single ranges.
    """
    combined = []
    consecutive_count = 0
    i = 0
    
    # Ensure bins are sorted numerically
    bins = sorted(bins, key=int)
    
    while i < len(bins):
        current_bin = bins[i]
        start_bin = current_bin
        end_bin = current_bin
        
        # Check for consecutive bins directly within this loop
        while i + 1 < len(bins):
            next_bin = bins[i + 1]
            try:
                # Check if the next bin is consecutive
                if len(current_bin) == len(next_bin) and int(next_bin) == int(current_bin) + 1:
                    end_bin = next_bin
                    current_bin = next_bin
                    i += 1
                    consecutive_count += 1
                else:
                    break
            except ValueError:
                # If there's an error in checking consecutive bins, break the loop
                break
        
        # Append combined bin range or single bin
        combined.append(f"{start_bin}-{end_bin}" if start_bin != end_bin else start_bin)
        i += 1
    
    return combined, consecutive_count

def calculate_bins(processed_bins):
    """
    Calculate the start and end bins for each processed bin range.
    """
    result = []

    for bin_range in processed_bins:
        bin_range = bin_range.strip()  # Clean up any extra spaces

        # Check if the bin_range is a range
        if '-' in bin_range:
            start_bin, end_bin = bin_range.split('-')
            start_bin = start_bin.strip().ljust(15, '0')  # Pad the start_bin with '0' to make it 15 characters
            end_bin = end_bin.strip().ljust(15, '9')    # Pad the end_bin with '9' to make it 15 characters
        else:
            start_bin = end_bin = bin_range.strip()
            start_bin = start_bin.ljust(15, '0')  # Pad the bin with '0' to make it 15 characters
            end_bin = end_bin.ljust(15, '9')     # Pad the bin with '9' to make it 15 characters

        result.append((start_bin, end_bin))

    return result

def process_user_input():
    """
    Process multiline user input to generate cleaned bin ranges.
    Returns:
        list: A list of processed bin ranges.
    """
    print("Enter the list of bin ranges (press Enter twice to finish):")

    # Take multiline input
    user_input = []
    while True:
        line = input()
        if line == "":  # End input on empty line
            break
        user_input.append(line.strip())

    # Flatten the list into a single list of bin ranges
    bin_list = []
    for line in user_input:
        bin_list.extend(line.split(','))

    # Remove extra spaces
    bin_list = [item.strip() for item in bin_list if item.strip()]

    # Remove duplicates and subsets
    bin_list = remove_duplicates_and_subsets(bin_list)

    # Combine consecutive ranges
    bin_range, _ = combine_consecutives(bin_list)

    # Return the cleaned-up bin ranges
    return bin_range

# Run the script and process the results
if __name__ == "__main__":
    processed_bins = process_user_input()
    print("Processed Bin Ranges:")
    print(processed_bins)

    # Calculate the start and end bins
    bins = calculate_bins(processed_bins)
    print("Calculated Bins (Start and End):")
    print(bins)
