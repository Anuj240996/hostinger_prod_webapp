# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.db.models import Q, Sum, Count
# from django.utils import timezone
# from django.http import JsonResponse, HttpResponse, FileResponse
# from datetime import timedelta
# import csv
# from reportlab.pdf import canvas
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.units import inch
# import io
#
# from .models import Quotation, QuotationItem, QuotationRevision
# from .forms import QuotationForm, QuotationItemForm
# from apps.leads.models import Lead
# from apps.surveys.models import Survey
#
#
# @login_required
# def quotation_list(request):
#     """
#     List all quotations with filters
#     """
#     quotations = Quotation.objects.all().select_related('lead', 'created_by')
#
#     # Apply filters
#     status = request.GET.get('status')
#     if status:
#         quotations = quotations.filter(status=status)
#
#     created_by = request.GET.get('created_by')
#     if created_by:
#         quotations = quotations.filter(created_by_id=created_by)
#
#     from_date = request.GET.get('from_date')
#     if from_date:
#         quotations = quotations.filter(created__date__gte=from_date)
#
#     to_date = request.GET.get('to_date')
#     if to_date:
#         quotations = quotations.filter(created__date__lte=to_date)
#
#     # Summary stats
#     total_quotations = quotations.count()
#     approved_count = quotations.filter(status='approved').count()
#     pending_count = quotations.filter(status__in=['draft', 'sent', 'viewed', 'negotiating']).count()
#     total_value = quotations.aggregate(total=Sum('total_cost'))['total'] or 0
#
#     context = {
#         'quotations': quotations,
#         'total_quotations': total_quotations,
#         'approved_count': approved_count,
#         'pending_count': pending_count,
#         'total_value': total_value,
#         'sales_users': User.objects.filter(groups__name='Sales'),
#     }
#
#     return render(request, 'quotations/quotation_list.html', context)
#
#
# @login_required
# def quotation_detail(request, pk):
#     """
#     Display detailed view of a quotation
#     """
#     quotation = get_object_or_404(Quotation, pk=pk)
#
#     context = {
#         'quotation': quotation,
#     }
#
#     return render(request, 'quotations/quotation_detail.html', context)
#
#
# @login_required
# def quotation_create(request):
#     """
#     Create a new quotation
#     """
#     if request.method == 'POST':
#         form = QuotationForm(request.POST)
#         if form.is_valid():
#             quotation = form.save(commit=False)
#             quotation.created_by = request.user
#
#             # Calculate financials
#             quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
#             quotation.total_cost = quotation.subtotal + quotation.gst_amount
#             quotation.net_cost = quotation.total_cost - quotation.subsidy_amount
#
#             quotation.save()
#
#             # Update lead stage
#             if quotation.lead.stage == 'survey':
#                 quotation.lead.stage = 'quote'
#                 quotation.lead.save()
#
#             messages.success(request, 'Quotation created successfully!')
#             return redirect('quotation_detail', pk=quotation.id)
#     else:
#         lead_id = request.GET.get('lead')
#         survey_id = request.GET.get('survey')
#         initial = {}
#         if lead_id:
#             initial['lead'] = lead_id
#         if survey_id:
#             initial['survey'] = survey_id
#         form = QuotationForm(initial=initial)
#
#     context = {
#         'form': form,
#         'title': 'Create New Quotation'
#     }
#
#     return render(request, 'quotations/quotation_form.html', context)
#
#
# @login_required
# def quotation_edit(request, pk):
#     """
#     Edit an existing quotation
#     """
#     quotation = get_object_or_404(Quotation, pk=pk)
#
#     if request.method == 'POST':
#         form = QuotationForm(request.POST, instance=quotation)
#         if form.is_valid():
#             quotation = form.save(commit=False)
#
#             # Recalculate financials
#             quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
#             quotation.total_cost = quotation.subtotal + quotation.gst_amount
#             quotation.net_cost = quotation.total_cost - quotation.subsidy_amount
#
#             # Create revision if total cost changed
#             if quotation.pk and 'total_cost' in form.changed_data:
#                 QuotationRevision.objects.create(
#                     quotation=quotation,
#                     version=quotation.version + 1,
#                     total_cost=quotation.total_cost,
#                     created_by=request.user
#                 )
#                 quotation.version += 1
#
#             quotation.save()
#
#             messages.success(request, 'Quotation updated successfully!')
#             return redirect('quotation_detail', pk=quotation.id)
#     else:
#         form = QuotationForm(instance=quotation)
#
#     context = {
#         'form': form,
#         'quotation': quotation,
#         'title': f'Edit Quotation #{quotation.quote_number}'
#     }
#
#     return render(request, 'quotations/quotation_form.html', context)
#
#
# @login_required
# def quotation_send(request, pk):
#     """
#     Mark quotation as sent
#     """
#     if request.method == 'POST':
#         quotation = get_object_or_404(Quotation, pk=pk)
#         quotation.status = 'sent'
#         quotation.sent_date = timezone.now()
#         quotation.save()
#
#         messages.success(request, 'Quotation marked as sent!')
#
#     return redirect('quotation_detail', pk=quotation.id)
#
#
# @login_required
# def quotation_approve(request, pk):
#     """
#     Approve quotation
#     """
#     if request.method == 'POST':
#         quotation = get_object_or_404(Quotation, pk=pk)
#         quotation.status = 'approved'
#         quotation.customer_approved = True
#         quotation.internal_approved = True
#         quotation.approval_date = timezone.now()
#         quotation.approved_by = request.user
#         quotation.save()
#
#         # Update lead
#         quotation.lead.stage = 'won'
#         quotation.lead.converted_at = timezone.now()
#         quotation.lead.save()
#
#         messages.success(request, 'Quotation approved!')
#
#     return redirect('quotation_detail', pk=quotation.id)
#
#
# @login_required
# def quotation_reject(request, pk):
#     """
#     Reject quotation
#     """
#     if request.method == 'POST':
#         quotation = get_object_or_404(Quotation, pk=pk)
#         quotation.status = 'rejected'
#         quotation.save()
#
#         messages.info(request, 'Quotation rejected.')
#
#     return redirect('quotation_detail', pk=quotation.id)
#
#
# @login_required
# def add_quotation_item(request, pk):
#     """
#     Add item to quotation
#     """
#     if request.method == 'POST':
#         quotation = get_object_or_404(Quotation, pk=pk)
#
#         form = QuotationItemForm(request.POST)
#         if form.is_valid():
#             item = form.save(commit=False)
#             item.quotation = quotation
#             item.total_price = item.quantity * item.unit_price
#             item.save()
#
#             # Update quotation subtotal
#             quotation.subtotal = quotation.items.aggregate(total=Sum('total_price'))['total'] or 0
#             quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
#             quotation.total_cost = quotation.subtotal + quotation.gst_amount
#             quotation.net_cost = quotation.total_cost - quotation.subsidy_amount
#             quotation.save()
#
#             return JsonResponse({'success': True})
#
#     return JsonResponse({'success': False}, status=400)
#
#
# @login_required
# def add_negotiation_note(request, pk):
#     """
#     Add negotiation note to quotation
#     """
#     if request.method == 'POST':
#         quotation = get_object_or_404(Quotation, pk=pk)
#         note = request.POST.get('note')
#
#         if note:
#             if quotation.negotiation_notes:
#                 quotation.negotiation_notes += f"\n\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}:\n{note}"
#             else:
#                 quotation.negotiation_notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}:\n{note}"
#
#             quotation.status = 'negotiating'
#             quotation.save()
#
#             return JsonResponse({'success': True})
#
#     return JsonResponse({'success': False}, status=400)
#
#
# @login_required
# def quotation_pdf(request, pk):
#     """
#     Generate PDF for quotation
#     """
#     quotation = get_object_or_404(Quotation, pk=pk)
#
#     # Create PDF
#     buffer = io.BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter
#
#     # Header
#     p.setFont("Helvetica-Bold", 20)
#     p.drawString(50, height - 50, "SOLAR QUOTATION")
#
#     p.setFont("Helvetica", 12)
#     p.drawString(50, height - 80, f"Quote #: {quotation.quote_number}")
#     p.drawString(50, height - 95, f"Date: {quotation.created.strftime('%d-%m-%Y')}")
#     p.drawString(50, height - 110, f"Valid Until: {quotation.valid_until.strftime('%d-%m-%Y')}")
#
#     # Customer Details
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(50, height - 140, "Customer Details")
#
#     p.setFont("Helvetica", 12)
#     p.drawString(50, height - 160, f"Name: {quotation.lead.name}")
#     p.drawString(50, height - 175, f"Address: {quotation.lead.address}")
#     p.drawString(50, height - 190, f"Phone: {quotation.lead.phone}")
#
#     # System Details
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(50, height - 220, "System Details")
#
#     p.setFont("Helvetica", 12)
#     p.drawString(50, height - 240, f"System Size: {quotation.system_size} kW")
#     p.drawString(50, height - 255, f"Panel Type: {quotation.panel_type}")
#     p.drawString(50, height - 270, f"Panel Count: {quotation.panel_count}")
#     p.drawString(50, height - 285, f"Inverter: {quotation.inverter_type}")
#
#     # Cost Breakdown
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(50, height - 315, "Cost Breakdown")
#
#     y = height - 335
#     p.setFont("Helvetica-Bold", 10)
#     p.drawString(50, y, "Description")
#     p.drawString(300, y, "Qty")
#     p.drawString(350, y, "Unit Price")
#     p.drawString(450, y, "Total")
#
#     y -= 15
#     p.setFont("Helvetica", 10)
#
#     for item in quotation.items.all():
#         p.drawString(50, y, item.description[:30])
#         p.drawString(300, y, str(item.quantity))
#         p.drawString(350, y, f"₹{item.unit_price:,.2f}")
#         p.drawString(450, y, f"₹{item.total_price:,.2f}")
#         y -= 15
#
#         if y < 50:  # New page
#             p.showPage()
#             y = height - 50
#
#     # Totals
#     y -= 10
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(350, y, "Subtotal:")
#     p.drawString(450, y, f"₹{quotation.subtotal:,.2f}")
#
#     y -= 15
#     p.drawString(350, y, f"GST ({quotation.gst_percentage}%):")
#     p.drawString(450, y, f"₹{quotation.gst_amount:,.2f}")
#
#     y -= 15
#     p.drawString(350, y, "Total:")
#     p.drawString(450, y, f"₹{quotation.total_cost:,.2f}")
#
#     y -= 15
#     p.drawString(350, y, "Subsidy:")
#     p.drawString(450, y, f"-₹{quotation.subsidy_amount:,.2f}")
#
#     y -= 15
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(350, y, "Net Cost:")
#     p.drawString(450, y, f"₹{quotation.net_cost:,.2f}")
#
#     # Financial Analysis
#     y -= 30
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(50, y, "Financial Analysis")
#
#     y -= 20
#     p.setFont("Helvetica", 12)
#     p.drawString(50, y, f"ROI: {quotation.roi}%")
#     p.drawString(200, y, f"Payback Period: {quotation.payback_years} years")
#
#     y -= 15
#     p.drawString(50, y, f"Monthly EMI: ₹{quotation.monthly_emi:,.2f}")
#     p.drawString(200, y, f"Monthly Savings: ₹{quotation.monthly_savings:,.2f}")
#
#     # Terms
#     y -= 30
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(50, y, "Terms & Conditions:")
#
#     y -= 15
#     p.setFont("Helvetica", 10)
#     terms = quotation.terms_conditions.split('\n')
#     for line in terms:
#         p.drawString(50, y, line)
#         y -= 12
#
#     p.save()
#
#     buffer.seek(0)
#     return FileResponse(buffer, as_attachment=True, filename=f"Quotation_{quotation.quote_number}.pdf")
#
#
# @login_required
# def quotation_export(request):
#     """
#     Export quotations to CSV
#     """
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = f'attachment; filename="quotations_{timezone.now().date()}.csv"'
#
#     writer = csv.writer(response)
#     writer.writerow(['Quote #', 'Lead', 'System Size', 'Total Cost', 'Status', 'Created By', 'Created Date'])
#
#     quotations = Quotation.objects.all().select_related('lead', 'created_by')
#     for quote in quotations:
#         writer.writerow([
#             quote.quote_number,
#             quote.lead.name,
#             f"{quote.system_size} kW",
#             quote.total_cost,
#             quote.get_status_display(),
#             quote.created_by.get_full_name() if quote.created_by else '',
#             quote.created.strftime('%Y-%m-%d'),
#         ])
#
#     return response

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
import csv

