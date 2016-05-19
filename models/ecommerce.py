from django.contrib import admin
from django.db import models
from suds.client import Client
from bc_api.models.crm import BCSite


class Catalogue(models.Model):
    """
        Representation of a BC Catalogue in our database
    """
    catalogueId = models.IntegerField("Catalogue ID (just Id in BC)", null=True, default=-1)
    ParentId = models.IntegerField("Parent ID", null=True, default=-1)
    TemplateId = models.IntegerField("TemplateId", null=True, default=-1)
    RoleId = models.IntegerField("RoleId", null=True, default=-1)
    Weight = models.IntegerField("Weight", null=True, default=-1)
    DisplayTypeId = models.IntegerField("DisplayTypeId", null=True, default=-1)
    Name = models.CharField("Name", max_length=1024, blank=True, null=True)
    Title = models.CharField("Title", max_length=1024, blank=True, null=True)
    Description = models.TextField("Description", blank=True, null=True)
    Image = models.CharField("Image", max_length=1024, blank=True, null=True)
    ReleaseDate = models.DateTimeField("ReleaseDate", null=True)
    ExpiryDate = models.DateTimeField("ExpiryDate", null=True)
    Notify = models.CharField("Notify", max_length=1024, null=True, blank=True)
    CreateBy = models.IntegerField("CreateBy (integer ID)", null=True, default=-1)
    CreateDate = models.DateTimeField("CreateDate", null=True)
    LastUpdateBy = models.IntegerField("LastUpdateBy (integer ID)", null=True, default=-1)
    LastUpdateDate = models.DateTimeField("LastUpdateDate", null=True)
    UseFriendlyURL = models.BooleanField("UseFriendlyUrl", default=True)
    ExcludeFromFeed = models.BooleanField("ExcludeFromFeed", default=False)
    Enabled = models.BooleanField("Enabled", default=False)
    Deleted = models.BooleanField("Deleted", default=False)
    MinPrice = models.DecimalField("MinPrice", max_digits=15, decimal_places=2, null=True)
    MaxPrice = models.DecimalField("MaxPrice", max_digits=15, decimal_places=2, null=True)
    PriceSlots = models.IntegerField("PriceSlots", null=True, default=0)
    ProductsStatsXml = models.TextField("ProductsStatsXml", blank=True, null=True)
    ReIndex = models.BooleanField("ReIndex", default=True)

    # Extra stuff inside CatalogueEntity
    Url = models.CharField("Url (from CatalogueEntity", max_length=1024, null=True, blank=True)
    Slug = models.CharField("Slug (from CatalogueEntity", max_length=1024, null=True, blank=True)

    db_creation_date = models.DateTimeField("DB Creation Date", auto_now_add=True)
    db_modified_date = models.DateTimeField("DB Modified Date", auto_now=True)

    bc_site = models.ForeignKey(BCSite, related_name='catalogues')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Catalogue ID: %s | Catalogue Name: %s" % (self.catalogueId, self.Name))


class CatalogueAdmin(admin.ModelAdmin):
    pass


admin.site.register(Catalogue, CatalogueAdmin)


