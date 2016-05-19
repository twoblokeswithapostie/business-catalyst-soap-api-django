from decimal import Decimal
import random
import re
import string
from django.db import models
import pytz
import datetime
from suds import WebFault
from suds.client import Client
from suds.plugin import MessagePlugin
from bc_api.constants import COUNTRIES_CHOICES


class LogPlugin(MessagePlugin):
    def sending(self, context):
        print(str(context.envelope))

    def received(self, context):
        print(str(context.reply))


PHONENOS_TYPES = (
    (1, "Home Phone"),
    (2, "Home Fax"),
    (3, "Work Phone"),
    (4, "Work Fax"),
    (5, "Cell Phone"),
    (6, "Pager"),
    (7, "Email Address 1 (Primary)"),
    (8, "Email Address 2"),
    (9, "Email Address 3"),
    (10, "Web Address")
)

ADDRESS_TYPES = (
    (1, "Home Address"),
    (2, "Work Address"),
    (3, "PO Box"),
    (5, 'Shipping Address'),
    (6, 'Pickup Address'),
    (7, 'Storage Address'),
    (8, 'Billing Address')
)

FIELD_TYPES = (
    (1, "Text (String)"),
    (2, "Number"),
    (3, "True/False (Boolean)"),
    (4, "DateTime"),
    (5, "List (Dropdown List)"),
    (6, "List (Checkbox List)"),
    (7, "List (Radio List)"),
    (8, "Image"),
    (9, "Text (Multiline)"),
    (10, "List (Listbox List)"),
    (11, "Text (Hyperlink)")
)

PAYMENT_METHODS = (
    (1, "Credit Card"),
    (2, "Cheque"),
    (3, "Cash"),
    (4, "EFT"),
    (5, "Paypal"),
    (7, "Hosted Credit Card e.g Google Checkout"),
    (8, "Direct Debit"),
    (9, "Gift Voucher"),
    (10, "Free")

)

NEW = 1
CLOSED = 2
OPEN = 3
REOPENED = 4
ESCALATED = 5

CASE_STATUS = (
    (NEW, 'New'),
    (CLOSED, 'Closed'),
    (OPEN, 'Open'),
    (REOPENED, 'Re-opened'),
    (ESCALATED, 'Escalated'),
)

GIFT_VOUCHER_PAYMENT_TYPE_ID = 9

ALL_TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))


class BCSite(models.Model):
    site_name = models.CharField("Site Name", max_length=1024)
    secure_site_url = models.CharField("Site URL", max_length=500)
    site_id = models.IntegerField(default=33228)
    admin_username = models.CharField("Admin Username", max_length=200)
    admin_password = models.CharField("Admin Password", max_length=100)
    site_timezone = models.CharField("Site Timezone", max_length=100, default='Australia/Sydney',
                                     choices=ALL_TIMEZONE_CHOICES)
    site_code = models.CharField("Random site code used in notification URL", max_length=10, null=True)
    check_recurring_orders = models.BooleanField("Check for Recurring Orders", default=False)
    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'
        ordering = ['site_name', 'site_code']

    def __unicode__(self):
        display = u"Name: %s Site ID: %s" % (self.site_name, self.site_id)
        return display

    def local_to_utc(self, naive_local_dt):
        if naive_local_dt.tzinfo is not None:
            naive_local_dt = naive_local_dt.replace(tzinfo=None)

        if naive_local_dt == datetime.datetime(1, 1, 1) or naive_local_dt == datetime.datetime(9999, 12, 31):
            return naive_local_dt.replace(tzinfo=pytz.UTC)

        utc_tz = pytz.utc

        if naive_local_dt.tzinfo is None:
            local_dt = pytz.timezone(self.site_timezone).localize(naive_local_dt)
        else:
            local_dt = naive_local_dt
        dt = utc_tz.normalize(local_dt.astimezone(utc_tz))
        return dt

    ## Converts a Naive UTC datetime (from DB) to a localized datetime according to the Business timezone

    def utc_to_local(self, naive_utc_dt):
        if naive_utc_dt.tzinfo is not None:
            naive_utc_dt = naive_utc_dt.replace(tzinfo=None)

        if naive_utc_dt == datetime.datetime(1, 1, 1) or naive_utc_dt == datetime.datetime(9999, 12, 31):
            return naive_utc_dt.replace(tzinfo=pytz.timezone(self.site_timezone))

        utc_tz = pytz.utc

        if naive_utc_dt.tzinfo is None:
            utc_dt = utc_tz.localize(naive_utc_dt)
        else:
            utc_dt = naive_utc_dt
        local_tz = pytz.timezone(self.site_timezone).normalize(utc_dt.astimezone(pytz.timezone(self.site_timezone)))
        return local_tz

    def generate_site_code(self):
        size = 10
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace('O', '')
        chars = chars.replace('I', '')
        chars = chars.replace('0', '')
        chars = chars.replace('1', '')

        site_code = ''.join(random.choice(chars) for x in range(size))

        exists = True
        while exists:
            try:
                BCSite.objects.get(site_code=site_code)
            except BCSite.DoesNotExist:
                exists = False
                break
            site_code = ''.join(random.choice(chars) for x in range(size))

        self.site_code = site_code.lower()

    def get_notifications_url(self):
        return "notifications/" + self.site_code + "/"

    def save(self, *args, **kwargs):
        if not self.site_code:
            self.generate_site_code()
        super(BCSite, self).save(*args, **kwargs)


