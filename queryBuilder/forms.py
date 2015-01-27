from django import forms
from django.forms.widgets import SplitDateTimeWidget, SelectMultiple, TimeInput, DateInput


STATION_CHOICES = (('station1', 'Station1'),
                   ('station1', 'Station2'),
                   ('station3', 'Station3'))

CONDITION_TYPES = (('voltage', 'Voltage'),)

CONDITION_OPERATORS = (('=', '='),
                       ('<', '<'),
                       ('<=', '<='),
                       ('>', '>'),
                       ('>=', '>='))

DATE_FORMAT = '%m/%d/%Y'

TIME_FORMAT = '%H:%M'


# The query form attributes
class QueryForm(forms.Form):
    query_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Name'}))

    start_date = forms.DateField(widget=DateInput(attrs={'placeholder': 'mm/dd/yyyy', 'class': 'datepicker'},
                                                  format=DATE_FORMAT))
    start_time = forms.TimeField(widget=TimeInput(attrs={'placeholder': 'HH:mm (24-hour)'}, format=TIME_FORMAT))

    end_date = forms.DateField(widget=DateInput(attrs={'placeholder': 'mm/dd/yyyy', 'class': 'datepicker'},
                                                format=DATE_FORMAT))
    end_time = forms.TimeField(widget=TimeInput(attrs={'placeholder': 'HH:mm (24-hour)'}, format=TIME_FORMAT))

    stations = forms.CharField(widget=forms.Select(choices=STATION_CHOICES))

    condition_type = forms.CharField(widget=forms.Select(choices=CONDITION_TYPES))
    condition_operator = forms.CharField(widget=forms.Select(choices=CONDITION_OPERATORS))
    condition_value = forms.IntegerField()

    file = forms.FileField()


class ConditionForm(forms.Form):
    condition_type = forms.CharField(required=False, widget=forms.Select(choices=CONDITION_TYPES))
    condition_operator = forms.CharField(required=False, widget=forms.Select(choices=CONDITION_OPERATORS))
    condition_value = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'style': 'width: 70px;'}))