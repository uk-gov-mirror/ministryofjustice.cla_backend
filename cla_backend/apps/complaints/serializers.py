# -*- coding: utf-8 -*-
from rest_framework import serializers
from cla_eventlog.models import ComplaintLog

from .models import Category, Complaint


class CategorySerializerBase(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class ComplaintSerializerBase(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True)
    full_name = serializers.CharField(
        source='eod.case.personal_details.full_name',
        read_only=True)
    category_of_law = serializers.CharField(
        source='eod.case.eligibility_check.category',
        read_only=True)
    case_reference = serializers.CharField(
        source='eod.case.reference',
        read_only=True)

    class Meta:
        model = Complaint
        read_only_fields = (
            'created', 'modified', 'created_by',
        )


class ComplaintLogSerializerBase(serializers.ModelSerializer):
    class Meta:
        model = ComplaintLog
