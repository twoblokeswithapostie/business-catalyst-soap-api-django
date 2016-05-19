import pytz
from suds import WebFault
from suds.client import Client
from bc_api.models.ecommerce import Catalogue, Product, ProductSalePrice, ProductRetailPrice, ProductWholesalePrice, \
    WholesaleTaxCode, TaxCode, GroupProduct, GroupProductDescription, CatalogueName, ProductVariation, RelatedProduct


class EcommerceWrapper:
    """
        Wrapper for all the BC Retrieve Functions for Ecommerce Catalogues/Products
    """

    def __init__(self, site):
        self.site = site
        url = str(self.site.secure_site_url + 'catalystwebservice/catalystecommercewebservice.asmx?WSDL')
        self.client = Client(url)

    def catalogue_list_retrieve(self, parent_catalogue_id):
        try:
            response = self.client.service.Catalogue_ListRetrieve(str(self.site.admin_username),
                                                                  str(self.site.admin_password),
                                                                  int(self.site.site_id),
                                                                  int(parent_catalogue_id))
        except WebFault as e:
            raise e

        if not response:
            return
        catalogue_list = response.Catalogue

        for catalogue_response in catalogue_list:
            new_catalogue = self.save_catalogue(catalogue_response)
            self.catalogue_list_retrieve(new_catalogue.catalogueId)

    def catalogue_retrieve(self, catalogue_id):
        try:
            response = self.client.service.Catalogue_Retrieve(str(self.site.admin_username),
                                                              str(self.site.admin_password),
                                                              int(self.site.site_id),
                                                              int(catalogue_id))
        except WebFault, e:
            # You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the
            # contact
            # result.message in this case will give you something like the following message:
            # u"Server raised fault: 'Server was unable to process request. ---> ERROR: Contact record could not be
            # retrieved.'"
            raise e
        return self.save_catalogue(response)

    def save_catalogue(self, response):
        try:
            catalogue = Catalogue.objects.get(catalogueId=int(response.Id), bc_site=self.site)
        except Catalogue.DoesNotExist:
            catalogue = Catalogue.objects.create(catalogueId=response.Id, bc_site=self.site)

        catalogue.catalogueId = response.Id
        catalogue.ParentId = response.ParentId
        catalogue.TemplateId = response.TemplateId
        catalogue.RoleId = response.RoleId
        catalogue.Weight = response.Weight
        catalogue.DisplayTypeId = response.DisplayTypeId
        if response.Name:
            catalogue.Name = response.Name.encode('ascii', 'xmlcharrefreplace').encode('utf-8')
        if response.Description:
            catalogue.Description = response.Description.encode('ascii', 'xmlcharrefreplace').encode('utf-8')
        catalogue.ReleaseDate = self.site.local_to_utc(response.ReleaseDate).replace(tzinfo=pytz.UTC)
        catalogue.ExpiryDate = self.site.local_to_utc(response.ExpiryDate).replace(tzinfo=pytz.UTC)
        if hasattr(response, "Notify"):
            catalogue.Notify = response.Notify
        else:
            catalogue.Notify = None

        catalogue.CreateBy = response.CreateBy
        catalogue.CreateDate = response.CreateDate
        catalogue.LastUpdateBy = response.LastUpdateBy
        catalogue.LastUpdateDate = response.LastUpdateDate

        if hasattr(response, "UseFriendlyURL"):
            catalogue.UseFriendlyURL = response.UseFriendlyURL

        catalogue.ExcludeFromFeed = response.ExcludeFromFeed
        catalogue.Enabled = response.Enabled
        catalogue.Deleted = response.Deleted
        catalogue.MinPrice = response.MinPrice
        catalogue.MaxPrice = response.MaxPrice
        catalogue.PriceSlots = response.PriceSlots
        catalogue.ProductStatsXml = response.ProductsStatsXml
        catalogue.ReIndex = response.ReIndex

        # our own metadata
        catalogue.save()
        return catalogue

    def product_list_retrieve(self, catalogueId=-1):
        try:
            response = self.client.service.Product_ListRetrieve(str(self.site.admin_username),
                                                                str(self.site.admin_password),
                                                                int(self.site.site_id),
                                                                int(catalogueId))
        except WebFault, e:
            raise e

        product_list = []
        for productResponse in response.Products:
            product = self.save_product(productResponse)
            product_list.append(product)
        return product_list

    def save_product(self, productResponse):
        try:
            product = Product.objects.get(productCode=productResponse.productCode, bc_site=self.site)
        except Product.DoesNotExist:
            product = Product.objects.create(productCode=productResponse.productCode, bc_site=self.site)

        product.productId = productResponse.productId

        if productResponse.productName is not None:
            product.productName = unicode(
                productResponse.productName.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        else:
            product.productName = None

        if productResponse.description is not None:
            product.description = unicode(
                productResponse.description.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        else:
            product.description = None

        if productResponse.smallImage is not None:
            product.smallImage = unicode(
                productResponse.smallImage.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        else:
            product.smallImage = None

        if productResponse.largeImage is not None:
            product.largeImage = unicode(
                productResponse.largeImage.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        else:
            product.largeImage = None

        if hasattr(productResponse, "supplierEntityId"):
            product.supplierEntityId = productResponse.supplierEntityId

        product.supplierCommission = productResponse.supplierCommission
        product.weight = productResponse.weight

        if hasattr(productResponse, "relatedProducts") and productResponse.relatedProducts != "":
            self.save_relatedProducts(productResponse.relatedProducts, product)

        if hasattr(productResponse, "tags"):
            product.tags = productResponse.tags

        product.unitType = productResponse.unitType

        if hasattr(productResponse, "minUnites"):
            product.minUnits = productResponse.minUnits

        if hasattr(productResponse, "maxUnits"):
            product.maxUnits = productResponse.maxUnits

        if hasattr(productResponse, "inStock"):
            product.inStock = productResponse.inStock

        if hasattr(productResponse, 'onOrder'):
            product.onOrder = productResponse.onOrder

        if hasattr(productResponse, "reOrder"):
            product.reOrder = productResponse.reOrder

        product.inventoryControl = productResponse.inventoryControl
        product.canPreOrder = productResponse.canPreOrder
        product.custom1 = unicode(productResponse.custom1.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if productResponse.custom1 is not None else ""
        product.custom2 = unicode(productResponse.custom2.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if productResponse.custom2 is not None else ""
        product.custom3 = unicode(productResponse.custom3.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if productResponse.custom3 is not None else ""
        product.custom4 = unicode(productResponse.custom4.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if productResponse.custom4 is not None else ""
        product.popletImages = productResponse.popletImages

        if hasattr(productResponse, "enabled"):
            product.enabled = productResponse.enabled
        else:
            product.enabled = True

        if hasattr(productResponse, "deleted"):
            product.deleted = productResponse.deleted

        product.captureDetails = productResponse.captureDetails
        product.downloadLimitCount = productResponse.downloadLimitCount
        product.limitDownloadsToIP = productResponse.limitDownloadsToIP
        product.isOnSale = productResponse.isOnSale
        product.hideIfNoStock = productResponse.hideIfNoStock

        if productResponse.productAttributes is not None:
            product.productAttributes = unicode(
                productResponse.productAttributes.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        else:
            product.productAttributes = None

        product.isGiftVoucher = productResponse.isGiftVoucher
        product.enableDropShipping = productResponse.enableDropShipping

        # Dimension bullshit

        if hasattr(productResponse, 'productWeight'):
            product.productWeight = productResponse.productWeight

        if hasattr(productResponse, 'productWidth'):
            product.productWidth = productResponse.productWidth

        if hasattr(productResponse, 'productHeight'):
            product.productHeight = productResponse.productHeight

        if hasattr(productResponse, 'productDepth'):
            product.productDepth = productResponse.productDepth

        product.excludeFromSearch = productResponse.excludeFromSearch
        product.productTitle = unicode(productResponse.productTitle.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if productResponse.productTitle is not None else ""

        if hasattr(productResponse, 'cycletypeId'):
            product.cycletypeId = productResponse.cycletypeId

        if hasattr(productResponse, 'cycletypeCount'):
            product.cycletypeCount = productResponse.cycletypeCount

        product.slug = unicode(productResponse.slug.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if productResponse.slug is not None else ""

        if hasattr(productResponse, 'hasVariations'):
            product.hasVariations = productResponse.hasVariations

        product.save()

        # Now create all the related stuff
        if productResponse.pricesSaleArray != "":
            self.save_saleprices(productResponse.pricesSaleArray, product)

        if productResponse.pricesRetailArray != "":
            self.save_retailprices(productResponse.pricesRetailArray, product)

        if productResponse.pricesWholesaleArray != "":
            self.save_wholesaleprices(productResponse.pricesWholesaleArray, product)

        if productResponse.wholesaleTaxCodeArray != "":
            self.save_wholesaletaxcodes(productResponse.wholesaleTaxCodeArray, product)

        if productResponse.taxCodeArray != "":
            self.save_taxcodes(productResponse.taxCodeArray, product)

        if productResponse.groupProducts != "":
            self.save_groupproducts(productResponse.groupProducts, product)

        if productResponse.groupProductsDescriptions != "":
            self.save_groupproductsdescriptions(productResponse.groupProductsDescriptions, product)

        if hasattr(productResponse, 'variations'):
            self.save_variations(productResponse.variations, product)

        ### Finally Add all available Catalogues

        if productResponse.cataloguesArray != "":
            self.save_catalogues(productResponse.cataloguesArray, product)

        return product

    def product_retrieve(self, product_code):
        try:
            response = self.client.service.Product_Retrieve(str(self.site.admin_username),
                                                            str(self.site.admin_password),
                                                            int(self.site.site_id),
                                                            str(product_code))
        except WebFault, e:
            # You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the
            # contact
            # result.message in this case will give you something like the following message:
            # u"Server raised fault: 'Server was unable to process request. ---> ERROR: Contact record could not be
            # retrieved.'"
            raise e

        try:
            product = Product.objects.get(productCode=int(response.productCode), bc_site=self.site)
        except Product.DoesNotExist:
            product = Product.objects.create(productCode=response.productCode, bc_site=self.site)

        product.productId = response.productId
        product.productName = unicode(response.productName.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        product.description = unicode(response.description.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        product.smallImage = unicode(response.smallImage.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
        product.largeImage = unicode(response.largeImage.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))

        if hasattr(response, "supplierEntityId"):
            product.supplierEntityId = response.supplierEntityId

        product.supplierCommission = response.supplierCommission
        product.weight = response.weight

        if hasattr(response, "relatedProducts") and response.relatedProducts != "":
            self.save_relatedProducts(response.relatedProducts, product)

        if hasattr(response, "tags"):
            product.tags = response.tags

        product.unitType = response.unitType

        if hasattr(response, "minUnites"):
            product.minUnits = response.minUnits

        if hasattr(response, "maxUnits"):
            product.maxUnits = response.maxUnits

        if hasattr(response, "inStock"):
            product.inStock = response.inStock

        product.onOrder = response.onOrder

        if hasattr(response, "reOrder"):
            product.reOrder = response.reOrder

        product.inventoryControl = response.inventoryControl
        product.canPreOrder = response.canPreOrder
        product.custom1 = unicode(response.custom1.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if response.custom1 is not None else ""
        product.custom2 = unicode(response.custom2.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if response.custom2 is not None else ""
        product.custom3 = unicode(response.custom3.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if response.custom3 is not None else ""
        product.custom4 = unicode(response.custom4.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if response.custom4 is not None else ""
        product.popletImages = response.popletImages

        if hasattr(response, "enabled"):
            product.enabled = response.enabled

        if hasattr(response, "deleted"):
            product.deleted = response.deleted

        product.captureDetails = response.captureDetails
        product.downloadLimitCount = response.downloadLimitCount
        product.limitDownloadsToIP = response.limitDownloadsToIP
        product.isOnSale = response.isOnSale
        product.hideIfNoStock = response.hideIfNoStock
        product.productAttributes = response.productAttributes.encode(
            'utf-8') if response.productAttributes is not None else ""
        product.isGiftVoucher = response.isGiftVoucher
        product.enableDropShipping = response.enableDropShipping

        # Dimension bullshit

        if hasattr(response, 'productWeight'):
            product.productWeight = response.productWeight

        if hasattr(response, 'productWidth'):
            product.productWidth = response.productWidth

        if hasattr(response, 'productHeight'):
            product.productHeight = response.productHeight

        if hasattr(response, 'productDepth'):
            product.productDepth = response.productDepth

        product.excludeFromSearch = response.excludeFromSearch
        product.productTitle = unicode(response.productTitle.encode('ascii', 'xmlcharrefreplace').encode(
            'utf-8')) if response.productTitle is not None else ""

        if hasattr(response, 'cycletypeId'):
            product.cycletypeId = response.cycletypeId

        if hasattr(response, 'cycletypeCount'):
            product.cycletypeCount = response.cycletypeCount
        product.slug = response.slug

        if hasattr(response, 'hasVariations'):
            product.hasVariations = response.hasVariations

        product.save()

        # Now create all the related stuff
        if response.pricesSaleArray != "":
            self.save_saleprices(response.pricesSaleArray, product)

        if response.pricesRetailArray != "":
            self.save_retailprices(response.pricesRetailArray, product)

        if response.pricesWholesaleArray != "":
            self.save_wholesaleprices(response.pricesWholesaleArray, product)

        if response.wholesaleTaxCodeArray != "":
            self.save_wholesaletaxcodes(response.wholesaleTaxCodeArray, product)

        if response.taxCodeArray != "":
            self.save_taxcodes(response.taxCodeArray, product)

        if response.groupProducts != "":
            self.save_groupproducts(response.groupProducts, product)

        if response.groupProductsDescriptions != "":
            self.save_groupproductsdescriptions(response.groupProductsDescriptions, product)

        if hasattr(response, 'variations'):
            self.save_variations(response.variations, product)

        ### Finally Add all available Catalogues

        if response.cataloguesArray != "":
            self.save_catalogues(response.cataloguesArray, product)

        return product

    def save_saleprices(self, pricesSaleArray, product):
        # Delete all the old sale prices first
        for existing_price in product.pricesSaleArray.all():
            existing_price.delete()

        for new_price in pricesSaleArray.string:
            ProductSalePrice.objects.create(data=new_price, product=product)

    def save_retailprices(self, pricesRetailArray, product):
        # Delete all the old sale prices first
        for existing_price in product.pricesRetailArray.all():
            existing_price.delete()

        for new_price in pricesRetailArray.string:
            ProductRetailPrice.objects.create(data=new_price, product=product)

    def save_wholesaleprices(self, pricesWholesaleArray, product):
        for existing_price in product.pricesWholesaleArray.all():
            existing_price.delete()

        for new_price in pricesWholesaleArray.string:
            ProductWholesalePrice.objects.create(data=new_price, product=product)

    def save_wholesaletaxcodes(self, wholesaleTaxCodeArray, product):
        for existing_taxcode in product.wholesaleTaxCodeArray.all():
            existing_taxcode.delete()

        for new_taxcode in wholesaleTaxCodeArray.string:
            WholesaleTaxCode.objects.create(data=new_taxcode, product=product)

    def save_taxcodes(self, taxCodeArray, product):
        for existing_taxcode in product.taxCodeArray.all():
            existing_taxcode.delete()

        for new_taxcode in taxCodeArray.string:
            TaxCode.objects.create(data=new_taxcode, product=product)

    def save_groupproducts(self, groupProducts, product):
        for existing_groupproduct in product.groupProducts.all():
            existing_groupproduct.delete()

        for new_groupproduct in groupProducts.string:
            GroupProduct.objects.create(data=new_groupproduct, product=product)

    def save_groupproductsdescriptions(self, groupProductsDescriptions, product):
        for existing_groupproductdescription in product.groupProductsDescriptions.all():
            existing_groupproductdescription.delete()

        for new_groupproductdescription in groupProductsDescriptions.string:
            GroupProductDescription.objects.create(data=new_groupproductdescription, product=product)

    def save_variations(self, variations, product):
        for existing_variations in product.variations.all():
            existing_variations.delete()

        for variation in variations.ProductVariation:
            new_variation = ProductVariation.objects.create(
                productVariationId=variation.id,
                enabled=variation.enabled,
                inStock=variation.inStock,
                onOrder=variation.onOrder,
                product=product,
                bc_site=product.bc_site
            )

            save_again = False
            if hasattr(variation, 'options'):
                new_variation.options = unicode(variation.options.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
                save_again = True
            if hasattr(variation, 'code'):
                new_variation.code = unicode(variation.code.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
                save_again = True

            if save_again:
                new_variation.save()

    def save_catalogues(self, cataloguesArray, product):
        # You should save the Catalogue Strings somewhere anyway so you can do the M2M adding asynchronously
        for existing_catalogue_names in product.catalogue_names.all():
            existing_catalogue_names.delete()

        # Remove all the many to many relationships here
        for catalogue in product.catalogues.all():
            product.catalogue_names.remove(catalogue)

        # Now re save all the catalogues
        for new_catalogue_name in cataloguesArray.string:
            new_catalogue_name = unicode(new_catalogue_name.encode('ascii', 'xmlcharrefreplace').encode('utf-8'))
            CatalogueName.objects.create(name=new_catalogue_name, product=product)
            clean_catalogue_name = new_catalogue_name.lstrip('/').rstrip('/')

            possible_catalogues = Catalogue.objects.filter(Name=clean_catalogue_name, bc_site=product.bc_site)
            # Always take the first one, we don't have much of any other choice, site owner has to be mindful that
            # no two catalogues have the same name
            if possible_catalogues:
                product.catalogues.add(possible_catalogues[0])

    def save_relatedProducts(self, relatedProducts, product):
        for existing_related_product in product.relatedproducts.all():
            existing_related_product.delete()

        for new_related_product in relatedProducts.string:
            RelatedProduct.objects.create(data=new_related_product, product=product)
