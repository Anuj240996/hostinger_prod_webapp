# from django import forms
# from .models import Quotation, QuotationItem
# from apps.leads.models import Lead
# from apps.surveys.models import Survey
#
#
# class QuotationForm(forms.ModelForm):
#     class Meta:
#         model = Quotation
#         fields = [
#             'lead', 'survey', 'system_size', 'panel_type', 'panel_count',
#             'inverter_type', 'mounting_type', 'warranty_years', 'estimated_generation',
#             'subtotal', 'gst_percentage', 'subsidy_amount',
#             'roi', 'payback_years', 'monthly_emi', 'monthly_savings',
#             'valid_until', 'terms_conditions', 'internal_notes'
#         ]
#         widgets = {
#             'valid_until': forms.DateInput(attrs={'type': 'date'}),
#             'terms_conditions': forms.Textarea(attrs={'rows': 4}),
#             'internal_notes': forms.Textarea(attrs={'rows': 3}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['lead'].queryset = Lead.objects.filter(stage__in=['qualified', 'survey', 'quote'])
#         self.fields['survey'].required = False
#         self.fields['survey'].queryset = Survey.objects.filter(status='completed')
#

from django import forms
from .models import Quotation, QuotationItem
from apps.leads.models import Lead
from apps.surveys.models import Survey

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'lead', 'survey', 'system_size', 'panel_type', 'panel_count',
            'inverter_type', 'mounting_type', 'warranty_years', 'estimated_generation',
            'subtotal', 'gst_percentage', 'subsidy_amount',
            'roi', 'payback_years', 'monthly_emi', 'monthly_savings',
            'valid_until', 'terms_conditions', 'internal_notes'
        ]
        widgets = {
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'terms_conditions': forms.Textarea(attrs={'rows': 4}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lead queryset: leads in qualified, survey, or quote stage
        leads_qs = Lead.objects.filter(stage__in=['qualified', 'survey', 'quote'])
        if not leads_qs.exists():
            leads_qs = Lead.objects.all()[:10]
            self.fields['lead'].help_text = "No leads in Qualified/Survey/Quote stage. Showing recent leads."
        self.fields['lead'].queryset = leads_qs
        self.fields['lead'].empty_label = "Select a lead"

        # Survey queryset: completed surveys
        survey_qs = Survey.objects.filter(status='completed')
        self.fields['survey'].queryset = survey_qs
        self.fields['survey'].empty_label = "Select a survey (optional)"
        self.fields['survey'].required = False

class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ['description', 'quantity', 'unit_price']