from django.shortcuts import get_object_or_404
from django_object_actions import DjangoObjectActions

from bc_api.crm_wrapper import CrmWrapper
from bc_api.models.crm import *
from django.contrib import admin


class MarketingListAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ['name', 'list_id', 'bc_site']
    list_filter = ['bc_site']

    def import_lists(self, request, queryset):
        site = BCSite.objects.first()
        wrapper = CrmWrapper(site)
        updated_lists = wrapper.get_marketing_lists()
        self.message_user(request, "Created or updated %d lists." % (len(updated_lists)))

    import_lists.label = "Import Lists"  # optional
    import_lists.short_description = "Imports marketing lists from a BC site"

    changelist_actions = ('import_lists', )

class crmFormFieldValueInline(admin.TabularInline):
    model = crmFormFieldValue
    raw_id_fields = ['contactRecord']

class CaseAdmin(admin.ModelAdmin):
    list_display = ('caseId', 'bc_site', 'caseSubject', 'createDate', 'contactRecord', 'contact_link')
    list_filter = ['bc_site', 'caseSubject']
    raw_id_fields = ['contactRecord']
    search_fields = ['id', 'caseId', 'contactRecord__entityId']
    list_select_related = True
    inlines = [crmFormFieldValueInline]

    def contact_link(self, obj):
        link = "<a href='/admin/bc_api/contactrecord/%s/'>View</a>" % obj.contactRecord.id if obj.contactRecord else '#'
        return link
    contact_link.allow_tags = True

class addressesAdmin(admin.ModelAdmin):
    list_display = ('addressLine1', 'addressLine2', 'city', 'zipcode', 'state', 'countryCode', 'contactRecord', 'order',
                    'addressTypeID')
    raw_id_fields = ['contactRecord']


class addressInline(admin.TabularInline):
    model = addresses

class phoneNosInline(admin.TabularInline):
    model = phoneNos

class ContactRecordAdmin(admin.ModelAdmin):
    list_display = ['entityId', 'firstName', 'lastName', 'username']
    search_fields = ['id', 'entityId']
    list_filter = ['bc_site']
    inlines = [addressInline,phoneNosInline, crmFormFieldValueInline]


class OrderAdmin(admin.ModelAdmin):
    list_display = (
    'orderId', 'bc_site', 'invoiceNumber', 'orderName', 'createDate', 'lastUpdateDate', 'invoiceDate', 'contactRecord',
    'totalOrderAmount', 'isRecur')
    search_fields = ['orderId', 'contactRecord__entityId']


class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = (
    'paymentMethodTypeID', 'amount', 'paymentStatusID', 'transactionNumber', 'transactionAuthCode', 'Description',
    'paymentDate')


class phoneNosAdmin(admin.ModelAdmin):
    pass


class OrderStatusAdmin(admin.ModelAdmin):
    pass


class crmFormFieldValueAdmin(admin.ModelAdmin):
    list_display = ('crmFormField', 'fieldValue', 'case', 'order', 'contactRecord')


class fileListAdmin(admin.ModelAdmin):
    list_display = ('fileId', 'fileName', 'fileSize', 'case')


class OrderProductAdmin(admin.ModelAdmin):
    list_display = ['productId', 'productCode', 'productDescription', 'units', 'productName', 'variationId', 'order']


class crmFormAdmin(admin.ModelAdmin):
    list_display = ('formId', 'formName', 'bc_site')


class crmFormFieldAdmin(admin.ModelAdmin):
    list_display = ('fieldId', 'fieldName', 'crmForm', 'bc_site')


class BCSiteAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'secure_site_url', 'site_id', 'site_code', 'check_recurring_orders']


admin.site.register(BCSite, BCSiteAdmin)
admin.site.register(MarketingList, MarketingListAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(addresses, addressesAdmin)
admin.site.register(ContactRecord, ContactRecordAdmin)
admin.site.register(crmFormField, crmFormFieldAdmin)
admin.site.register(crmForm, crmFormAdmin)
admin.site.register(crmFormFieldValue, crmFormFieldValueAdmin)
admin.site.register(phoneNos, phoneNosAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderPayment, OrderPaymentAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(fileList, fileListAdmin)
admin.site.register(OrderStatus, OrderStatusAdmin)