class crmForm(models.Model):
    formId = models.IntegerField("Form ID", null=True)
    formName = models.CharField("Form Name", max_length=1024, null=True)
    bc_site = models.ForeignKey(BCSite, related_name='crmforms')
    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return u"Form Name: %s | Form ID: %s" % (self.formName, self.formId)


class crmFormField(models.Model):
    fieldId = models.IntegerField("Field ID", null=True)
    fieldTypeId = models.IntegerField("Field Type ID", null=True)
    fieldName = models.CharField("Field Name", max_length=1024, null=True)
    crmForm = models.ForeignKey(crmForm, related_name='crmformfields')
    bc_site = models.ForeignKey(BCSite, related_name='crmformfields')

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("%s - FieldID: %s - FormID: %s" % (self.fieldName, self.fieldId, self.crmForm.formId))


class ContactRecord(models.Model):
    entityId = models.IntegerField("BC Entity ID", null=True, default=-1)
    externalId = models.CharField("External Customer ID", max_length=256, null=True, blank=True)
    emailAddress = models.EmailField("Email Address", null=True)
    contactTitle = models.CharField("Title", max_length=256, null=True, blank=True)
    deleted = models.BooleanField("Is Deleted?", default=False)
    fullName = models.CharField("Full Name", max_length=512, null=True, blank=True)
    firstName = models.CharField("First Name", max_length=256, null=True)
    lastName = models.CharField("Last Name", max_length=256, null=True)
    username = models.CharField("Username", max_length=256, null=True, blank=True)
    password = models.CharField("Password", max_length=256, null=True, blank=True)
    dateOfBirth = models.DateTimeField("DOB", null=True, blank=True)
    createDate = models.DateTimeField("Create Date", null=True, blank=True)
    lastUpdateDate = models.DateTimeField("Last Update Date", null=True, blank=True)
    customerType = models.CharField("Customer Type", max_length=256, null=True, blank=True)
    industryType = models.CharField("Industry Type", max_length=256, null=True, blank=True)
    leadSourceType = models.CharField("Lead Source Type", max_length=256, null=True, blank=True)
    ratingType = models.CharField("Rating Type", max_length=256, null=True, blank=True)
    MasterOptIn = models.BooleanField("Master Opt-In", default=True)
    bc_site = models.ForeignKey(BCSite, related_name='contactrecords')

    crmForms = models.ManyToManyField(crmForm, blank=True)

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    def __unicode__(self):
        return u"EntityId: %s - %s %s - on %s" % (
            unicode(self.entityId), unicode(self.firstName), unicode(self.lastName), self.bc_site.site_name)

    class Meta:
        app_label = 'bc_api'

    def get_full_name(self):
        if self.fullName:
            return self.fullName
        return unicode(self.firstName) + " " + unicode(self.lastName)

    def get_phone_number(self):
        try:
            return self.phonenos.filter(phoneNoTypeID=1).last().phoneNo
        except phoneNos.DoesNotExist:
            return None
        except AttributeError:
            return None

    def get_mobile_number(self):
        try:
            return self.phonenos.get(phoneNoTypeID=5).phoneNo
        except phoneNos.DoesNotExist:
            return None

    def get_fax_number(self):
        try:
            return self.phonenos.get(phoneNoTypeID=2).phoneNo
        except:
            return "Not available"

    def get_email_one(self):
        try:
            return self.phonenos.get(phoneNoTypeID=7).phoneNo
        except phoneNos.DoesNotExist:
            return None

    def create_or_update_email_one(self, email):
        try:
            e = self.phonenos.get(phoneNoTypeID=7, phoneNo=email)
            e.phoneNo = email
            e.save()
        except phoneNos.DoesNotExist:
            e = self.phonenos.create(phoneNoTypeID=7, phoneNo=email)
        return e

    def get_email_two(self):
        try:
            return self.phonenos.get(phoneNoTypeID=8).phoneNo
        except:
            return "Not available"

    def get_website(self):
        try:
            return self.phonenos.get(phoneNoTypeID=10).phoneNo
        except:
            return "Not available"

    def get_home_address_object(self):
        try:
            return self.addresses.get(addressTypeID=1)
        except addresses.DoesNotExist:
            return None

    def get_home_address(self):
        try:
            home_address = self.addresses.get(addressTypeID=1)
            return "%s,%s,%s,%s,%s,%s" % (
            home_address.addressLine1, home_address.addressLine2, home_address.city, home_address.state,
            home_address.zipcode, home_address.countryCode)
        except:
            return "Not available"

    def get_billing_address(self):
        try:
            billing_address = self.addresses.get(addressTypeID=8)
            return "%s,%s,%s,%s,%s,%s" % (
            billing_address.addressLine1, billing_address.addressLine2, billing_address.city, billing_address.state,
            billing_address.zipcode, billing_address.countryCode)
        except:
            return "Not available"

    def get_work_address(self):
        try:
            work_address = self.addresses.get(addressTypeID=8)
            return "%s,%s,%s,%s,%s,%s" % (
            work_address.addressLine1, work_address.addressLine2, work_address.city, work_address.state,
            work_address.zipcode, work_address.countryCode)
        except:
            return "Not available"

    def add_to_mailinglist(self, mailing_list_id):
        site = self.bc_site
        url = str(site.secure_site_url + 'catalystwebservice/catalystcrmwebservice.asmx?WSDL')
        client = Client(url)

        # Can't remember why I was writing this but need to finish it here (it was for Suze)

    def delete_from_bc(self):
        site = self.bc_site
        url = str(site.secure_site_url + 'catalystwebservice/catalystcrmwebservice.asmx?WSDL')
        client = Client(url)
        try:
            response = client.service.Contact_DeleteByEntityID(str(site.admin_username),
                                                               str(site.admin_password),
                                                               int(site.site_id),
                                                               self.entityId)
        except Exception as e:
            print e
        else:
            return response

    def create_or_update_to_bc(self):
        site = self.bc_site
        url = str(site.secure_site_url + 'catalystwebservice/catalystcrmwebservice.asmx?WSDL')
        client = Client(url, plugins=[LogPlugin()])

        contact_list = client.factory.create('ArrayOfContactRecord')
        contact = client.factory.create('ContactRecord')

        contact.entityId = self.entityId
        contact.externalId = self.externalId
        contact.emailAddress = self.emailAddress
        contact.fullName = self.fullName
        contact.firstName = self.firstName
        contact.lastName = self.lastName
        contact.dateOfBirth = self.dateOfBirth
        contact.createDate = self.createDate
        contact.lastUpdateDate = self.lastUpdateDate
        contact.MasterOptIn = self.MasterOptIn
        contact.deleted = self.deleted

        # Moniques 4 fields go here
        contact.industryType = self.industryType
        contact.leadSourceType = self.leadSourceType
        contact.ratingType = self.ratingType
        contact.customerType = self.customerType

        phoneno_array = self.create_phoneno_array(client)
        if phoneno_array is not None:
            contact.phoneNos = phoneno_array

        address_array = self.create_address_array(client)
        if address_array is not None:
            contact.addresses = address_array

        custom_crm_form_array = self.create_custom_crm_form_array(client)
        if custom_crm_form_array is not None:
            contact.crmForms = custom_crm_form_array

        contact_list.ContactRecord.append(contact)
        try:
            response = client.service.ContactList_UpdateInsert(str(site.admin_username),
                                                               str(site.admin_password),
                                                               int(site.site_id),
                                                               contact_list)
        except Exception as e:
            return e
        else:
            pass

        if self.entityId == -1:
            try:
                response = client.service.Contact_RetrieveByEmailAddress(str(self.bc_site.admin_username),
                                                                         str(self.bc_site.admin_password),
                                                                         int(self.bc_site.site_id),
                                                                         str(self.emailAddress))
            except Exception as e:
                pass
            else:
                self.entityId = response.entityId
                self.save()
        return None

    def create_phoneno_array(self, client):
        phone_no_list = client.factory.create('ArrayOfPhoneNo')
        empty = True

        for db_phone_no in self.phonenos.all():
            phone_no_list.PhoneNo.append(db_phone_no.createPhoneNoObject(client))
            empty = False

        if empty:
            return None
        else:
            return phone_no_list

    def create_address_array(self, client):

        address_list = client.factory.create('ArrayOfAddress')

        for a in self.addresses.all():
            address = a.createAddressObject(client)
            if address is None:
                continue
            else:
                address_list.Address.append(address)

        return address_list

    def create_custom_crm_form_array(self, client):
        crmform_list = client.factory.create('ArrayOfCrmForms')

        # Get List of CRM forms attached to this Order
        for form in self.crmForms.all():
            # Create a CRM Form Object
            crm_form_object = client.factory.create('CrmForms')
            crm_form_object.formId = form.formId
            crm_form_object.formName = form.formName

            # Create Array of CRM Form Fields
            crmformfield_list = client.factory.create('ArrayOfCrmFormFields')

            # Now go through fields and find field values
            for crmField in form.crmformfields.all():
                crm_form_field_object = client.factory.create('CrmFormFields')
                crm_form_field_object.fieldId = crmField.fieldId
                crm_form_field_object.fieldTypeId = crmField.fieldTypeId
                crm_form_field_object.fieldName = crmField.fieldName

                # Get Field Value associated with this order
                try:
                    fieldValue = crmFormFieldValue.objects.get(crmFormField=crmField, contactRecord=self)
                except crmFormFieldValue.DoesNotExist:
                    crm_form_field_object.fieldValue = None
                else:
                    crm_form_field_object.fieldValue = fieldValue.fieldValue

                crmformfield_list.CrmFormFields.append(crm_form_field_object)

            crm_form_object.crmFormFields = crmformfield_list
            crmform_list.CrmForms.append(crm_form_object)
        return crmform_list

    def unsubscribe_from_list(self, list_id, list_name):
        url = str(self.bc_site.secure_site_url + 'catalystwebservice/catalystcrmwebservice.asmx?WSDL')
        client = Client(url)
        szlist = client.factory.create('ArrayOfSecureZone')
        secure_zone = client.factory.create('SecureZone')
        secure_zone.secureZoneID = int(list_id)
        secure_zone.secureZoneName = list_name
        secure_zone.secureZoneExpiryDate = datetime.datetime.today()
        secure_zone.secureZoneUnsubscribe = True
        szlist.SecureZone.append(secure_zone)
        try:
            response = client.service.Contact_SecureZoneListUpdateInsert(str(self.bc_site.admin_username),
                                                                         str(self.bc_site.admin_password),
                                                                         int(self.bc_site.site_id),
                                                                         self.phonenos.get(phoneNoTypeID=7).phoneNo,
                                                                         szlist)
        except WebFault, e:
            return


