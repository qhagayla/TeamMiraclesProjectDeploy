from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Stratum, Course, CourseAllocation, Upload


admin.site.register(Stratum)
admin.site.register(Course)
admin.site.register(CourseAllocation)
admin.site.register(Upload)