from .models import Quotation, QuotationItem, QuotationRevision
from .forms import QuotationForm, QuotationItemForm
from apps.leads.models import Lead
from apps.surveys.models import Survey
from django.contrib.auth.models import User

import logging

# Try to import reportlab, provide fallback if not available
try:
    from reportlab.pdf import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not installed. PDF generation will be disabled.")

from .models import Quotation, QuotationItem, QuotationRevision
from .forms import QuotationForm, QuotationItemForm
from apps.leads.models import Lead
from apps.surveys.models import Survey
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@login_required
def quotation_list(request):
    """
    List all quotations with filters
    """
    quotations = Quotation.objects.all().select_related('lead', 'created_by')

    # Apply filters
    status = request.GET.get('status')
    if status:
        quotations = quotations.filter(status=status)

    created_by = request.GET.get('created_by')
    if created_by:
        quotations = quotations.filter(created_by_id=created_by)

    from_date = request.GET.get('from_date')
    if from_date:
        quotations = quotations.filter(created__date__gte=from_date)

    to_date = request.GET.get('to_date')
    if to_date:
        quotations = quotations.filter(created__date__lte=to_date)

    # Summary stats
    total_quotations = quotations.count()
    approved_count = quotations.filter(status='approved').count()
    pending_count = quotations.filter(status__in=['draft', 'sent', 'viewed', 'negotiating']).count()
    total_value = quotations.aggregate(total=Sum('total_cost'))['total'] or 0

    context = {
        'quotations': quotations,
        'total_quotations': total_quotations,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'total_value': total_value,
        'sales_users': User.objects.filter(groups__name='Sales'),
    }

    return render(request, 'quotations/quotation_list.html', context)