class ContactRecordNotes(models.Model):
    note = models.TextField("Note")
    created = models.DateTimeField("Created", auto_now_add=True)
    contactRecord = models.ForeignKey(ContactRecord, related_name="notes")

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u"%s | %s" % (self.note, self.contactRecord)


class phoneNos(models.Model):
    phoneNoTypeID = models.IntegerField("Contact Type", choices=PHONENOS_TYPES, default=7)
    phoneNo = models.CharField("Phone Number/Email Address", max_length=1024, null=True)
    contactRecord = models.ForeignKey(ContactRecord, related_name='phonenos')

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'
        ordering = ['phoneNoTypeID']

    def __unicode__(self):
        return "%s | %s | %s" % (self.contactRecord, self.phoneNoTypeID, self.phoneNo)

    def createPhoneNoObject(self, client):
        phone_no = client.factory.create('PhoneNo')
        phone_no.phoneNoTypeID = self.phoneNoTypeID
        phone_no.phoneNo = self.phoneNo
        return phone_no


class Case(models.Model):
    entityId = models.IntegerField("BC Entity ID", null=True, default=-1)
    caseId = models.IntegerField("Case ID", null=True, default=-1)
    assignedTo = models.IntegerField("The user this case is assigned to", default=0)  # Bc returns 0 for unassigned case
    caseSubject = models.CharField("Case Subject (Also a web form name)", max_length=1024, null=True)
    createDate = models.DateTimeField("Case Create Date", null=True, blank=True)
    lastUpdateDate = models.DateTimeField("Case Last Update Date", null=True)
    contactRecord = models.ForeignKey(ContactRecord, related_name='cases', null=True)
    bc_site = models.ForeignKey(BCSite, related_name='cases')
    objectTypeId = models.IntegerField("BC Object Type ID for Cases", default=1001)
    synced = models.DateTimeField("Date Item Synced", null=True, blank=True)
    workflow_sent = models.DateTimeField("Date Workflow Sent", null=True, blank=True)
    status = models.IntegerField("Case Status", choices=CASE_STATUS, default=NEW, blank=True)
    deleted = models.BooleanField("Deleted?", default=False, blank=True)
    prospectus_sent_date = models.DateTimeField("Prospectus Sent Date", null=True, blank=True)

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    crmForms = models.ManyToManyField(crmForm)

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return u"CaseId: %s - EntityId: %s - Subject: %s" % (
            unicode(self.caseId), unicode(self.entityId), unicode(self.caseSubject))

    def get_form_field_value(self, field_id):
        try:
            form_field = self.bc_site.crmformfields.get(fieldId=field_id)
        except crmFormField.DoesNotExist:
            return ''

        try:
            form_field_value = self.crmformfieldvalues.get(crmFormField=form_field)
        except crmFormFieldValue.DoesNotExist:
            return ''

        if not form_field_value.fieldValue:
            return ''
        else:
            clean_field_value = re.sub('&.+;', '', form_field_value.fieldValue)
            fixer = dict.fromkeys([0x201c, 0x201d], u'"')
            return clean_field_value.translate(fixer).encode("ascii", "replace")

    def get_subject(self):
        return self.caseSubject


