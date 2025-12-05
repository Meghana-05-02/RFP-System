from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'rfp'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'rfps', views.RFPViewSet, basename='rfp')

urlpatterns = [
    # ViewSet routes (includes /vendors/, /rfps/, etc.)
    path('', include(router.urls)),
    
    # Custom function-based views
    path('<int:pk>/', views.get_rfp_detail, name='rfp-detail'),
    path('create-from-text/', views.create_rfp_from_text, name='create-from-text'),
    path('comparison/<int:rfp_id>/', views.get_rfp_comparison, name='rfp-comparison'),
    path('ai-recommendation/<int:rfp_id>/', views.get_ai_recommendation, name='ai-recommendation'),
]