class Product(models.Model):
    """
        Representation of a BC Product in our database
    """
    productId = models.IntegerField("productId (just Id in BC)", null=True, default=-1)
    productCode = models.CharField("productCode", max_length=1024, blank=True, null=True)
    productName = models.CharField("productName", max_length=1024, blank=True, null=True)
    description = models.TextField("description", blank=True, null=True)
    smallImage = models.CharField("smallImage", max_length=1024, blank=True, null=True)
    largeImage = models.CharField("largeImage", max_length=1024, blank=True, null=True)

    # Try to create as many of the array things out of Foreign Key Relationships as possible and use functions to create
    # the responses to send back to BC
    catalogues = models.ManyToManyField(Catalogue, related_name='products')

    supplierEntityId = models.IntegerField("supplierEntityId", null=True, default=-1)
    supplierCommission = models.FloatField("supplierCommision", default=0)
    weight = models.IntegerField("weight", null=True, default=0)

    #related Products - how to represent??? probably need some sort of meta item (FFS)

    tags = models.TextField("tags", null=True, blank=True)

    # Inventory Control
    unitType = models.CharField("unitType", max_length=100, null=True, blank=True)
    minUnits = models.IntegerField("minUnits", null=True, default=-1)
    maxUnits = models.IntegerField("maxUnits", null=True, default=-1)
    inStock = models.IntegerField("inStock", null=True, default=-1)
    onOrder = models.IntegerField("onOrder", null=True, default=-1)
    reOrder = models.IntegerField("reOrder", null=True, default=-1)
    inventoryControl = models.BooleanField("inventoryControl", default=False)
    canPreOrder = models.BooleanField("canPreOrder", default=False)

    # Custom Fields
    custom1 = models.TextField("custom1", null=True, blank=True)
    custom2 = models.TextField("custom2", null=True, blank=True)
    custom3 = models.TextField("custom3", null=True, blank=True)
    custom4 = models.TextField("custom4", null=True, blank=True)

    popletImages = models.TextField("popletImages", null=True, blank=True)
    enabled = models.BooleanField("enabled", default=True)
    deleted = models.BooleanField("deleted", default=False)
    captureDetails = models.NullBooleanField("captureDetails", null=True, default=False)

    downloadLimitCount = models.IntegerField("downloadLimitCount", null=True, default=-1)
    limitDownloadsToIP = models.IntegerField("limiDownloadsToIP", null=True, default=-1)
    isOnSale = models.BooleanField("isOnSale", default=False)
    hideIfNoStock = models.BooleanField("hideIfNoStock", default=True)
    productAttributes = models.TextField("productAttributes", null=True, blank=True)
    isGiftVoucher = models.BooleanField("isGiftVoucher", default=False)
    enableDropShipping = models.BooleanField("enableDropShipping", default=False)

    # Dimensions
    productWeight = models.IntegerField("productWeight", null=True, default=-1)
    productWidth = models.IntegerField("productWidth", null=True, default=-1)
    productHeight = models.IntegerField("productHeight", null=True, default=-1)
    productDepth = models.IntegerField("productDepth", null=True, default=-1)

    excludeFromSearch = models.BooleanField("excludeFromSearch", default=False)
    productTitle = models.CharField("productTitle", null=True, blank=True, max_length=1000)
    cycletypeId = models.IntegerField("cycleTypeId", null=True, default=0)
    cycletypeCount = models.IntegerField("cycletypeCount", null=True, default=-1)
    slug = models.CharField("slug", null=True, blank=True, max_length=1000)
    hasVariations = models.BooleanField("hasVariations", default=False)
    bc_site = models.ForeignKey(BCSite, related_name='products')

    class Meta:
        app_label = 'bc_api'
        ordering = ['productName']

    def __unicode__(self):
        return unicode("ID: %s - %s | Product Code: %s" % (self.productId, self.productName, self.productCode))

    def update_insert_to_bc(self):
        site = self.bc_site
        url = str(site.secure_site_url + 'catalystwebservice/catalystecommercewebservice.asmx?WSDL')
        client = Client(url)

        productList = client.factory.create('ArrayOfProducts')
        product = client.factory.create('Products')

        product.productId = self.productId
        if self.productCode:
            product.productCode = self.productCode

        if self.productName:
            product.productName = self.productName

        if self.description:
            product.description = self.description

        if self.smallImage:
            product.smallImage = self.smallImage

        if self.largeImage:
            product.largeImage = self.largeImage

        cataloguesArray = self.createCataloguesArray(client)
        if cataloguesArray:
            product.cataloguesArray = cataloguesArray

        pricesSaleArray = self.createPricesSaleArray(client)
        if pricesSaleArray:
            product.pricesSaleArray = pricesSaleArray

        pricesRetailArray = self.createPricesRetailArray(client)
        if pricesRetailArray:
            product.pricesRetailArray = pricesRetailArray

        pricesWholesaleArray = self.createPricesWholesaleArray(client)
        if pricesWholesaleArray:
            product.pricesWholesaleArray = pricesWholesaleArray

        wholesaleTaxCodeArray = self.createWholesaleTaxCodeArray(client)
        if wholesaleTaxCodeArray:
            product.wholesaleTaxCodeArray = wholesaleTaxCodeArray

        taxCodeArray = self.createTaxCodeArray(client)
        if taxCodeArray:
            product.taxCodeArray = taxCodeArray

        groupProducts = self.createGroupProducts(client)
        if groupProducts:
            product.groupProducts = groupProducts

        groupProductsDescriptions = self.createGroupProductsDescriptions(client)
        if groupProductsDescriptions:
            product.groupProductsDescriptions = groupProductsDescriptions

        product.supplierEntityId = self.supplierEntityId
        product.supplierCommission = self.supplierCommission
        product.weight = self.weight

        relatedProducts = self.createRelatedProducts(client)
        if relatedProducts:
            product.relatedProducts = relatedProducts

        if self.tags:
            product.tags = self.tags

        if self.unitType:
            product.unitType = self.unitType

        if self.minUnits:
            product.minUnits = self.minUnits

        if self.maxUnits:
            product.maxUnits = self.maxUnits

        if self.inStock:
            product.inStock = self.inStock

        if self.onOrder:
            product.onOrder = self.onOrder

        if self.reOrder:
            product.reOrder = self.reOrder

        product.inventoryControl = self.inventoryControl
        product.canPreOrder = self.canPreOrder

        if self.custom1:
            product.custom1 = self.custom1

        if self.custom2:
            product.custom1 = self.custom1

        if self.custom3:
            product.custom1 = self.custom1

        if self.custom4:
            product.custom1 = self.custom1

        if self.popletImages:
            product.popletImages = self.popletImages

        product.enabled = self.enabled
        product.deleted = self.deleted
        product.captureDetails = self.captureDetails
        product.downloadLimitCount = self.downloadLimitCount
        product.limitDownloadsToIP = self.limitDownloadsToIP
        product.isOnSale = self.isOnSale
        product.hideIfNoStock = self.hideIfNoStock

        if self.productAttributes:
            product.productAttributes = self.productAttributes

        product.isGiftVoucher = self.isGiftVoucher
        product.enableDropShipping = self.enableDropShipping

        if self.productWeight:
            product.productWeight = self.productWeight

        if self.productWidth:
            product.productWidth = self.productWidth

        if self.productHeight:
            product.productWeight = self.productHeight

        if self.productDepth:
            product.productDepth = self.productDepth

        product.excludeFromSearch = self.excludeFromSearch
        if self.productTitle:
            product.productTitle = self.productTitle

        if self.cycletypeId:
            product.cycletypeId = self.cycletypeId

        product.cycletypeCount = self.cycletypeCount

        if self.slug:
            product.slug = self.slug

        product.hasVariations = self.hasVariations

        variations = self.createVariations(client)
        if variations is not None:
            product.variations = variations

        productList.Products.append(product)
        ###
        try:
            response = client.service.Product_UpdateInsert(str(site.admin_username),
                                                           str(site.admin_password),
                                                           int(site.site_id),
                                                           productList)
        except Exception, e:
            print e
            raise e

        # Now that the product is in BC DB we retrieve it to get it's ID (what a bullshit workaround)
        if self.productId == -1:
            try:
                response = client.service.Product_Retrieve(str(site.admin_username),
                                                           str(site.admin_password),
                                                           int(site.site_id),
                                                           str(self.productCode))
            except Exception, e:
            #### You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the contact
            #### result.message in this case will give you something like the following message:
            #### u"Server raised fault: 'Server was unable to process request. ---> ERROR: Contact record could not be retrieved.'"
                return # we couldn't get the product code, move on, it's ok
            self.productId = response.productId
            self.save()




    def createCataloguesArray(self, client):
        catalogue_names = self.catalogue_names.all()
        if not catalogue_names.exists():
            return ""
        else:
            catalogueArray = client.factory.create('ArrayOfString')
            for name in catalogue_names:
                catalogueArray.string.append(name.name)
            return catalogueArray


    def createPricesSaleArray(self, client):
        prices = self.pricesSaleArray.all()
        if not prices.exists():
            return ""
        else:
            pricesSaleArray = client.factory.create('ArrayOfString')
            for price in prices:
                pricesSaleArray.string.append(price.data)
            return pricesSaleArray


    def createPricesRetailArray(self, client):
        prices = self.pricesRetailArray.all()
        if not prices.exists():
            return ""
        else:
            pricesRetailArray = client.factory.create('ArrayOfString')
            for price in prices:
                pricesRetailArray.string.append(price.data)
            return pricesRetailArray

    def createPricesWholesaleArray(self, client):
        prices = self.pricesWholesaleArray.all()
        if not prices.exists():
            return ""
        else:
            pricesWholesaleArray = client.factory.create('ArrayOfString')
            for price in prices:
                pricesWholesaleArray.string.append(price.data)
            return pricesWholesaleArray

    def createWholesaleTaxCodeArray(self, client):
        taxes = self.wholesaleTaxCodeArray.all()
        if not taxes.exists():
            return ""
        else:
            wholesaleTaxCodeArray = client.factory.create('ArrayOfString')
            for tax in taxes:
                wholesaleTaxCodeArray.string.append(tax.data)
            return wholesaleTaxCodeArray

    def createTaxCodeArray(self, client):
        taxes = self.taxCodeArray.all()
        if not taxes.exists():
            return ""
        else:
            taxCodeArray = client.factory.create('ArrayOfString')
            for tax in taxes:
                taxCodeArray.string.append(tax.data)
            return taxCodeArray

    def createGroupProducts(self, client):
        taxes = self.taxCodeArray.all()
        if not taxes.exists():
            return ""
        else:
            taxCodeArray = client.factory.create('ArrayOfString')
            for tax in taxes:
                taxCodeArray.string.append(tax.data)
            return taxCodeArray

    def createGroupProductsDescriptions(self, client):
        taxes = self.taxCodeArray.all()
        if not taxes.exists():
            return ""
        else:
            taxCodeArray = client.factory.create('ArrayOfString')
            for tax in taxes:
                taxCodeArray.string.append(tax.data)
            return taxCodeArray

    def createRelatedProducts(self, client):
        taxes = self.taxCodeArray.all()
        if not taxes.exists():
            return ""
        else:
            taxCodeArray = client.factory.create('ArrayOfString')
            for tax in taxes:
                taxCodeArray.string.append(tax.data)
            return taxCodeArray

    def createVariations(self, client):
        variations = self.variations.all()
        if not variations.exists():
            return ""
        else:
            variationArray = client.factory.create('ArrayOfProductVariation')
            for v in variations:
                variation = client.factory.create('ProductVariation')
                variation.id = v.productVariationId
                if v.options:
                    variation.options = v.options
                if v.code:
                    variation.code = v.code

                variation.enabled = v.enabled
                variation.inStock = v.inStock
                variation.onOrder = v.onOrder
                variationArray.ProductVariation.append(variation)
            return variationArray