@login_required
def quotation_detail(request, pk):
    """
    Display detailed view of a quotation
    """
    quotation = get_object_or_404(Quotation, pk=pk)

    context = {
        'quotation': quotation,
    }

    return render(request, 'quotations/quotation_detail.html', context)

#
# @login_required
# def quotation_create(request):
#     """
#     Create a new quotation
#     """
#     if request.method == 'POST':
#         form = QuotationForm(request.POST)
#         if form.is_valid():
#             quotation = form.save(commit=False)
#             quotation.created_by = request.user
#
#             # Calculate financials
#             quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
#             quotation.total_cost = quotation.subtotal + quotation.gst_amount
#             quotation.net_cost = quotation.total_cost - quotation.subsidy_amount
#
#             quotation.save()
#
#             # Update lead stage
#             if quotation.lead.stage == 'survey':
#                 quotation.lead.stage = 'quote'
#                 quotation.lead.save()
#
#             messages.success(request, 'Quotation created successfully!')
#             return redirect('quotation_detail', pk=quotation.id)
#     else:
#         lead_id = request.GET.get('lead')
#         survey_id = request.GET.get('survey')
#         initial = {}
#         if lead_id:
#             initial['lead'] = lead_id
#         if survey_id:
#             initial['survey'] = survey_id
#         form = QuotationForm(initial=initial)
#
#     context = {
#         'form': form,
#         'title': 'Create New Quotation'
#     }
#
#     return render(request, 'quotations/quotation_form.html', context)

