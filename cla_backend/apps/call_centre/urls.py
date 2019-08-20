from django.conf.urls import patterns, url, include
from rest_framework import routers

from core.drf.router import NestedSimpleRouter, NestedCLARouter, AdvancedSimpleRouter
from core import routers as core_routers

from . import views


router = routers.DefaultRouter()
adv_router = AdvancedSimpleRouter()
router.register(r"category", views.CategoryViewSet)
router.register(r"provider/rota", views.OutOfHoursRotaViewSet)  # Has update
router.register(r"provider", views.ProviderViewSet)
adv_router.register(r"case", views.CaseViewSet)  # has update
router.register(r"user", views.UserViewSet, base_name="user")
router.register(r"event", views.EventViewSet, base_name="event")
router.register(r"knowledgebase/article", views.ArticleViewSet)
router.register(r"knowledgebase/category", views.ArticleCategoryViewSet)
router.register(r"guidance/note", views.GuidanceNoteViewSet, base_name="guidance_note")
router.register(r"notifications/notification", views.NotificationViewSet, base_name="notifications")
router.register(r"adaptations", views.AdaptationDetailsMetadataViewSet, base_name="adaptations-metadata")  # has update
router.register(r"mattertype", views.MatterTypeViewSet)
router.register(r"mediacode", views.MediaCodeViewSet)
router.register(r"contact_research_methods", views.ContactResearchMethodViewSet)
router.register(r"feedback", views.FeedbackViewSet)  # has update
router.register(r"case_archive", views.CaseArchivedViewSet)
router.register(r"csvupload", views.CSVUploadViewSet)
adv_router.register(r"complaints/complaint", views.ComplaintViewSet, base_name="complaints")
router.register(r"complaints/category", views.ComplaintCategoryViewSet, base_name="complaints-categories")

timer_router = core_routers.SingletonRouter()
timer_router.register(r"timer", views.TimerViewSet, base_name="timer")

case_one2one_router = NestedCLARouter(adv_router, "case", lookup="case")
case_one2one_router.register(
    r"eligibility_check", views.EligibilityCheckViewSet, base_name="eligibility_check"
)  # has update
case_one2one_router.register(r"personal_details", views.PersonalDetailsViewSet)  # has update
case_one2one_router.register(r"adaptation_details", views.AdaptationDetailsViewSet)  # has update
case_one2one_router.register(r"eod_details", views.EODDetailsViewSet)  # has update
case_one2one_router.register(r"thirdparty_details", views.ThirdPartyDetailsViewSet)  # has update
case_one2one_router.register(r"diagnosis", views.DiagnosisViewSet, base_name="diagnosis")  # has update

case_one2many_router = NestedSimpleRouter(adv_router, r"case", lookup="case")
case_one2many_router.register(r"logs", views.LogViewSet)
case_one2many_router.register(r"notes_history", views.CaseNotesHistoryViewSet)

complaint_one2many_router = NestedSimpleRouter(adv_router, r"complaints/complaint", lookup="complaint")
complaint_one2many_router.register(r"logs", views.ComplaintLogViewset)


urlpatterns = patterns(
    "",
    url(r"^complaints/constants/?$", views.ComplaintConstantsView.as_view()),
    url(r"^", include(complaint_one2many_router.urls)),
    url(r"^", include(case_one2one_router.urls)),
    url(r"^", include(case_one2many_router.urls)),
    url(r"^", include(adv_router.urls)),
    url(r"^", include(router.urls)),
    url(r"^", include(timer_router.urls)),
)
