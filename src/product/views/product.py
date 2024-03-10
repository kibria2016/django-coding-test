from collections import defaultdict
from datetime import datetime, timedelta

from django.core import paginator
from django.db.models import Q, Min, Count, Max
from django.views import generic
from django.views.generic import ListView
from product.models import Variant, Product, ProductVariantPrice, ProductVariant
from .serializers import ProductSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context


class ProductAPIView(APIView):
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Print the validation errors to debug
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 2

    def get_queryset(self):
        queryset = super().get_queryset()  # Get the default queryset
        product = self.request.GET.get('title', '')  # Get search query (product name)
        variant_id = self.request.GET.get('variant')  # Get selected variant
        min_price = self.request.GET.get('price_from', None)  # Get minimum price (if any)
        max_price = self.request.GET.get('price_to', None)  # Get maximum price (if any)
        date = self.request.GET.get('date', None)  # Get start date (if any)

        # Case 1: Only Product name is provided
        if product and not variant_id and not min_price and not max_price and not date:
            return queryset.filter(title__icontains=product)

        # Case 2: Only variant is provided
        if variant_id and not product and not min_price and not max_price and not date:
            return queryset.filter(productvariant__variant_title=variant_id)

        # Case 3: Both product name and variant are provided
        if product and variant_id and not min_price and not max_price and not date:
            return queryset.filter(Q(title__icontains=product) | Q(productvariant__variant_title=variant_id))

        # Case 4: Only price range is provided
        if min_price and max_price and not product and not variant_id and not date:
            # Filter ProductVariantPrice objects by price range
            price_queryset = ProductVariantPrice.objects.filter(price__range=(min_price, max_price))
            # Get unique product IDs from the filtered ProductVariantPrice queryset
            product_ids = price_queryset.values_list('product_id', flat=True).distinct()
            # Filter Product queryset based on the product IDs
            return queryset.filter(id__in=product_ids)

        # Case 5: Product name, variant, and price range are provided
        if product and variant_id and min_price and max_price and not date:
            # Filter products by product name and variant
            queryset = queryset.filter(Q(title__icontains=product) | Q(productvariant__variant_title=variant_id))
            # Filter ProductVariantPrice objects by price range
            price_queryset = ProductVariantPrice.objects.filter(price__range=(min_price, max_price))
            # Get unique product IDs from the filtered ProductVariantPrice queryset
            product_ids = price_queryset.values_list('product_id', flat=True).distinct()
            # Filter Product queryset based on the product IDs
            return queryset.filter(id__in=product_ids)

        # Case 6: Product name and price range are provided
        if product and min_price and max_price and not variant_id and not date:
            # Filter products by product name
            queryset = queryset.filter(title__icontains=product)
            # Filter ProductVariantPrice objects by price range
            price_queryset = ProductVariantPrice.objects.filter(price__range=(min_price, max_price))
            # Get unique product IDs from the filtered ProductVariantPrice queryset
            product_ids = price_queryset.values_list('product_id', flat=True).distinct()
            # Filter Product queryset based on the product IDs
            return queryset.filter(id__in=product_ids)

        # Additional case: Date range is provided
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')  # Adjust format as needed
                # Calculate end of day for the selected date
                end_of_day = date_obj + timedelta(days=1)
                # Filter records between the start and end of the selected day
                return queryset.filter(created_at__range=(date_obj, end_of_day))
            except ValueError:
                # Handle invalid date format errors (optional)
                pass

        return queryset.distinct()  # Ensure distinct products are returned

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']

        # Get all product variants
        product_variants = ProductVariant.objects.select_related('variant').all()

        # Create a defaultdict to store variants grouped by main variant group
        main_variant_groups = defaultdict(set)

        # Iterate over product variants and group them by main variant group
        for product_variant in product_variants:
            main_variant_groups[product_variant.variant.title].add(
                (product_variant.variant.id, product_variant.variant_title))

        # Convert the sets to lists to maintain the order of insertion
        main_variant_groups = {group: list(variants) for group, variants in main_variant_groups.items()}

        # Pass the main variant groups to the template
        context['main_variant_groups'] = main_variant_groups

        # Pass the main variant groups to the template
        # for group, variants in main_variant_groups.items():
        #     print(group)
        #
        #     for variant_id, variant_title in variants:
        #         print(variant_id, variant_title)

        context['variants'] = product_variants
        context['main_variant_groups'] = main_variant_groups
        context['is_paginated'] = paginator.num_pages > 1
        context['start_index'] = page_obj.start_index()
        context['end_index'] = page_obj.end_index()
        context['total_products'] = paginator.count

        return context