@login_required
def quotation_create(request):
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        if form.is_valid():
            quotation = form.save(commit=False)
            quotation.created_by = request.user
            # Calculate financials
            quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
            quotation.total_cost = quotation.subtotal + quotation.gst_amount
            quotation.net_cost = quotation.total_cost - quotation.subsidy_amount
            quotation.save()

            # Update lead stage
            if quotation.lead.stage == 'survey':
                quotation.lead.stage = 'quote'
                quotation.lead.save()

            messages.success(request, 'Quotation created successfully!')
            return redirect('quotation_detail', pk=quotation.id)
    else:
        initial = {}
        survey_id = request.GET.get('survey')
        if survey_id:
            try:
                from apps.surveys.models import Survey
                survey = Survey.objects.select_related('lead').get(pk=survey_id)
                initial['lead'] = survey.lead.id
                initial['survey'] = survey.id
                # Pre-fill system size from survey if available
                if survey.recommended_size:
                    initial['system_size'] = survey.recommended_size
            except Survey.DoesNotExist:
                pass

        lead_id = request.GET.get('lead')
        if lead_id:
            initial['lead'] = lead_id

        form = QuotationForm(initial=initial)

    context = {
        'form': form,
        'title': 'Create New Quotation'
    }
    return render(request, 'quotations/quotation_form.html', context)


