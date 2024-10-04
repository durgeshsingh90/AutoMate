from django.shortcuts import render

# Create your views here.
# MainWebsite/views.py
from django.shortcuts import render

def home(request):
    return render(request, 'first_page/index.html')

def SplunkRRN(request):
    return render(request, 'first_page/SplunkRRN.html')

def json2yaml(request):
    return render(request, 'first_page/json2yaml.html')