class Order(models.Model):
    entityId = models.IntegerField("BC Entity ID", null=True, default=-1)
    orderId = models.IntegerField("Order ID", null=True, default=-1)
    orderName = models.CharField("Order Name", max_length=1024, blank=True, null=True)
    workflowId = models.IntegerField("Workflow ID", null=True, default=-1)
    statusTypeId = models.IntegerField("Status Type ID", null=True, default=-1)
    countryCode = models.CharField("Country Code", max_length=10, blank=True, null=True)
    orderType = models.IntegerField("Order Type", null=True, default=-1)
    invoiceNumber = models.IntegerField("Invoice Number", null=True, default=-1)
    invoiceDate = models.DateTimeField("Invoice Date", null=True)
    userID_AssignedTo = models.IntegerField("User ID assigned To", null=True, default=-1)
    shippingAmount = models.DecimalField("Shipping Amount", max_digits=15, decimal_places=2, null=True)
    shippingTaxRate = models.DecimalField("Shipping Tax Rate", max_digits=15, decimal_places=2, null=True)
    shippingAttention = models.CharField("Shipping Attention", max_length=1024, blank=True, null=True)
    shippingInstructions = models.CharField("Shipping Instructions", max_length=1024, blank=True, null=True)
    shippingOptionId = models.IntegerField("Shipping Option ID", null=True, default=-1)
    discountCodeId = models.IntegerField("Discount Code ID", null=True, default=-1)
    discountRate = models.DecimalField("Discount Rate", max_digits=15, decimal_places=2, null=True)
    totalOrderAmount = models.DecimalField("Total Order Amount", max_digits=15, decimal_places=2, null=True)
    directDebitTypeId = models.IntegerField("Direct Debit Type ID", null=True, default=-1)
    directDebitDays = models.IntegerField("Direct Debit Days", null=True, default=0)
    isRecur = models.BooleanField("Is Recurring?", default=False)
    nextInvoiceDate = models.DateTimeField("Next Invoice Date", null=True)
    endRecurDate = models.DateTimeField("End Recur Date", null=True, blank=True)
    cycleTypeID = models.IntegerField("Cycle Type ID", null=True, default=-1)
    createDate = models.DateTimeField("BC Order Create Date", null=True)
    lastUpdateDate = models.DateTimeField("BC Order Last Update Date", null=True)
    deleted = models.BooleanField("Deleted", default=False)

    crmForms = models.ManyToManyField(crmForm, blank=True)
    contactRecord = models.ForeignKey(ContactRecord, related_name='orders', null=True)
    bc_site = models.ForeignKey(BCSite, related_name='orders')
    objectTypeId = models.IntegerField("BC Object Type ID for Orders", default=1002)

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return u"OrderId: %s - EntityId: %s - Amount: %s" % (
            unicode(self.orderId), unicode(self.entityId), unicode(self.totalOrderAmount))

    def calc_shipping_tax(self):
        return '%0.2f' % float(self.shippingAmount * self.shippingTaxRate)

    def calc_total_tax(self):
        tax = float(0)
        for p in self.products.all():
            tax += (float(p.unitTaxRate * p.unitPrice) / 100) * p.units
        tax_string = '%0.2f' % tax
        return tax_string

    def calc_total_tax_as_decimal(self):
        tax = float(0)
        for p in self.products.all():
            tax += (float(p.unitTaxRate * p.unitPrice) / 100) * p.units
        return Decimal(tax)

    def updateOrderToBC(self, add_payments=False):
        site = self.bc_site
        url = str(site.secure_site_url + 'catalystwebservice/catalystcrmwebservice.asmx?WSDL')
        client = Client(url)

        orderDetails = client.factory.create('OrderDetails')

        orderDetails.entityId = self.entityId
        orderDetails.orderId = self.orderId
        orderDetails.orderName = self.orderName
        orderDetails.workflowId = self.workflowId
        orderDetails.statusTypeId = self.statusTypeId
        orderDetails.countryCode = self.countryCode
        orderDetails.orderType = self.orderType
        orderDetails.invoiceNumber = self.invoiceNumber
        orderDetails.invoiceDate = self.bc_site.utc_to_local(self.invoiceDate).replace(tzinfo=None)
        orderDetails.userID_AssignedTo = self.userID_AssignedTo
        orderDetails.shippingAmount = self.shippingAmount
        orderDetails.shippingTaxRate = self.shippingTaxRate
        orderDetails.shippingAttention = self.shippingAttention
        orderDetails.shippingInstructions = self.shippingInstructions
        orderDetails.shippingOptionId = self.shippingOptionId
        orderDetails.discountCodeId = self.discountCodeId
        orderDetails.discountRate = self.discountRate
        orderDetails.totalOrderAmount = self.totalOrderAmount
        orderDetails.directDebitTypeId = self.directDebitTypeId
        orderDetails.directDebitDays = self.directDebitDays
        orderDetails.isRecur = self.isRecur
        if self.nextInvoiceDate is not None:
            orderDetails.nextInvoiceDate = self.bc_site.utc_to_local(self.nextInvoiceDate).replace(tzinfo=None)
        else:
            orderDetails.nextInvoiceDate = datetime.datetime(1, 1, 1)

        if self.isRecur:
            orderDetails.endRecurDate = datetime.datetime(9999, 12, 31)
        else:
            orderDetails.endRecurDate = datetime.datetime(1, 1, 1)

        orderDetails.cycleTypeID = self.cycleTypeID

        orderDetails.createDate = self.bc_site.utc_to_local(self.createDate).replace(tzinfo=None)
        orderDetails.lastUpdateDate = self.bc_site.utc_to_local(self.lastUpdateDate).replace(tzinfo=None)
        orderDetails.deleted = self.deleted

        orderDetails.products = self.createProductArray(client)
        # Do not need to update Payments because BC just appends them

        if add_payments:
            orderDetails.payments = self.createPaymentArray(client)

        orderDetails.addresses = self.createAddressesArray(client)
        orderDetails.crmForms = self.createCRMFormsArray(client, self)
        try:
            response = client.service.Order_CreateUpdate(str(site.admin_username), str(site.admin_password),
                                                         int(site.site_id), orderDetails)
        except Exception, e:
            raise e
        return response

    def createProductArray(self, client):
        product_list = client.factory.create('ArrayOfProduct')

        for p in self.products.all():
            product_list.Product.append(p.createProductObject(client))

        return product_list

    def createPaymentArray(self, client):
        payment_list = client.factory.create('ArrayOfPayment')

        for p in self.payments.all():
            payment_list.Payment.append(p.createPaymentObject(client))

        return payment_list

    def createAddressesArray(self, client):
        address_list = client.factory.create('ArrayOfAddress')

        for a in self.addresses.all():
            address = a.createAddressObject(client)
            if address is None:
                continue
            else:
                address_list.Address.append(address)

        return address_list

    def createCRMFormsArray(self, client, order):
        crmform_list = client.factory.create('ArrayOfCrmForms')

        # Get List of CRM forms attached to this Order
        for form in self.crmForms.all():
            # Create a CRM Form Object
            crm_form_object = client.factory.create('CrmForms')
            crm_form_object.formId = form.formId
            crm_form_object.formName = form.formName

            # Create Array of CRM Form Fields
            crmformfield_list = client.factory.create('ArrayOfCrmFormFields')

            # Now go through fields and find field values
            for crmField in form.crmformfields.all():
                crm_form_field_object = client.factory.create('CrmFormFields')
                crm_form_field_object.fieldId = crmField.fieldId
                crm_form_field_object.fieldTypeId = crmField.fieldTypeId
                crm_form_field_object.fieldName = crmField.fieldName

                # Get Field Value associated with this order
                try:
                    fieldValue = crmFormFieldValue.objects.get(crmFormField=crmField, order=order)
                except crmFormFieldValue.DoesNotExist:
                    crm_form_field_object.fieldValue = None
                else:
                    crm_form_field_object.fieldValue = fieldValue.fieldValue

                crmformfield_list.CrmFormFields.append(crm_form_field_object)

            crm_form_object.crmFormFields = crmformfield_list
            crmform_list.CrmForms.append(crm_form_object)
        return crmform_list

    def checksum(self):
        total = float(0)
        for p in self.products.all():
            total += float(p.totalProductPrice)

        total += float(self.shippingAmount)
        total -= float(self.discountRate)
        if abs(total - float(self.totalOrderAmount)) > 1:
            print 'Order ID: %s' % self.orderId
            print 'Calculated Total %s' % total
            print 'Stored Total %s' % self.totalOrderAmount
            return False
        else:
            return True

    ### Calculation Functions Required for VendPos (could be useful for other stuff in the future)

    def get_total_product_price(self):
        total_product_price = Decimal(0)
        for p in self.products.all():
            total_product_price += p.unitPrice * p.units

        return total_product_price

    def get_total_product_tax(self):
        total_product_tax = Decimal(0)
        for p in self.products.all():
            total_product_tax += p.unitTaxRate / 100 * p.unitPrice * p.units
        return total_product_tax

    def get_total_payment(self):
        total_payment = Decimal(0)
        for p in self.payments.all():
            total_payment += p.amount
        return total_payment

    def amount_paid_with_gift_voucher(self):
        gift_voucher_amount = Decimal(0.00)
        for p in self.payments.all():
            if p.paymentMethodTypeID == GIFT_VOUCHER_PAYMENT_TYPE_ID:
                gift_voucher_amount += p.amount

        return gift_voucher_amount