@login_required
def quotation_edit(request, pk):
    """
    Edit an existing quotation
    """
    quotation = get_object_or_404(Quotation, pk=pk)

    if request.method == 'POST':
        form = QuotationForm(request.POST, instance=quotation)
        if form.is_valid():
            quotation = form.save(commit=False)

            # Recalculate financials
            quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
            quotation.total_cost = quotation.subtotal + quotation.gst_amount
            quotation.net_cost = quotation.total_cost - quotation.subsidy_amount

            # Create revision if total cost changed
            if quotation.pk and 'total_cost' in form.changed_data:
                QuotationRevision.objects.create(
                    quotation=quotation,
                    version=quotation.version + 1,
                    total_cost=quotation.total_cost,
                    created_by=request.user
                )
                quotation.version += 1

            quotation.save()

            messages.success(request, 'Quotation updated successfully!')
            return redirect('quotation_detail', pk=quotation.id)
    else:
        form = QuotationForm(instance=quotation)

    context = {
        'form': form,
        'quotation': quotation,
        'title': f'Edit Quotation #{quotation.quote_number}'
    }

    return render(request, 'quotations/quotation_form.html', context)


@login_required
def quotation_send(request, pk):
    """
    Mark quotation as sent
    """
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)
        quotation.status = 'sent'
        quotation.sent_date = timezone.now()
        quotation.save()

        messages.success(request, 'Quotation marked as sent!')

    return redirect('quotation_detail', pk=quotation.id)

#
# @login_required
# def quotation_approve(request, pk):
#     """
#     Approve quotation
#     """
#     if request.method == 'POST':
#         quotation = get_object_or_404(Quotation, pk=pk)
#         quotation.status = 'approved'
#         quotation.customer_approved = True
#         quotation.internal_approved = True
#         quotation.approval_date = timezone.now()
#         quotation.approved_by = request.user
#         quotation.save()
#
#         # Update lead
#         quotation.lead.stage = 'won'
#         quotation.lead.converted_at = timezone.now()
#         quotation.lead.save()
#
#         messages.success(request, 'Quotation approved!')
#
#     return redirect('quotation_detail', pk=quotation.id)

@login_required
def quotation_approve(request, pk):
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)
        quotation.status = 'approved'
        quotation.customer_approved = True
        quotation.internal_approved = True
        quotation.approval_date = timezone.now()
        quotation.approved_by = request.user
        quotation.save()

        # Update lead
        quotation.lead.stage = 'won'
        quotation.lead.converted_at = timezone.now()
        quotation.lead.save()

        # Create revenue record
        from apps.revenue.models import Revenue
        Revenue.objects.create(
            lead=quotation.lead,
            quotation=quotation,
            amount=quotation.net_cost or quotation.total_cost,
            date=timezone.now().date(),
            payment_status='pending'  # or 'paid' if payment is received immediately
        )

        messages.success(request, 'Quotation approved! Revenue record created.')

    return redirect('quotation_detail', pk=quotation.id)

