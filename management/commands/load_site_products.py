from django.core.management.base import BaseCommand, CommandError
from bc_api.models.crm import BCSite
from bc_api.ecommerce_wrapper import EcommerceWrapper


class Command(BaseCommand):
    help = 'Loads all products for a given site e.g. python manage.py load_site_products <site_id>'

    def handle(self, *args, **options):
        site_id = args[0]

        #  Get BC site
        try:
            bc_site = BCSite.objects.get(site_id=site_id)
        except BCSite.DoesNotExist:
            raise CommandError('BC Site with ID %s does not exist!' % site_id)
        self.stdout.write('Site loaded: "%s".' % bc_site)

        wrapper = EcommerceWrapper(bc_site)
        product_list = wrapper.product_list_retrieve()
        i = 0
        for product in product_list:
            i += 1
            self.stdout.write('%s - Loaded : %s' % (i, product))