class OrderProduct(models.Model):
    """
    Assume that each order has it's own set of products which are only loosely related to the actual products in the
    Ecommerce Database (by productId)
    """
    productId = models.IntegerField("Product ID", null=True, default=-1)
    productCode = models.CharField("Product Code", max_length=1024, blank=True, null=True)
    productDescription = models.CharField("Product Description", max_length=1024, blank=True, null=True)
    units = models.IntegerField("Units", null=True, default=1)
    unitPrice = models.DecimalField("Unit Price", max_digits=15, decimal_places=2, null=True)
    unitTaxRate = models.DecimalField("Unit Tax Rate", max_digits=15, decimal_places=2, null=True)
    totalProductPrice = models.DecimalField("Total Product Price", max_digits=15, decimal_places=2, null=True)
    productName = models.CharField("Product Name", max_length=1024, blank=True, null=True)
    variationId = models.IntegerField("variationId", null=True, default=0)

    order = models.ForeignKey(Order, related_name='products')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return u"OrderId: %s | Product Name: %s | Product Description: %s | Unit Price: %s | Units: %s | Sub Total: %s" % (
            self.order.orderId, self.productName, self.productDescription, self.unitPrice, self.units,
            self.totalProductPrice)

    def calc_unit_tax(self):
        return '%0.2f' % (float(self.unitTaxRate * self.unitPrice) / 100)

    def createProductObject(self, client):
        orderProduct = client.factory.create('Product')
        orderProduct.productId = self.productId
        orderProduct.productCode = self.productCode
        orderProduct.productDescription = self.productDescription
        orderProduct.units = self.units
        orderProduct.unitPrice = self.unitPrice
        orderProduct.unitTaxRate = self.unitTaxRate
        orderProduct.totalProductPrice = self.totalProductPrice
        orderProduct.variationId = self.variationId

        return orderProduct