### Models for supporting Products, all of these just need foreign key to Product and hold a string for data
### Any existing records are deleted whenever the product is pulled again from BC

class ProductSalePrice(models.Model):
    data = models.CharField("data", max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='pricesSaleArray')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Sale Price: %s for product: %s" % (self.data, self.product))


class ProductSalePriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(ProductSalePrice, ProductSalePriceAdmin)



class ProductRetailPrice(models.Model):
    data = models.CharField("data", max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='pricesRetailArray')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Retail Price: %s for product: %s" % (self.data, self.product))


class ProductRetailPriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(ProductRetailPrice, ProductRetailPriceAdmin)


class ProductWholesalePrice(models.Model):
    data = models.CharField("data", max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='pricesWholesaleArray')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Wholesale Price: %s for product: %s" % (self.data, self.product))

class ProductWholesalePriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(ProductWholesalePrice, ProductWholesalePriceAdmin)


class WholesaleTaxCode(models.Model):
    data = models.CharField("data", max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='wholesaleTaxCodeArray')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Wholesale Tax Code: %s for product: %s" % (self.data, self.product))

class WholesaleTaxCodeAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(WholesaleTaxCode, WholesaleTaxCodeAdmin)



class TaxCode(models.Model):
    data = models.CharField("data", max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='taxCodeArray')

    class Meta:
        app_label = 'bc_api'


    def __unicode__(self):
        return unicode("Tax Code: %s for product: %s" % (self.data, self.product))


class TaxCodeAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(TaxCode, TaxCodeAdmin)


class RelatedProduct(models.Model):
    data = models.CharField("data", max_length=100, null=True, blank=True)
    product = models.ForeignKey(Product, related_name='relatedproducts')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Related Product: %s for product: %s" % (self.data, self.product))


class RelatedProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(RelatedProduct, RelatedProductAdmin)


class GroupProduct(models.Model):
    data = models.TextField("data", null=True, blank=True)
    product = models.ForeignKey(Product, related_name='groupProducts')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Group Product: %s for product: %s" % (self.data, self.product))


class GroupProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(GroupProduct, GroupProductAdmin)

class GroupProductDescription(models.Model):
    data = models.TextField("data", null=True, blank=True)
    product = models.ForeignKey(Product, related_name='groupProductsDescriptions')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Group Product Description: %s for product: %s" % (self.data, self.product))

class GroupProductDescriptionAdmin(admin.ModelAdmin):
    list_display = ('product', 'data')

admin.site.register(GroupProductDescription, GroupProductDescriptionAdmin)


class CatalogueName(models.Model):
    name = models.CharField("Catalogue Name", max_length=1024)
    product = models.ForeignKey(Product, related_name='catalogue_names')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Catalogue Name: %s for Product: %s" % (self.name, self.product))


