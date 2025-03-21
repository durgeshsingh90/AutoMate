from django.shortcuts import render

def reversal_generator(request):
    return render(request, 'gen_reversals/reversals.html')
