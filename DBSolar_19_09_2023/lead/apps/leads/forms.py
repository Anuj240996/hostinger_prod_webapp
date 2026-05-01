from django import forms
from .models import Lead, LeadActivity, LeadSource
from django.contrib.auth.models import User

#
# class LeadForm(forms.ModelForm):
#     class Meta:
#         model = Lead
#         fields = [
#             'name', 'phone', 'email', 'alternate_phone',
#             'address', 'city', 'state', 'pincode',
#             'property_type', 'roof_type', 'electricity_bill', 'monthly_consumption',
#             'source', 'campaign', 'score',
#             'assigned_to', 'budget', 'estimated_value',
#             'next_followup', 'notes', 'internal_notes'
#         ]
#         widgets = {
#             'address': forms.Textarea(attrs={'rows': 3}),
#             'notes': forms.Textarea(attrs={'rows': 3}),
#             'internal_notes': forms.Textarea(attrs={'rows': 3}),
#             'next_followup': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
#         self.fields['assigned_to'].required = False

from django import forms
from .models import Lead, LeadSource, Campaign

class LeadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['source'].queryset = LeadSource.objects.filter(organization=organization, is_active=True)
            self.fields['campaign'].queryset = Campaign.objects.filter(organization=organization, is_active=True)
        else:
            self.fields['source'].queryset = LeadSource.objects.none()
            self.fields['campaign'].queryset = Campaign.objects.none()

    class Meta:
        model = Lead
        fields = [
            'name', 'phone', 'email', 'alternate_phone',
            'address', 'city', 'state', 'pincode',
            'property_type', 'roof_type', 'electricity_bill', 'monthly_consumption',
            'source', 'campaign', 'score',
            'assigned_to', 'budget', 'estimated_value',
            'next_followup', 'notes', 'internal_notes'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
            'next_followup': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class LeadActivityForm(forms.ModelForm):
    class Meta:
        model = LeadActivity
        fields = ['activity_type', 'description', 'metadata']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class LeadFilterForm(forms.Form):
    date_range = forms.ChoiceField(choices=[
        ('', 'All Time'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('custom', 'Custom Range'),
    ], required=False)

    from_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    to_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    assigned_to = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True), required=False)
    source = forms.ModelChoiceField(queryset=LeadSource.objects.filter(is_active=True), required=False)
    stage = forms.ChoiceField(choices=[('', 'All')] + list(Lead.STAGE_CHOICES), required=False)
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter city'}))
    score = forms.ChoiceField(choices=[('', 'All')] + list(Lead.SCORE_CHOICES), required=False)