class CatalogueNameAdmin(admin.ModelAdmin):
    list_display = ('product', 'name')

admin.site.register(CatalogueName, CatalogueNameAdmin)


class ProductVariation(models.Model):
    productVariationId = models.IntegerField("productId (just 'id' in BC)", null=True, default=-1)
    options = models.TextField("options", blank=True, null=True)
    code = models.CharField("code", max_length=100, blank=True, null=True)
    enabled = models.BooleanField("enabled", default=True)
    inStock = models.IntegerField("inStock", null=True, default=-1)
    onOrder = models.IntegerField("onOrder", null=True, default=-1)
    product = models.ForeignKey(Product, related_name='variations')

    bc_site = models.ForeignKey(BCSite, related_name='product_variations', null=True)

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Product Variation: %s for product: %s" % (self.options, self.product))


class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ['options','code','enabled','inStock','onOrder','product']


admin.site.register(ProductVariation, ProductVariationAdmin)


class ShippingOption(models.Model):
    option_id = models.IntegerField("Shipping Option ID")
    option_description = models.CharField("Shipping Option Description", max_length=300)
    bc_site = models.ForeignKey(BCSite, related_name="shipping_option_bcsite")

    class Meta:
        app_label = "bc_api"

    def __unicode__(self):
        return unicode("ID: %s Description: %s Site: %s" % (self.option_id, self.option_description, self.bc_site))


class ShippingOptionAdmin(admin.ModelAdmin):
    pass

admin.site.register(ShippingOption, ShippingOptionAdmin)