class OrderPayment(models.Model):
    """
    Each order can have it's own set of payments
    """
    paymentMethodTypeID = models.IntegerField("PaymentMethod Type ID", null=True, default=-1)
    amount = models.DecimalField("Amount", max_digits=15, decimal_places=2, null=True)
    paymentStatusID = models.IntegerField("Payment Status ID", null=True, default=-1)
    transactionNumber = models.CharField("Transaction Number", max_length=1024, blank=True, null=True)
    transactionAuthCode = models.CharField("Transaction Auth Code", max_length=1024, blank=True, null=True)
    Description = models.CharField("Description", max_length=1024, blank=True, null=True)
    paymentDate = models.DateTimeField("Payment Date", null=True)

    order = models.ForeignKey(Order, related_name='payments')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return u"OrderId: %s | Payment Amount: %s | Payment Date : %s" % (
            self.order.orderId, self.amount, self.paymentDate)

    def createPaymentObject(self, client):
        orderPayment = client.factory.create('Payment')
        orderPayment.paymentMethodTypeID = self.paymentMethodTypeID
        orderPayment.amount = self.amount
        orderPayment.paymentStatusID = self.paymentStatusID
        orderPayment.transactionNumber = self.transactionNumber
        orderPayment.transactionAuthCode = self.transactionAuthCode
        orderPayment.Description = self.Description
        orderPayment.paymentDate = self.paymentDate

        return orderPayment


