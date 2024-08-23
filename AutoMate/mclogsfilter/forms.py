from django import forms

class LogFileForm(forms.Form):
    log_file = forms.FileField(
        label='Select a log file',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    rrn_numbers = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        label='Enter RRN numbers (one per line)'
    )
