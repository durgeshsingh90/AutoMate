import random

def generate_random_numbers(start, end, num_numbers):
  """Generates a list of random numbers within a specified range.

  Args:
    start: The starting number of the range.
    end: The ending number of the range.
    num_numbers: The number of random numbers to generate.

  Returns:
    A list of random numbers.
  """

  random_numbers = []
  for _ in range(num_numbers):
    random_number = random.randint(start, end)
    random_numbers.append(random_number)
  return random_numbers

# Generate 1000 random numbers between 4000 and 999999
random_numbers = generate_random_numbers(4000, 999999, 1000)

# Print the generated numbers (optional)
print(random_numbers)
