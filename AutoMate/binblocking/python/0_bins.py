def calculate_bins(processed_bins):
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
bins = calculate_bins(processed_bins)
print (bins)
# for start, end in bins:
#     print(f"Start Bin: {start}, End Bin: {end}")