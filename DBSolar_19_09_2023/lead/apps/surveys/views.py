from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
import csv

from .models import Survey, SurveyImage
from .forms import SurveyForm, SurveyImageForm, engineer_users_queryset
from apps.leads.models import Lead
@login_required
def survey_list(request):
    """
    List all surveys with filters
    """
    surveys = Survey.objects.all().select_related('lead', 'engineer')

    # Apply filters
    status = request.GET.get('status')
    if status:
        surveys = surveys.filter(status=status)

    engineer = request.GET.get('engineer')
    if engineer:
        surveys = surveys.filter(engineer_id=engineer)

    from_date = request.GET.get('from_date')
    if from_date:
        surveys = surveys.filter(scheduled_date__date__gte=from_date)

    to_date = request.GET.get('to_date')
    if to_date:
        surveys = surveys.filter(scheduled_date__date__lte=to_date)

    context = {
        'surveys': surveys,
        'engineers': engineer_users_queryset(),
    }

    return render(request, 'surveys/survey_list.html', context)


@login_required
def survey_detail(request, pk):
    """
    Display detailed view of a survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    context = {
        'survey': survey,
    }

    return render(request, 'surveys/survey_detail.html', context)


@login_required
def survey_create(request):
    """
    Create a new survey
    """
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.created_by = request.user
            survey.save()

            messages.success(request, 'Survey scheduled successfully!')
            return redirect('survey_detail', pk=survey.id)
    else:
        lead_id = request.GET.get('lead')
        initial = {}
        if lead_id:
            initial['lead'] = lead_id
        form = SurveyForm(initial=initial)

    context = {
        'form': form,
        'title': 'Schedule New Survey'
    }

    return render(request, 'surveys/survey_form.html', context)


@login_required
def survey_edit(request, pk):
    """
    Edit an existing survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Survey updated successfully!')
            return redirect('survey_detail', pk=survey.id)
    else:
        form = SurveyForm(instance=survey)

    context = {
        'form': form,
        'survey': survey,
        'title': f'Edit Survey - {survey.lead.name}'
    }

    return render(request, 'surveys/survey_form.html', context)


@login_required
def survey_complete(request, pk):
    """
    Mark survey as complete
    """
    if request.method == 'POST':
        survey = get_object_or_404(Survey, pk=pk)
        survey.status = 'completed'
        survey.completed_date = timezone.now()
        survey.save()

        # Update lead stage
        if survey.lead.stage == 'survey':
            survey.lead.stage = 'quote'
            survey.lead.save()

        messages.success(request, 'Survey marked as complete!')

    return redirect('survey_detail', pk=pk)


@login_required
def survey_cancel(request, pk):
    """
    Cancel survey
    """
    if request.method == 'POST':
        survey = get_object_or_404(Survey, pk=pk)
        survey.status = 'cancelled'
        survey.save()

        messages.info(request, 'Survey cancelled.')

    return redirect('survey_detail', pk=pk)


@login_required
def upload_survey_image(request, pk):
    """
    Upload images for survey
    """
    survey = get_object_or_404(Survey, pk=pk)

    if request.method == 'POST' and request.FILES.get('image'):
        image = SurveyImage(
            survey=survey,
            image=request.FILES['image'],
            caption=request.POST.get('caption', ''),
            is_primary=request.POST.get('is_primary') == 'on'
        )
        image.save()

        # If this is primary, unset other primary images
        if image.is_primary:
            SurveyImage.objects.filter(survey=survey).exclude(pk=image.pk).update(is_primary=False)

        return JsonResponse({'success': True, 'image_id': image.id})

    return JsonResponse({'success': False}, status=400)


@login_required
def survey_export(request):
    """
    Export surveys to CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="surveys_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ['Lead Name', 'Engineer', 'Scheduled Date', 'Status', 'Feasibility', 'System Size', 'Completed Date'])

    surveys = Survey.objects.all().select_related('lead', 'engineer')
    for survey in surveys:
        writer.writerow([
            survey.lead.name,
            survey.engineer.get_full_name() if survey.engineer else 'Unassigned',
            survey.scheduled_date.strftime('%Y-%m-%d %H:%M'),
            survey.get_status_display(),
            survey.get_feasibility_display() if survey.feasibility else '',
            survey.recommended_size,
            survey.completed_date.strftime('%Y-%m-%d') if survey.completed_date else '',
        ])

    return response