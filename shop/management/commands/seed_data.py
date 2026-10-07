from django.core.management.base import BaseCommand

from shop.models import Category, Product


TREES = [
    ("Alpine Balsam Fir", 95.00, "https://static.wixstatic.com/media/c837a6_bf4cb44bed8c4e95b2f5f50e2041b174~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_bf4cb44bed8c4e95b2f5f50e2041b174~mv2.jpg", True),
    ("Classic Fraser Fir", 95.00, "https://static.wixstatic.com/media/c837a6_e9e73cfb8128490ca20b8d7ca9a496f9~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_e9e73cfb8128490ca20b8d7ca9a496f9~mv2.jpg", False),
    ("Alpine Nordmann Fir", 120.00, "https://static.wixstatic.com/media/c837a6_918527a10955452daa2e16c50f4c9dab~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_918527a10955452daa2e16c50f4c9dab~mv2.jpg", False),
]

LIGHTS = [
    ("Green Sculptural Candle Trio", 35.00, "https://static.wixstatic.com/media/c837a6_4200890b8bf741d29afa990eed828858~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_4200890b8bf741d29afa990eed828858~mv2.jpg", True),
    ("Red Pleated Tree Candle", 35.00, "https://static.wixstatic.com/media/c837a6_d402765473a943d2a506d8f6beed16e7~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_d402765473a943d2a506d8f6beed16e7~mv2.jpg", False),
    ("Ivory Cone Candle", 35.00, "https://static.wixstatic.com/media/c837a6_67ab2af6f75e4eb9b2f827f30ba70044~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_67ab2af6f75e4eb9b2f827f30ba70044~mv2.jpg", False),
]

ORNAMENTS = [
    ("Olive Honeycomb", 5.00, "https://static.wixstatic.com/media/c837a6_f5264560fc674e9d8c8980eeb2ac7785~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_f5264560fc674e9d8c8980eeb2ac7785~mv2.jpg", True),
    ("Ivory Honeycomb", 5.00, "https://static.wixstatic.com/media/c837a6_c01f08e4dab743618f7c92098e333f5d~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_c01f08e4dab743618f7c92098e333f5d~mv2.jpg", False),
    ("Red Honeycomb", 5.00, "https://static.wixstatic.com/media/c837a6_fad33659557940a484146b128c1f9ec5~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_fad33659557940a484146b128c1f9ec5~mv2.jpg", False),
    ("Red Ceramic Bow", 45.00, "https://static.wixstatic.com/media/c837a6_dbacc8f2c6014c7184c5d55eb0d33378~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_dbacc8f2c6014c7184c5d55eb0d33378~mv2.jpg", False),
    ("Stripes Ceramic Bow", 45.00, "https://static.wixstatic.com/media/c837a6_6efbcfa850244818ab9376c61db76a2c~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_6efbcfa850244818ab9376c61db76a2c~mv2.jpg", False),
    ("White Ceramic Bow", 45.00, "https://static.wixstatic.com/media/c837a6_83c5159728ed4ff9bc66c4adfbbd316b~mv2.jpeg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_83c5159728ed4ff9bc66c4adfbbd316b~mv2.jpeg", False),
    ("Green Stripe Bauble", 12.00, "https://static.wixstatic.com/media/c837a6_a39bb75bae9c443cb8e720d6e8ef0d4d~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_a39bb75bae9c443cb8e720d6e8ef0d4d~mv2.jpg", False),
    ("Red Dot Bauble", 12.00, "https://static.wixstatic.com/media/c837a6_5ac814634200416687187630ce14203c~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_5ac814634200416687187630ce14203c~mv2.jpg", False),
    ("Pink Stripe Bauble", 12.00, "https://static.wixstatic.com/media/c837a6_8a8cfd10490340eb96708e64b0e8eee2~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_8a8cfd10490340eb96708e64b0e8eee2~mv2.jpg", False),
    ("Blue Blossom Bauble", 12.00, "https://static.wixstatic.com/media/c837a6_f7f9bf4c0975457484b11bc6e26f40e0~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_f7f9bf4c0975457484b11bc6e26f40e0~mv2.jpg", False),
    ("Silver Flower Bauble", 12.00, "https://static.wixstatic.com/media/c837a6_d9f90a9ffb6e4273b8b3f4e2c9bf9a05~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_d9f90a9ffb6e4273b8b3f4e2c9bf9a05~mv2.jpg", False),
    ("Ivory Flower Bauble", 12.00, "https://static.wixstatic.com/media/c837a6_c753ed22fbaa4481b05ea982e1821ce5~mv2.jpg/v1/fill/w_360,h_480,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/c837a6_c753ed22fbaa4481b05ea982e1821ce5~mv2.jpg", False),
]


class Command(BaseCommand):
    help = 'Seed the database with the original Christmas Boutique categories & products.'

    def handle(self, *args, **options):
        data = {
            'Trees': TREES,
            'Lights': LIGHTS,
            'Ornaments': ORNAMENTS,
        }
        created_products = 0
        for cat_name, products in data.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for name, price, image_url, is_bestseller in products:
                _, created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        'category': category,
                        'price': price,
                        'image_url': image_url,
                        'is_bestseller': is_bestseller,
                        'is_featured': is_bestseller,
                    },
                )
                if created:
                    created_products += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {Category.objects.count()} categories, '
            f'{created_products} new products added ({Product.objects.count()} total).'
        ))
