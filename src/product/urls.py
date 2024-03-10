from django.urls import path
from django.views.generic import TemplateView

from product.views.product import CreateProductView, ProductListView, ProductAPIView
from product.views.variant import VariantView, VariantCreateView, VariantEditView

# from src.product.views.product import ProductListView

app_name = "product"

urlpatterns = [
    # Variants URLs
    path('variants/', VariantView.as_view(), name='variants'),
    path('variant/create', VariantCreateView.as_view(), name='create.variant'),
    path('variant/<int:id>/edit', VariantEditView.as_view(), name='update.variant'),

    # Products URLs
    path('create/', CreateProductView.as_view(), name='create.product'),
    path('save/', ProductAPIView.as_view()),
    path('list/', ProductListView.as_view(), name='list.product'),
]
