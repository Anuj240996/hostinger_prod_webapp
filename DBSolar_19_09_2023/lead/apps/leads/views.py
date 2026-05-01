from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import csv

from .models import Lead, LeadActivity, FollowUp, LeadSource
from .forms import LeadForm, LeadActivityForm, LeadFilterForm
from django.contrib.auth.models import User


@login_required
def lead_list(request):
    """
    Display list of leads with filtering
    """
    leads = Lead.objects.all()

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    # Apply filters
    if request.GET.get('stage'):
        leads = leads.filter(stage=request.GET.get('stage'))
    if request.GET.get('score'):
        leads = leads.filter(score=request.GET.get('score'))
    if request.GET.get('assigned_to'):
        leads = leads.filter(assigned_to_id=request.GET.get('assigned_to'))
    if request.GET.get('source'):
        leads = leads.filter(source_id=request.GET.get('source'))
    if request.GET.get('city'):
        leads = leads.filter(city__icontains=request.GET.get('city'))

    # Date range filter
    date_range = request.GET.get('date_range')
    if date_range == 'today':
        leads = leads.filter(created__date=timezone.now().date())
    elif date_range == 'yesterday':
        yesterday = timezone.now().date() - timedelta(days=1)
        leads = leads.filter(created__date=yesterday)
    elif date_range == 'this_week':
        start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        leads = leads.filter(created__date__gte=start)
    elif date_range == 'this_month':
        leads = leads.filter(created__month=timezone.now().month)

    # Ordering
    order_by = request.GET.get('order_by', '-created')
    leads = leads.order_by(order_by)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(leads, 20)
    leads_page = paginator.get_page(page)

    context = {
        'leads': leads_page,
        'page_obj': leads_page,
        'sales_users': User.objects.filter(groups__name='Sales'),
        'lead_sources': LeadSource.objects.filter(is_active=True),
        'stage_choices': Lead.STAGE_CHOICES,
        'now': timezone.now(),
    }

    return render(request, 'leads/lead_list.html', context)


@login_required
def lead_detail(request, pk):
    """
    Display detailed view of a single lead
    """
    lead = get_object_or_404(Lead, pk=pk)
    activities = lead.activities.all().select_related('user')[:50]
    followups = lead.followups.all()

    context = {
        'lead': lead,
        'activities': activities,
        'followups': followups,
        'stage_choices': Lead.STAGE_CHOICES,
    }

    return render(request, 'new_lead/leads/lead_detail.html', context)

#
# @login_required
# def lead_create(request):
#     """
#     Create a new lead
#     """
#     if request.method == 'POST':
#         form = LeadForm(request.POST)
#         if form.is_valid():
#             lead = form.save(commit=False)
#             lead.assigned_by = request.user
#             lead.save()
#
#             # Create activity
#             LeadActivity.objects.create(
#                 lead=lead,
#                 user=request.user,
#                 activity_type='note',
#                 description=f'Lead created by {request.user.get_full_name()}'
#             )
#
#             messages.success(request, 'Lead created successfully!')
#             return redirect('lead_detail', pk=lead.id)
#     else:
#         form = LeadForm()
#
#     context = {
#         'form': form,
#         'title': 'Create New Lead'
#     }
#
#     return render(request, 'leads/lead_form.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LeadForm
from .models import Lead, LeadActivity


@login_required
def lead_create(request):
    if request.method == 'POST':
        form = LeadForm(request.POST, organization=request.organization)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.assigned_by = request.user
            lead.organization = request.organization  # ensure organization is set
            lead.save()
            # Create activity
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='note',
                description=f'Lead created by {request.user.get_full_name()}'
            )
            messages.success(request, 'Lead created successfully!')
            return redirect(f'/new-lead/leads/{lead.id}/')
    else:
        form = LeadForm(organization=request.organization)

    context = {
        'form': form,
        'title': 'Create New Lead'
    }
    return render(request, 'leads/lead_form.html', context)

#
# @login_required
# def lead_edit(request, pk):
#     """
#     Edit an existing lead
#     """
#     lead = get_object_or_404(Lead, pk=pk)
#
#     if request.method == 'POST':
#         form = LeadForm(request.POST, instance=lead)
#         if form.is_valid():
#             form.save()
#
#             messages.success(request, 'Lead updated successfully!')
#             return redirect('lead_detail', pk=lead.id)
#     else:
#         form = LeadForm(instance=lead)
#
#     context = {
#         'form': form,
#         'lead': lead,
#         'title': f'Edit Lead: {lead.name}'
#     }
#
#     return render(request, 'leads/lead_form.html', context)