@login_required
def quotation_reject(request, pk):
    """
    Reject quotation
    """
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)
        quotation.status = 'rejected'
        quotation.save()

        messages.info(request, 'Quotation rejected.')

    return redirect('quotation_detail', pk=quotation.id)


@login_required
def add_quotation_item(request, pk):
    """
    Add item to quotation
    """
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)

        form = QuotationItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.quotation = quotation
            item.total_price = item.quantity * item.unit_price
            item.save()

            # Update quotation subtotal
            quotation.subtotal = quotation.items.aggregate(total=Sum('total_price'))['total'] or 0
            quotation.gst_amount = quotation.subtotal * (quotation.gst_percentage / 100)
            quotation.total_cost = quotation.subtotal + quotation.gst_amount
            quotation.net_cost = quotation.total_cost - quotation.subsidy_amount
            quotation.save()

            return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


@login_required
def add_negotiation_note(request, pk):
    """
    Add negotiation note to quotation
    """
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)
        note = request.POST.get('note')

        if note:
            if quotation.negotiation_notes:
                quotation.negotiation_notes += f"\n\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}:\n{note}"
            else:
                quotation.negotiation_notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}:\n{note}"

            quotation.status = 'negotiating'
            quotation.save()

            return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)

#
# def quotation_pdf(request, pk):
#     """
#     PDF generation - temporarily disabled
#     """
#     messages.info(request, 'PDF generation is currently being set up. Please check back later.')
#     return redirect('quotation_detail', pk=pk)


from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime


