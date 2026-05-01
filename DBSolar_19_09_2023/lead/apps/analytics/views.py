# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.db.models import Count, Sum, Q, Avg
# from django.utils import timezone
# from datetime import timedelta, datetime
# import json
#
# from apps.leads.models import Lead, LeadSource, LeadActivity
# from apps.revenue.models import Revenue
# from django.contrib.auth.models import User
#
#
# @login_required
# def analytics_dashboard(request):
#     """
#     Analytics dashboard with all metrics
#     """
#     today = timezone.now().date()
#     first_day_month = today.replace(day=1)
#
#     # Lead Analytics
#     total_leads = Lead.objects.count()
#
#     # Cost per lead
#     total_cost = LeadSource.objects.aggregate(total=Sum('cost_per_lead'))['total'] or 0
#     cost_per_lead = total_cost / total_leads if total_leads > 0 else 0
#
#     # Cost per acquisition
#     won_leads = Lead.objects.filter(stage='won').count()
#     cost_per_acquisition = total_cost / won_leads if won_leads > 0 else 0
#
#     # Lead aging
#     aging_buckets = {
#         '0-7': Lead.objects.filter(created__date__gte=today - timedelta(days=7)).count(),
#         '8-15': Lead.objects.filter(
#             created__date__gte=today - timedelta(days=15),
#             created__date__lt=today - timedelta(days=7)
#         ).count(),
#         '16-30': Lead.objects.filter(
#             created__date__gte=today - timedelta(days=30),
#             created__date__lt=today - timedelta(days=15)
#         ).count(),
#         '30+': Lead.objects.filter(created__date__lt=today - timedelta(days=30)).count(),
#     }
#
#     # Lead source performance
#     lead_sources_analytics = []
#     for source in LeadSource.objects.all():
#         leads = Lead.objects.filter(source=source)
#         conversions = leads.filter(stage='won').count()
#         conversion_rate = (conversions / leads.count() * 100) if leads.count() > 0 else 0
#         revenue = Revenue.objects.filter(lead__source=source).aggregate(total=Sum('amount'))['total'] or 0
#         total_cost = leads.count() * (source.cost_per_lead or 0)
#         roi = ((revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
#
#         lead_sources_analytics.append({
#             'name': source.name,
#             'lead_count': leads.count(),
#             'conversion_count': conversions,
#             'conversion_rate': round(conversion_rate, 1),
#             'cost_per_lead': source.cost_per_lead or 0,
#             'total_cost': total_cost,
#             'revenue': revenue,
#             'roi': round(roi, 1),
#         })
#
#     # Sales performance
#     sales_performance = []
#     for user in User.objects.filter(groups__name='Sales'):
#         leads = Lead.objects.filter(assigned_to=user)
#         total_leads = leads.count()
#         conversions = leads.filter(stage='won').count()
#         conversion_rate = (conversions / total_leads * 100) if total_leads > 0 else 0
#         revenue = Revenue.objects.filter(lead__assigned_to=user).aggregate(total=Sum('amount'))['total'] or 0
#         avg_deal_size = revenue / conversions if conversions > 0 else 0
#
#         # Follow-up compliance
#         total_followups = LeadActivity.objects.filter(user=user, activity_type='followup').count()
#         completed_followups = LeadActivity.objects.filter(
#             user=user,
#             activity_type='followup',
#             created__date__gte=first_day_month
#         ).count()
#         followup_compliance = (completed_followups / total_followups * 100) if total_followups > 0 else 0
#
#         sales_performance.append({
#             'id': user.id,
#             'name': user.get_full_name() or user.username,
#             'email': user.email,
#             'leads_assigned': total_leads,
#             'conversions': conversions,
#             'conversion_rate': round(conversion_rate, 1),
#             'revenue': revenue,
#             'avg_deal_size': avg_deal_size,
#             'followup_compliance': round(followup_compliance, 1),
#         })
#
#     # Lost lead analysis
#     lost_reasons = Lead.objects.filter(stage='lost').values('lost_reason').annotate(
#         count=Count('id')
#     ).order_by('-count')
#
#     lost_reason_labels = [item['lost_reason'] or 'Unknown' for item in lost_reasons]
#     lost_reason_data = [item['count'] for item in lost_reasons]
#
#     # Overall metrics
#     overall_conversion = (won_leads / total_leads * 100) if total_leads > 0 else 0
#
#     # Average closing time
#     closed_leads = Lead.objects.filter(stage='won', converted_at__isnull=False)
#     total_days = 0
#     for lead in closed_leads:
#         days = (lead.converted_at.date() - lead.created.date()).days
#         total_days += days
#     avg_closing_days = total_days / closed_leads.count() if closed_leads.count() > 0 else 0
#
#     context = {
#         'total_leads': total_leads,
#         'cost_per_lead': round(cost_per_lead, 2),
#         'cost_per_acquisition': round(cost_per_acquisition, 2),
#         'avg_lead_age': 15,  # Calculate from actual data
#         'lead_sources_analytics': lead_sources_analytics,
#         'source_labels': json.dumps([s['name'] for s in lead_sources_analytics]),
#         'source_data': json.dumps([s['lead_count'] for s in lead_sources_analytics]),
#         'aging_data': json.dumps(list(aging_buckets.values())),
#         'sales_performance': sales_performance,
#         'lost_reason_labels': json.dumps(lost_reason_labels),
#         'lost_reason_data': json.dumps(lost_reason_data),
#         'overall_conversion': round(overall_conversion, 1),
#         'avg_closing_days': round(avg_closing_days, 1),
#         'followup_compliance': 85,  # Calculate from actual data
#     }
#
#     return render(request, 'analytics/analytics.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import json
from decimal import Decimal

