from bs4 import BeautifulSoup

def extract_isoblock_by_stan(html_content, stan_list):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all table entries
    tables = soup.find_all('table', {'cellspacing': '0'})
    
    blocks = []
    
    # Iterate over each table to find matching STAN number
    for table in tables:
        stan_tag = table.find('td', string='System trace audit number')
        
        if stan_tag:
            # Retrieve the corresponding STAN value
            stan_value = stan_tag.find_next_sibling('td', class_='cell7').text.strip()
            
            if stan_value in stan_list:
                blocks.append(str(table))
    
    return blocks

def main():
    # Hardcoded HTML file path
    html_filepath = r'C:\Users\f94gdos\Desktop\New folder (2)\DCI\DCI.html'

    # Prompt the user to input STAN numbers line by line
    print("Enter the STAN numbers, one per line. Enter an empty line to finish:")

    stan_list = []
    while True:
        stan_input = input().strip()
        if stan_input == '':
            break
        stan_list.append(stan_input)

    # Read the HTML file content
    with open(html_filepath, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML content to find the matching blocks
    soup = BeautifulSoup(html_content, 'html.parser')
    matching_blocks = extract_isoblock_by_stan(html_content, stan_list)

    # Write the matching blocks to an output file
    output_filepath = 'matching_blocks.html'
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        # Write the entire original content up to the body tag
        top = str(soup).split('<body>')[0]
        outfile.write(top)
        outfile.write('<body>\n')
        
        # Write only the matching blocks
        for block in matching_blocks:
            outfile.write(block)
            outfile.write('\n\n')  # Add some space between blocks for readability
        
        outfile.write('</body>\n</html>')

    print(f"Matching blocks have been written to {output_filepath}")

if __name__ == '__main__':
    main()
