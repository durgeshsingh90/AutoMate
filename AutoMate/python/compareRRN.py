def read_numbers_from_file(file_path):
    with open(file_path, 'r') as f:
        return set(line.strip() for line in f)

def write_numbers_to_file(numbers, file_path):
    with open(file_path, 'w') as f:
        for number in numbers:
            f.write(number + '\n')

def find_unique_numbers(file1, file2, output_file):
    numbers1 = read_numbers_from_file(file1)
    numbers2 = read_numbers_from_file(file2)
    
    unique_numbers = numbers1 - numbers2
    
    write_numbers_to_file(unique_numbers, output_file)

file1 = r'C:\Users\f94gdos\Downloads\100message.txt'
file2 = r'C:\Users\f94gdos\Downloads\110message.txt'
output_file = r'C:\Users\f94gdos\Downloads\unique_numbers.txt'

find_unique_numbers(file1, file2, output_file)