class messageThreads(models.Model):
    message = models.TextField("Message", null=True)
    createDate = models.DateTimeField("Message Create Date", null=True)
    objectId = models.IntegerField("To whom the case is assigned to", null=True)
    objectType = models.IntegerField("Object Type", default=14)
    isInternal = models.BooleanField("Is Internal?", default=False)
    entityId = models.IntegerField("Entity Id", null=True)
    case = models.ForeignKey(Case, null=True, related_name='messagethreads')

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'


class crmFormFieldValue(models.Model):
    fieldValue = models.CharField("Field Value", max_length=4096, null=True, blank=True)
    crmFormField = models.ForeignKey(crmFormField, related_name='crmformfieldvalues')
    case = models.ForeignKey(Case, related_name='crmformfieldvalues', null=True)
    order = models.ForeignKey(Order, related_name='crmformfieldvalues', null=True, blank=True)
    contactRecord = models.ForeignKey(ContactRecord, related_name='crmformfieldvalues', null=True, blank=True)
    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'
        ordering = ['crmFormField__fieldName']

    def __unicode__(self):
        return unicode(self.fieldValue)


class fileList(models.Model):
    fileId = models.IntegerField("File ID", null=True)
    fileName = models.CharField("File Name", max_length=1024, null=True)
    fileSize = models.FloatField("File Size", null=True)
    case = models.ForeignKey(Case, null=True, related_name='filelists')

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Filename: %s for %s" % (self.fileName, self.case))


