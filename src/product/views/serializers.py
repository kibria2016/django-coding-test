from rest_framework import serializers
from product.models import Product, ProductImage, ProductVariant, ProductVariantPrice


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'file_path')


class ProductVariantPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantPrice
        fields = ('price', 'stock')


class ProductVariantSerializer(serializers.ModelSerializer):
    product_variant_prices = ProductVariantPriceSerializer(many=True)

    class Meta:
        model = ProductVariant
        fields = ('id', 'variant_title', 'product_variant_prices')


class ProductSerializer(serializers.ModelSerializer):
    # product_images = ProductImageSerializer(many=True, read_only=True)
    product_variants = ProductVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = ('id', 'title', 'sku', 'description', 'product_variants',)
        # fields = ('id', 'title', 'sku', 'description', 'product_images', 'product_variants')

    def create(self, validated_data):
        # product_images_data = validated_data.pop('product_images', [])
        product_variants_data = validated_data.pop('product_variants', [])

        product = Product.objects.create(**validated_data)

        # for image_data in product_images_data:
        #     ProductImage.objects.create(product=product, **image_data)

        for variant_data in product_variants_data:
            product_variant_prices_data = variant_data.pop('product_variant_prices', [])
            product_variant = ProductVariant.objects.create(product=product, **variant_data)

            for price_data in product_variant_prices_data:
                ProductVariantPrice.objects.create(product_variant=product_variant, **price_data)

        return product