from apps.leads.models import Lead, LeadSource, LeadActivity
from apps.revenue.models import Revenue
from django.contrib.auth.models import User


@login_required
def analytics_dashboard(request):
    """
    Analytics dashboard with all metrics
    """
    today = timezone.now().date()
    first_day_month = today.replace(day=1)

    # ---------------------------
    # Lead Source Performance
    # ---------------------------
    lead_sources_analytics = []
    source_labels = []
    source_data = []

    for source in LeadSource.objects.filter(is_active=True):
        leads = Lead.objects.filter(source=source)
        lead_count = leads.count()
        conversions = leads.filter(stage='won').count()
        conversion_rate = (conversions / lead_count * 100) if lead_count > 0 else 0

        # Revenue from this source (all time, paid)
        revenue = Revenue.objects.filter(
            lead__source=source,
            payment_status='paid'
        ).aggregate(total=Sum('amount'))['total']
        revenue = float(revenue) if revenue else 0.0

        # Cost per lead (as float)
        cost_per_lead = float(source.cost_per_lead) if source.cost_per_lead else 0.0
        total_cost = cost_per_lead * lead_count

        # ROI: (revenue - total_cost) / total_cost * 100
        if total_cost > 0:
            roi = ((revenue - total_cost) / total_cost) * 100
        else:
            roi = 0.0

        lead_sources_analytics.append({
            'name': source.name,
            'lead_count': lead_count,
            'conversion_count': conversions,
            'conversion_rate': round(conversion_rate, 1),
            'cost_per_lead': cost_per_lead,
            'total_cost': total_cost,
            'revenue': revenue,
            'roi': round(roi, 1),
        })

        # For chart (leads per source)
        source_labels.append(source.name)
        source_data.append(lead_count)

    # ---------------------------
    # Lead Aging Report
    # ---------------------------
    aging_buckets = {
        '0-7 days': Lead.objects.filter(created__date__gte=today - timedelta(days=7)).count(),
        '8-15 days': Lead.objects.filter(
            created__date__gte=today - timedelta(days=15),
            created__date__lt=today - timedelta(days=7)
        ).count(),
        '16-30 days': Lead.objects.filter(
            created__date__gte=today - timedelta(days=30),
            created__date__lt=today - timedelta(days=15)
        ).count(),
        '30+ days': Lead.objects.filter(created__date__lt=today - timedelta(days=30)).count(),
    }
    aging_labels = list(aging_buckets.keys())
    aging_data = list(aging_buckets.values())

    # ---------------------------
    # Lost Lead Analysis
    # ---------------------------
    lost_reasons = Lead.objects.filter(stage='lost').values('lost_reason').annotate(
        count=Count('id')
    ).order_by('-count')

    lost_reason_labels = [item['lost_reason'] or 'Unknown' for item in lost_reasons]
    lost_reason_data = [item['count'] for item in lost_reasons]

    # Lost by source
    lost_by_source = Lead.objects.filter(stage='lost').values('source__name').annotate(
        count=Count('id')
    ).order_by('-count')
    lost_source_labels = [item['source__name'] or 'Unknown' for item in lost_by_source]
    lost_source_data = [item['count'] for item in lost_by_source]

    # ---------------------------
    # Sales Performance
    # ---------------------------
    sales_performance = []
    for user in User.objects.filter(groups__name='Sales'):
        leads = Lead.objects.filter(assigned_to=user)
        total_leads = leads.count()
        conversions = leads.filter(stage='won').count()
        conversion_rate = (conversions / total_leads * 100) if total_leads > 0 else 0

        # Revenue from this user (all time, paid)
        revenue = Revenue.objects.filter(
            lead__assigned_to=user,
            payment_status='paid'
        ).aggregate(total=Sum('amount'))['total']
        revenue = float(revenue) if revenue else 0.0

        # Follow-up compliance (simplified)
        total_followups = LeadActivity.objects.filter(user=user, activity_type='followup').count()
        completed_followups = LeadActivity.objects.filter(
            user=user,
            activity_type='followup',
            created__date__gte=first_day_month
        ).count()
        followup_percentage = (completed_followups / total_followups * 100) if total_followups > 0 else 0

        sales_performance.append({
            'name': user.get_full_name() or user.username,
            'leads_assigned': total_leads,
            'conversions': conversions,
            'conversion_rate': round(conversion_rate, 1),
            'revenue': revenue,
            'followup_percentage': round(followup_percentage, 1),
            'performance': round(conversion_rate, 1),  # placeholder
        })

    # Sort by revenue for leaderboard
    sales_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # ---------------------------
    # Overall metrics
    # ---------------------------
    total_leads = Lead.objects.count()
    won_leads = Lead.objects.filter(stage='won').count()
    lost_leads = Lead.objects.filter(stage='lost').count()

    # Cost per lead (average across all sources)
    total_cost_all = sum(s['total_cost'] for s in lead_sources_analytics)
    cost_per_lead_avg = total_cost_all / total_leads if total_leads > 0 else 0

    # Cost per acquisition
    cost_per_acquisition = total_cost_all / won_leads if won_leads > 0 else 0

    # Average lead age
    if total_leads > 0:
        total_days = sum((today - l.created.date()).days for l in Lead.objects.all())
        avg_lead_age = total_days / total_leads
    else:
        avg_lead_age = 0

    # Average closing time (for won leads)
    closed_leads = Lead.objects.filter(stage='won', converted_at__isnull=False)
    if closed_leads.exists():
        total_days = sum((l.converted_at.date() - l.created.date()).days for l in closed_leads)
        avg_closing_days = total_days / closed_leads.count()
    else:
        avg_closing_days = 0

    overall_conversion = (won_leads / total_leads * 100) if total_leads > 0 else 0
    followup_compliance = 75  # placeholder, can be computed later

    context = {
        # Lead Analytics
        'total_leads': total_leads,
        'cost_per_lead': round(cost_per_lead_avg, 2),
        'cost_per_acquisition': round(cost_per_acquisition, 2),
        'avg_lead_age': round(avg_lead_age, 1),

        # Lead source data
        'lead_sources_analytics': lead_sources_analytics,
        'source_labels': json.dumps(source_labels),
        'source_data': json.dumps(source_data),

        # Aging report
        'aging_labels': json.dumps(aging_labels),
        'aging_data': json.dumps(aging_data),

        # Lost reasons
        'lost_reason_labels': json.dumps(lost_reason_labels),
        'lost_reason_data': json.dumps(lost_reason_data),
        'lost_source_labels': json.dumps(lost_source_labels),
        'lost_source_data': json.dumps(lost_source_data),

        # Sales performance
        'sales_performance': sales_performance,
        'overall_conversion': round(overall_conversion, 1),
        'avg_closing_days': round(avg_closing_days, 1),
        'followup_compliance': followup_compliance,

        # Additional for tables
        'lost_leads': Lead.objects.filter(stage='lost').select_related('assigned_to')[:20],
    }

    return render(request, 'analytics/analytics.html', context)