class addresses(models.Model):
    addressTypeID = models.IntegerField("Address Type", choices=ADDRESS_TYPES, default=1)
    addressLine1 = models.CharField("Address Line 1", max_length=1024, null=True, blank=True)
    addressLine2 = models.CharField("Address Line 2", max_length=1024, null=True, blank=True)
    city = models.CharField("City", max_length=1024, null=True, blank=True)
    zipcode = models.CharField("Zipcode/Postcode", max_length=1024, null=True, blank=True)
    state = models.CharField("State", max_length=1024, null=True, blank=True)
    countryCode = models.CharField("Country", max_length=2, null=True, blank=True, choices=COUNTRIES_CHOICES)
    contactRecord = models.ForeignKey(ContactRecord, related_name='addresses', null=True, blank=True)
    order = models.ForeignKey(Order, related_name='addresses', null=True, blank=True)

    api_db_creation_date = models.DateTimeField("Date Created in API Database", auto_now_add=True)
    api_db_modified_date = models.DateTimeField("Date Last Modified in API Database", auto_now=True)

    class Meta:
        app_label = 'bc_api'

    def createAddressObject(self, client):
        if not (self.addressLine1 and self.city and self.zipcode and self.state and self.countryCode):
            return None

        addressObject = client.factory.create("Address")
        addressObject.addressTypeID = self.addressTypeID
        addressObject.addressLine1 = self.addressLine1
        if addressObject.addressLine2 is not None and addressObject.addressLine2 != '':
            addressObject.addressLine2 = self.addressLine2
        else:
            addressObject.addressLine2 = ''
        addressObject.city = self.city
        addressObject.zipcode = self.zipcode
        addressObject.state = self.state
        addressObject.countryCode = self.countryCode

        return addressObject

    def get_addressline1(self):
        return self.addressLine1

    def get_addressline2(self):
        return self.addressLine2

    def get_city(self):
        return self.city

    def get_zipcode(self):
        return self.zipcode

    def get_state(self):
        return self.state

    def get_country(self):
        return self.countryCode


class OrderStatus(models.Model):
    status_id = models.IntegerField("Order Status ID")
    status_description = models.CharField("Order Status Description", max_length=300)
    bc_site = models.ForeignKey(BCSite, related_name="order_status_bcsite")

    class Meta:
        app_label = "bc_api"

    def __unicode__(self):
        return unicode("ID: %s Description: %s Site: %s" % (self.status_id, self.status_description, self.bc_site))


class MarketingList(models.Model):
    name = models.CharField("List Name", max_length=200)
    list_id = models.IntegerField("List ID in BC")
    bc_site = models.ForeignKey(BCSite, related_name="marketing_list_site")

    class Meta:
        app_label = "bc_api"

    def __unicode__(self):
        return unicode("%s - %s" % (self.name, self.list_id))


class WorkflowTemplates(models.Model):
    name = models.CharField("Name e.g. case_templates", max_length=100)
    workflow_html_template = models.TextField("Case workflow HTML template", blank=True)
    workflow_text_template = models.TextField("Case workflow text template", blank=True)