@login_required
def quotation_pdf(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    # Container for the 'Flowable' objects
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=16, spaceAfter=20))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10))

    # Title
    elements.append(Paragraph("SOLAR QUOTATION", styles['Center']))

    # Quotation number and date
    elements.append(Paragraph(f"Quote #: {quotation.quote_number}", styles['Normal']))
    elements.append(Paragraph(f"Date: {quotation.created.strftime('%d-%m-%Y')}", styles['Normal']))
    elements.append(Paragraph(f"Valid Until: {quotation.valid_until.strftime('%d-%m-%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Customer Details
    elements.append(Paragraph("Customer Details", styles['Heading2']))
    elements.append(Paragraph(f"Name: {quotation.lead.name}", styles['Normal']))
    elements.append(Paragraph(f"Address: {quotation.lead.address}, {quotation.lead.city}", styles['Normal']))
    elements.append(Paragraph(f"Phone: {quotation.lead.phone}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # System Details
    elements.append(Paragraph("System Details", styles['Heading2']))
    data_system = [
        ["System Size", f"{quotation.system_size} kW"],
        ["Panel Type", quotation.panel_type],
        ["Panel Count", str(quotation.panel_count)],
        ["Inverter Type", quotation.inverter_type],
        ["Mounting Type", quotation.mounting_type],
        ["Warranty", f"{quotation.warranty_years} years"],
        ["Est. Generation", f"{quotation.estimated_generation} kWh/year"],
    ]
    table_system = Table(data_system, colWidths=[150, 200])
    table_system.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_system)
    elements.append(Spacer(1, 20))

    # Cost Breakdown
    elements.append(Paragraph("Cost Breakdown", styles['Heading2']))
    data_items = [["Description", "Qty", "Unit Price (₹)", "Total (₹)"]]
    for item in quotation.items.all():
        data_items.append([
            item.description,
            str(item.quantity),
            f"{item.unit_price:,.2f}",
            f"{item.total_price:,.2f}"
        ])
    # Totals
    data_items.append(["", "", "Subtotal:", f"{quotation.subtotal:,.2f}"])
    data_items.append(["", "", f"GST ({quotation.gst_percentage}%):", f"{quotation.gst_amount:,.2f}"])
    data_items.append(["", "", "Total:", f"{quotation.total_cost:,.2f}"])
    data_items.append(["", "", "Subsidy:", f"-{quotation.subsidy_amount:,.2f}"])
    data_items.append(["", "", "Net Cost:", f"{quotation.net_cost:,.2f}"])

    table_items = Table(data_items, colWidths=[200, 50, 100, 100])
    table_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    # Make the last row (Net Cost) bold
    table_items.setStyle(TableStyle([
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table_items)
    elements.append(Spacer(1, 20))

    # Financial Analysis
    elements.append(Paragraph("Financial Analysis", styles['Heading2']))
    data_finance = [
        ["ROI", f"{quotation.roi}%"],
        ["Payback Period", f"{quotation.payback_years} years"],
        ["Monthly EMI", f"₹{quotation.monthly_emi:,.2f}"],
        ["Monthly Savings", f"₹{quotation.monthly_savings:,.2f}"],
    ]
    table_finance = Table(data_finance, colWidths=[150, 200])
    table_finance.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_finance)
    elements.append(Spacer(1, 20))

    # Terms and Conditions
    if quotation.terms_conditions:
        elements.append(Paragraph("Terms & Conditions", styles['Heading2']))
        elements.append(Paragraph(quotation.terms_conditions.replace('\n', '<br/>'), styles['Normal']))

    # Build PDF
    doc.build(elements)

    # FileResponse sets the appropriate headers
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Quotation_{quotation.quote_number}.pdf")

#
# @login_required
# def quotation_pdf(request, pk):
#     """
#     Generate PDF for quotation
#     """
#     if not REPORTLAB_AVAILABLE:
#         messages.error(request, 'PDF generation is not available. Please install reportlab.')
#         return redirect('quotation_detail', pk=pk)
#
#     quotation = get_object_or_404(Quotation, pk=pk)
#
#     try:
#         # Create PDF
#         buffer = io.BytesIO()
#         p = canvas.Canvas(buffer, pagesize=letter)
#         width, height = letter
#
#         # Helper to safely format numbers
#         def safe_currency(value):
#             if value is None:
#                 return "₹0"
#             try:
#                 # Convert Decimal to float and format
#                 val = float(value)
#                 return f"₹{val:,.2f}"
#             except (TypeError, ValueError):
#                 return "₹0"
#
#         def safe_float(value, default=0):
#             if value is None:
#                 return default
#             try:
#                 return float(value)
#             except (TypeError, ValueError):
#                 return default
#
#         def safe_str(value):
#             return str(value) if value is not None else ""
#
#         # Header
#         p.setFont("Helvetica-Bold", 20)
#         p.drawString(50, height - 50, "SOLAR QUOTATION")
#
#         p.setFont("Helvetica", 12)
#         p.drawString(50, height - 80, f"Quote #: {quotation.quote_number}")
#         p.drawString(50, height - 95, f"Date: {quotation.created.strftime('%d-%m-%Y')}")
#         p.drawString(50, height - 110,
#                      f"Valid Until: {quotation.valid_until.strftime('%d-%m-%Y') if quotation.valid_until else 'N/A'}")
#
#         # Customer Details
#         p.setFont("Helvetica-Bold", 14)
#         p.drawString(50, height - 140, "Customer Details")
#
#         p.setFont("Helvetica", 12)
#         p.drawString(50, height - 160, f"Name: {quotation.lead.name}")
#         p.drawString(50, height - 175, f"Address: {quotation.lead.address}")
#         p.drawString(50, height - 190, f"Phone: {quotation.lead.phone}")
#
#         # System Details
#         p.setFont("Helvetica-Bold", 14)
#         p.drawString(50, height - 220, "System Details")
#
#         p.setFont("Helvetica", 12)
#         p.drawString(50, height - 240, f"System Size: {safe_float(quotation.system_size)} kW")
#         p.drawString(50, height - 255, f"Panel Type: {safe_str(quotation.panel_type)}")
#         p.drawString(50, height - 270, f"Panel Count: {quotation.panel_count or 0}")
#         p.drawString(50, height - 285, f"Inverter: {safe_str(quotation.inverter_type)}")
#
#         # Cost Breakdown
#         p.setFont("Helvetica-Bold", 14)
#         p.drawString(50, height - 315, "Cost Breakdown")
#
#         y = height - 335
#         p.setFont("Helvetica-Bold", 10)
#         p.drawString(50, y, "Description")
#         p.drawString(300, y, "Qty")
#         p.drawString(350, y, "Unit Price")
#         p.drawString(450, y, "Total")
#
#         y -= 15
#         p.setFont("Helvetica", 10)
#
#         for item in quotation.items.all():
#             p.drawString(50, y, safe_str(item.description)[:30])
#             p.drawString(300, y, str(item.quantity or 0))
#             p.drawString(350, y, safe_currency(item.unit_price))
#             p.drawString(450, y, safe_currency(item.total_price))
#             y -= 15
#
#             if y < 50:  # New page
#                 p.showPage()
#                 y = height - 50
#
#         # Totals
#         y -= 10
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(350, y, "Subtotal:")
#         p.drawString(450, y, safe_currency(quotation.subtotal))
#
#         y -= 15
#         gst_percent = safe_float(quotation.gst_percentage, 0)
#         p.drawString(350, y, f"GST ({gst_percent:.1f}%):")
#         p.drawString(450, y, safe_currency(quotation.gst_amount))
#
#         y -= 15
#         p.drawString(350, y, "Total:")
#         p.drawString(450, y, safe_currency(quotation.total_cost))
#
#         y -= 15
#         p.drawString(350, y, "Subsidy:")
#         p.drawString(450, y, f"-{safe_currency(quotation.subsidy_amount)}")
#
#         y -= 15
#         p.setFont("Helvetica-Bold", 14)
#         p.drawString(350, y, "Net Cost:")
#         p.drawString(450, y, safe_currency(quotation.net_cost))
#
#         # Financial Analysis
#         y -= 30
#         p.setFont("Helvetica-Bold", 14)
#         p.drawString(50, y, "Financial Analysis")
#
#         y -= 20
#         p.setFont("Helvetica", 12)
#         p.drawString(50, y, f"ROI: {safe_float(quotation.roi, 0):.1f}%")
#         p.drawString(200, y, f"Payback Period: {safe_float(quotation.payback_years, 0):.1f} years")
#
#         y -= 15
#         p.drawString(50, y, f"Monthly EMI: {safe_currency(quotation.monthly_emi)}")
#         p.drawString(200, y, f"Monthly Savings: {safe_currency(quotation.monthly_savings)}")
#
#         # Terms
#         y -= 30
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(50, y, "Terms & Conditions:")
#
#         y -= 15
#         p.setFont("Helvetica", 10)
#         terms = (quotation.terms_conditions or "").split('\n')
#         for line in terms:
#             p.drawString(50, y, line[:80])  # Truncate long lines
#             y -= 12
#             if y < 30:
#                 p.showPage()
#                 y = height - 30
#
#         p.save()
#         buffer.seek(0)
#         return FileResponse(buffer, as_attachment=True, filename=f"Quotation_{quotation.quote_number}.pdf")
#
#     except Exception as e:
#         logger.error(f"PDF generation error: {e}")
#         messages.error(request, f'Error generating PDF: {str(e)}')
#         return redirect('quotation_detail', pk=quotation.id)

@login_required
def quotation_export(request):
    """
    Export quotations to CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="quotations_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Quote #', 'Lead', 'System Size', 'Total Cost', 'Status', 'Created By', 'Created Date'])

    quotations = Quotation.objects.all().select_related('lead', 'created_by')
    for quote in quotations:
        writer.writerow([
            quote.quote_number,
            quote.lead.name,
            f"{quote.system_size} kW",
            quote.total_cost,
            quote.get_status_display(),
            quote.created_by.get_full_name() if quote.created_by else '',
            quote.created.strftime('%Y-%m-%d'),
        ])

    return response