@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk, organization=request.organization)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead, organization=request.organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead updated successfully!')
            return redirect(f'/new-lead/leads/{lead.id}/')
    else:
        form = LeadForm(instance=lead, organization=request.organization)

    context = {
        'form': form,
        'lead': lead,
        'title': f'Edit Lead: {lead.name}'
    }
    return render(request, 'leads/lead_form.html', context)


@login_required
def lead_update_stage(request, pk):
    """
    Update lead stage
    """
    if request.method == 'POST':
        lead = get_object_or_404(Lead, pk=pk)
        old_stage = lead.stage
        new_stage = request.POST.get('stage')

        if new_stage and new_stage in dict(Lead.STAGE_CHOICES):
            lead.stage = new_stage

            # Update probability based on stage
            stage_probabilities = {
                'new': 10,
                'qualified': 30,
                'survey': 50,
                'quote': 70,
                'negotiation': 85,
                'won': 100,
                'lost': 0,
            }
            lead.probability = stage_probabilities.get(new_stage, 0)

            if new_stage == 'won':
                lead.converted_at = timezone.now()
            elif new_stage == 'lost':
                lead.lost_at = timezone.now()

            lead.save()

            # Log activity
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='stage_change',
                description=f'Stage changed from {dict(Lead.STAGE_CHOICES)[old_stage]} to {dict(Lead.STAGE_CHOICES)[new_stage]}'
            )

            messages.success(request, f'Lead stage updated to {dict(Lead.STAGE_CHOICES)[new_stage]}')

    return redirect(f'/new-lead/leads/{lead.id}/')


@login_required
def lead_mark_lost(request, pk):
    """
    Mark a lead as lost with reason
    """
    if request.method == 'POST':
        lead = get_object_or_404(Lead, pk=pk)
        lead.stage = 'lost'
        lead.lost_reason = request.POST.get('lost_reason')
        lead.competitor = request.POST.get('competitor')
        lead.notes = request.POST.get('notes')
        lead.lost_at = timezone.now()
        lead.probability = 0
        lead.save()

        # Log activity
        LeadActivity.objects.create(
            lead=lead,
            user=request.user,
            activity_type='note',
            description=f'Lead marked as lost. Reason: {lead.lost_reason}'
        )

        messages.info(request, 'Lead marked as lost')

    return redirect(f'/new-lead/leads/{lead.id}/')


@login_required
def lead_add_activity(request, pk):
    """
    Add an activity to a lead
    """
    if request.method == 'POST':
        lead = get_object_or_404(Lead, pk=pk)

        activity_type = request.POST.get('activity_type')
        description = request.POST.get('description')

        metadata = {}
        if activity_type == 'call':
            metadata = {
                'duration': request.POST.get('duration'),
                'outcome': request.POST.get('outcome'),
            }
        elif activity_type == 'followup':
            followup_date = request.POST.get('followup_date')
            if followup_date:
                lead.next_followup = followup_date
                lead.save()

                # Create follow-up record
                FollowUp.objects.create(
                    lead=lead,
                    user=request.user,
                    scheduled_date=followup_date,
                    notes=description
                )

        # Create activity
        LeadActivity.objects.create(
            lead=lead,
            user=request.user,
            activity_type=activity_type,
            description=description,
            metadata=metadata
        )

        # Update last contacted
        lead.last_contacted = timezone.now()
        lead.save()

        messages.success(request, 'Activity added successfully!')

    return redirect(f'/new-lead/leads/{lead.id}/')


@login_required
def lead_export(request):
    """
    Export leads to CSV
    """
    leads = Lead.objects.all()

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="leads_export_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'City', 'Stage', 'Score', 'Assigned To', 'Created Date', 'Value'])

    for lead in leads:
        writer.writerow([
            lead.name,
            lead.phone,
            lead.email,
            lead.city,
            lead.get_stage_display(),
            lead.get_score_display(),
            lead.assigned_to.get_full_name() if lead.assigned_to else '',
            lead.created.date(),
            lead.estimated_value or 0,
        ])

    return response