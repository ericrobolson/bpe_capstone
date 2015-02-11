from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.forms import formset_factory
from django.utils.datastructures import MultiValueDictKeyError

from query.forms import QueryForm, ConditionForm, SignalForm
from query.models import Query
from stations.models import Station

import status_response
import datetime
import time
import json


class Condition:
    def __init__(self, condition_type, condition_operator, condition_value):
        self.condition_type = condition_type
        self.condition_operator = condition_operator
        self.condition_value = condition_value

    def __str__(self):
        return self.condition_type + " " + self.condition_operator + " " + str(self.condition_value)


class QueryObject:
    def __init__(self, model_id, start_date_time, end_date_time,
                 conditions, file_name, signals,qr_file,
		 ar_file, sr_cpu, sr_completed, sr_available, sr_used):
        self.model_id = model_id
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time
        self.conditions = conditions
        self.file_name = file_name
        self.signals = signals
	self.qr_file = qr_file
	self.ar_file = ar_file
	self.sr_cpu = sr_cpu
	self.sr_completed = sr_completed
	self.sr_available = sr_available
	self.sr_used = sr_used

@login_required
def query_index(request):
    return render(request, 'query/query.html')

@login_required
def query_result(request):
    return render(request, 'query/query-result.html')


form_submitted = False
query_model = Query()
query_object = QueryObject(None, None, None, None, None, None, None, None, None, None, None, None)

# Builds a query given user input
@login_required
def query_builder(request):
    global form_submitted
    global query_model
    global query_object
    condition_form_set = formset_factory(ConditionForm, extra=1)
    username = None
    if request.user.is_authenticated():
        username = request.user.username
        query_model.user_name = username
        creation_date = time.strftime("%Y-%m-%d %H:%M:%S")
        query_model.create_date_time = creation_date

    if request.method == 'POST':
        form = QueryForm(request.POST, request.FILES)
        signal_form = SignalForm(request.POST)
        condition_form = condition_form_set(request.POST)

        # global form_submitted
        if signal_form.is_valid() and form_submitted and 'send' in request.POST:
            query_model.save()
            query_object.model_id = query_model.id
            query_object.signals = signal_form.cleaned_data['signals']
            print(convert_to_json(query_object))
            form_submitted = False
	   
	    # return results page           
            context = {'query_id':query_model.id, 'qr_file':query_model.qr_file, 'ar_file':query_model.ar_file,
	   	       'sr_cpu':query_model.sr_cpu, 'sr_completed':query_model.sr_completed,
		       'sr_available':query_model.sr_available, 'sr_used':query_model.sr_used}
            return render(request, 'query/query-result.html', context)

        elif 'send' in request.POST:
            return HttpResponseRedirect('/query/query-builder/')

        if form.is_valid() and condition_form.is_valid() and 'refresh' in request.POST:
            query_model.owner = request.user
            query_model.query_name = form.cleaned_data['query_name']
            start_date = form.cleaned_data['start_date']
            start_time = form.cleaned_data['start_time']
            start_date_time = datetime.datetime.combine(start_date, start_time)
            query_model.start_date_time = start_date_time
            end_date = form.cleaned_data['end_date']
            end_time = form.cleaned_data['end_time']
            end_date_time = datetime.datetime.combine(end_date, end_time)
            query_model.end_date_time = end_date_time
            stations = form.cleaned_data['stations']
            query_model.set_stations(stations)
            condition_type = form.cleaned_data['condition_type']
            condition_operator = form.cleaned_data['condition_operator']
            condition_value = form.cleaned_data['condition_value']
            primary_condition = Condition(condition_type, condition_operator, condition_value)
            conditions = []
            if condition_value is not None:
                conditions = [primary_condition]

            for condition_field in condition_form:
                condition = Condition(condition_field.cleaned_data['condition_type'],
                                      condition_field.cleaned_data['condition_operator'],
                                      condition_field.cleaned_data['condition_value'])
                if condition.condition_value is not None:
                    conditions.append(condition)
            condition_strings = []
            for condition in conditions:
                condition_strings.append(condition.__str__())
            query_model.set_conditions(condition_strings)

            try:
                file = request.FILES["file"]
                file_name = file.name
            except MultiValueDictKeyError:
                file_name = ""
            query_model.file_name = file_name

            query_object = QueryObject(None, start_date_time, end_date_time,
                                       conditions, file_name, None, None, None, None, None, None, None)

            form_submitted = True

            station_objects = []
            for station in stations:
                station_queryset = Station.objects.filter(PMU_Name_Short=station)
                for station_object in station_queryset:
                    station_objects.append(station_object)
            SignalForm.update_signals(signal_form, station_objects, conditions)

            return HttpResponseRedirect('/query/query-builder/')
    else:
        form = QueryForm()
        signal_form = SignalForm()

    context = {'username': username, 'form': form, 'signal_form': signal_form, 'formset': condition_form_set,
               'signals_refreshed': int(form_submitted)}
    return render(request, 'query/query-builder.html', context)


def convert_to_json(query_param):
    query_id = query_param.model_id
    start_date_time = query_param.start_date_time
    end_date_time = query_param.end_date_time
    conditions = query_param.conditions
    file_name = query_param.file_name
    signals = query_param.signals

    voltage_conditions = []
    current_conditions = []
    frequency_conditions = []

    for condition in conditions:
        condition_type = condition.condition_type
        if condition_type == "voltage":
            voltage_conditions.append(condition.__str__())
        elif condition_type == "current":
            current_conditions.append(condition.__str__())
        else:
            frequency_conditions.append(condition.__str__())

    query = json.dumps({
        "query": {
            "query_id": query_id,
            "start": start_date_time.__str__(),
            "end": end_date_time.__str__(),
            "analysis_file": file_name,
            "signal_id": signals
        }
    })

    return query
