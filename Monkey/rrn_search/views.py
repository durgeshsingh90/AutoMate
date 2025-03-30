from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'rrn_search/index.html')


# inside any Django view or service file
from dbutils.multi_dbconnection import execute_query, run_multiple_queries, run_query_as_json

# Single query
result = execute_query("SELECT * FROM my_table WHERE ROWNUM < 10")
print(result)

# Multiple queries
query_list = [
    "SELECT COUNT(*) FROM customers",
    "SELECT * FROM orders WHERE ROWNUM < 5"
]
results = run_multiple_queries(query_list)
