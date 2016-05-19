import datetime
import pytz
from suds import WebFault
from suds.client import Client
from bc_api.models.crm import ContactRecord, phoneNos, addresses, crmForm, crmFormField, crmFormFieldValue, Case, \
    messageThreads, fileList, Order, OrderProduct, OrderPayment, MarketingList

import logging
logger = logging.getLogger('raven')


class CrmWrapper(object):
    """
    Excepts our BC site object as a parameter and uses its arguments to talk to BC

    Example:

    from bc_api.models import BCSite
    site = BCSite.objects.get(id=1)
    bc_wrap = BcWrapper(site)
    result = bc_wrap.contact_retrieve_by_entity_id(entity_id) #where entity_id is a BC CRM ID

    """

    def __init__(self, site):
        self.site = site
        url = str(self.site.secure_site_url + 'catalystwebservice/catalystcrmwebservice.asmx?WSDL')
        self.client = Client(url)

    def caselist_retrieve(self, utcLastUpdateDate, recordStart=0):
        """
        Retrieves all cases that have been modified or added since the given datetime
        """
        localLastUpdateDate = self.site.utc_to_local(utcLastUpdateDate)

        try:
            response = self.client.service.CaseList_Retrieve(
                str(self.site.admin_username),
                str(self.site.admin_password), int(self.site.site_id),
                localLastUpdateDate,
                recordStart,
                False
            )
        except WebFault, e:
            logger.debug("Error Retrieving Case List", exc_info=True, extra={'stack':True})
            return
        if response is None:
            return
        # Now iterate through - see if we can share code with Case Retrieve and Order Retrieve
        new_cases, updated_cases = [], []
        if hasattr(response, "CaseList_RetrieveResult"):
            cases = self.client.dict(response["CaseList_RetrieveResult"])
            for incoming_case in cases['CaseDetails']:
                if incoming_case.entityId == -1:
                    continue
                contact = self.contact_retrieve_by_entity_id(incoming_case.entityId)
                try:
                    db_case = Case.objects.get(caseId=incoming_case.caseId, bc_site=self.site)
                except Case.DoesNotExist:
                    self.save_case(incoming_case, contact, 2001)
                else:
                    # check the last update date against the one we have in DB
                    if db_case.lastUpdateDate < self.site.local_to_utc(incoming_case.lastUpdateDate):
                        self.save_case(incoming_case, contact, 2001)

        while response.moreRecords:
            recordStart += 100
            response = self.client.service.OrderList_Retrieve(
                str(self.site.admin_username),
                str(self.site.admin_password),
                int(self.site.site_id),
                localLastUpdateDate, recordStart, False
            )
            cases = self.client.dict(response["CaseList_RetrieveResult"])
            for incoming_case in cases['CaseDetails']:
                if incoming_case.entityId == -1:
                    continue
                contact = self.contact_retrieve_by_entity_id(incoming_case.entityId)
                try:
                    db_case = Case.objects.get(caseId=incoming_case.caseId, bc_site=self.site)
                except Case.DoesNotExist:
                    self.save_case(incoming_case, contact, 2001)
                else:
                    # check the last update date against the one we have in DB
                    if db_case.lastUpdateDate < self.site.local_to_utc(incoming_case.lastUpdateDate):
                        self.save_case(incoming_case, contact, 2001)

    def contact_retrieve_by_entity_id(self, entity_id):

        """
        Takes  BC entity ID, stores the contact in DB  and returns either
        """

        try:
            response = self.client.service.Contact_RetrieveByEntityID(str(self.site.admin_username),
                                                                      str(self.site.admin_password),
                                                                      int(self.site.site_id), int(entity_id))
        except WebFault as e:
        #### You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the contact
        #### result.message in this case will give you something like the following message:
        #### u"Server raised fault: 'Server was unable to process request. ---> ERROR: Contact record could not be retrieved.'"
            logger.debug("Error Retrieving BC Contact (ID: %s) for site with ID %s" % (entity_id, self.site.site_id), exc_info=True, extra={'stack':True})
            return None

        # Try retrieving the customer and update their details or create a new customer
        try:
            bc_contact = ContactRecord.objects.get(entityId=int(response.entityId), bc_site=self.site)
        except ContactRecord.DoesNotExist:
            bc_contact = ContactRecord()

        bc_contact.entityId = response.entityId
        if hasattr(response, "contactTitle"):
            bc_contact.contactTitle = response.contactTitle
        bc_contact.deleted = response.deleted
        bc_contact.fullName = unicode(response.fullName).encode('utf-8').strip()
        bc_contact.firstName = unicode(response.firstName).encode('utf-8').strip()
        bc_contact.lastName = unicode(response.lastName).encode('utf-8').strip()
        if hasattr(response, "username"):
            bc_contact.username = response.username
        if response.dateOfBirth != datetime.datetime(1, 1, 1, 0, 0):
            bc_contact.dateOfBirth = self.site.local_to_utc(response.dateOfBirth)
        if hasattr(response, "customerType"):
            bc_contact.customerType = response.customerType
        if hasattr(response, "industryType"):
            bc_contact.industryType = response.industryType
        if hasattr(response, "leadSourceType"):
            bc_contact.leadSourceType = response.leadSourceType
        if hasattr(response, "ratingType"):
            bc_contact.ratingType = response.ratingType
        bc_contact.MasterOptIn = response.MasterOptIn
        bc_contact.bc_site = self.site
        bc_contact.externalId = response.externalId if hasattr(response, 'externalId') and response.externalId is not None else ''
        bc_contact.save()

        #bc_contact.externalId = bc_contact.id
        bc_contact.save()

        #Save the phone number and email address against the customer record
        if hasattr(response, "phoneNos"):
            phone_numbers = self.client.dict(response["phoneNos"])
            for ph_no in phone_numbers["PhoneNo"]:
                try:
                    phone_nos = phoneNos.objects.get(phoneNoTypeID=ph_no.phoneNoTypeID,
                                                     contactRecord=bc_contact)
                except phoneNos.DoesNotExist:
                    phone_nos = phoneNos()

                phone_nos.phoneNoTypeID = ph_no.phoneNoTypeID
                phone_nos.phoneNo = ph_no.phoneNo
                phone_nos.contactRecord = bc_contact
                phone_nos.save()

        #Save address details from contact record
        if hasattr(response, "addresses"):
            customer_addresses = self.client.dict(response["addresses"])
            for a in customer_addresses['Address']:
                self.save_address(a, order=None, contactRecord=bc_contact)

        # Save CRM Forms and fields
        if hasattr(response, "crmForms"):
            crm_forms = self.client.dict(response["crmForms"])
            for form in crm_forms["CrmForms"]:
                self.save_crmForm(form_response=form, order=None, case=None, contactRecord=bc_contact)
        return bc_contact


    def case_retrieve(self, case_id, bc_object_type_id):

        """

        Takes  BC's case ID, and stores it against the existing contact. If the contact does not exist then it
        will use the entity Id from case details to pull int the contact and save the contact, then attach a case to it

        Usage example:
        # >>> from bc_api.tasks import *
        # >>> from bc_api.models import BCSite
        # >>> site = BCSite.objects.get(id=2)
        # >>> bc_wrap = BcWrapper(site)
        # >>> result = bc_wrap.case_retrieve(4043920)

        """

        try:
            response = self.client.service.Case_Retrieve(str(self.site.admin_username), str(self.site.admin_password),
                                                         int(self.site.site_id), int(case_id))
        except WebFault, e:
            #### You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the contact
            #### result.message in this case will give you something like the following message:
            #### u"Server raised fault: 'Server was unable to process request. ---> ERROR: Case details for the given caseId could not be found.'"
            logger.debug("Error retrieving BC Case (ID: %s) for site with ID %s" % (case_id, self.site.site_id), exc_info=True, extra={'stack':True})
            return None

        if response is None:
            return None

        # Check if the entity id returned inside the case exists in our DB and if not pull it from BC
        contact = self.contact_retrieve_by_entity_id(int(response.entityId))
        return self.save_case(response, contact, bc_object_type_id)



    def save_case(self, response, contact, bc_object_type_id):
        try:
            case = Case.objects.get(caseId=response.caseId, contactRecord=contact, bc_site=self.site)
        except Case.DoesNotExist:
            case = Case()
            case.caseId = response.caseId
            case.contactRecord = contact
            if contact is None:
                case.bc_site = self.site
            else:
                case.bc_site = contact.bc_site

        case.caseId = response.caseId
        case.entityId = response.entityId
        case.assignedTo = response.assignedTo
        case.caseSubject = response.caseSubject
        case.createDate = self.site.local_to_utc(response.createDate)
        case.lastUpdateDate = self.site.local_to_utc(response.lastUpdateDate)
        case.contactRecord = contact
        case.bc_site = self.site
        case.objectTypeId = bc_object_type_id
        case.save()

        # Save CRM Forms and fields
        if hasattr(response, "crmForms"):
            crm_forms = self.client.dict(response["crmForms"])
            for form in crm_forms["CrmForms"]:
                self.save_crmForm(form, order=None, case=case, contactRecord=None)

        # Save case message threads
        if hasattr(response, "messageThreads"):
            messages = self.client.dict(response["messageThreads"])
            for m in messages['MessageThreads']:
                try:
                    message = messageThreads.objects.get(createDate=m.createDate, entityId=m.entityId, case=case)
                except messageThreads.DoesNotExist:
                    message = messageThreads()
                message.message = m.message
                message.createDate = self.site.local_to_utc(m.createDate)
                message.objectId = m.objectId
                message.objectType = m.objectType
                message.isInternal = m.isInternal
                message.entityId = m.entityId
                message.case = case
                message.save()

        # Save file information

        if hasattr(response, "fileList"):
            files = self.client.dict(response["fileList"])
            for f in files['Files']:
                try:
                    myfile = fileList.objects.get(fileId=f.fileId, case=case)
                except fileList.DoesNotExist:
                    myfile = fileList()
                myfile.fileId = f.fileId
                myfile.fileName = f.fileName
                myfile.fileSize = f.fileSize
                myfile.case = case
                myfile.save()
        return case




    def order_retrieve(self, order_id, bc_object_type_id):
        """
        Takes  BC's Order ID, and stores it against the existing contact. If the contact does not exist then it
        will use the entity Id from case details to pull int the contact and save the contact, then attach a case to it

        Usage example:
        # >>> from bc_api.tasks import *
        # >>> from bc_api.models import BCSite
        # >>> site = BCSite.objects.get(id=2)
        # >>> bc_wrap = BcWrapper(site)
        # >>> result = bc_wrap.order_retrieve(4043920)
        """
        try:
            response = self.client.service.Order_Retrieve(str(self.site.admin_username), str(self.site.admin_password),
                                                          int(self.site.site_id), int(order_id))
        except WebFault as e:
            #You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the contact
            #result.message in this case will give you something like the following message:
            #u"Server raised fault: 'Server was unable to process request. ---> ERROR: Case details for the given caseId
            #could not be found.'"
            logger.debug("Error retrieving BC Order (ID: %s) for site with ID %s" % (order_id, self.site.site_id), extra={'stack':True})
            return None

        if response is None:
            return None

        contact = self.contact_retrieve_by_entity_id(entity_id=int(response.entityId))
        return self.save_order(response, contact, bc_object_type_id)

    def save_order(self, order_response, contact, bc_object_type_id):
        try:
            order = Order.objects.get(orderId=order_response.orderId, contactRecord=contact, bc_site=self.site)
        except Order.DoesNotExist:
            order = Order()
            order.orderId = order_response.orderId
            order.contactRecord = contact
            if contact is None:
                order.bc_site = self.site
            else:
                order.bc_site = contact.bc_site

        order.entityId = order_response.entityId
        order.orderName = order_response.orderName
        if hasattr(order_response, 'workflowId'):
            order.workflowId = order_response.workflowId
        order.statusTypeId = order_response.statusTypeId
        order.countryCode = order_response.countryCode
        order.orderType = order_response.orderType
        order.invoiceNumber = order_response.invoiceNumber
        order.invoiceDate = self.site.local_to_utc(order_response.invoiceDate)
        order.userID_AssignedTo = order_response.userID_AssignedTo
        order.shippingAmount = order_response.shippingAmount
        order.shippingTaxRate = order_response.shippingTaxRate
        if order_response.shippingAttention is not None:
            order.shippingAttention = order_response.shippingAttention
        else:
            order.shippingAttention = ''
        order.shippingInstructions = order_response.shippingInstructions
        order.shippingOptionId = order_response.shippingOptionId
        order.discountCodeId = order_response.discountCodeId
        order.discountRate = order_response.discountRate
        order.totalOrderAmount = order_response.totalOrderAmount
        order.directDebitTypeId = order_response.directDebitTypeId
        order.isRecur = order_response.isRecur

        try:
            order.nextInvoiceDate = self.site.local_to_utc(order_response.nextInvoiceDate)
        except OverflowError:
            order.nextInvoiceDate = datetime.datetime(1, 1, 1).replace(tzinfo=pytz.UTC)

        try:
            order.endRecurDate = self.site.local_to_utc(order_response.endRecurDate)
        except OverflowError:
            order.endRecurDate = datetime.datetime(9999,12,31).replace(tzinfo=pytz.UTC)
        order.cycleTypeID = order_response.cycleTypeID

        order.createDate = self.site.local_to_utc(order_response.createDate)
        order.lastUpdateDate = self.site.local_to_utc(order_response.lastUpdateDate)

        order.deleted = order_response.deleted
        order.objectTypeId = bc_object_type_id
        order.save()

        # Process Products

        if hasattr(order_response, "products"):
            # Delete all existing products
            for p in order.products.all():
                p.delete()
            products = self.client.dict(order_response["products"])
            try:
                for product in products["Product"]: ### Check this
                    self.save_product(product, order)
            except KeyError:
                pass


        # Process Payments
        if hasattr(order_response, "payments"):
            for p in order.payments.all():
                p.delete()
            payments = self.client.dict(order_response["payments"])
            for payment in payments["Payment"]:
                self.save_payment(payment, order)

        # Process Addresses
        if hasattr(order_response, "addresses"):
            order_addresses = self.client.dict(order_response["addresses"])
            for order_address in order_addresses["Address"]:
                self.save_address(address_response=order_address, order=order, contactRecord=None)

        # Save CRM Forms and fields
        if hasattr(order_response, "crmForms"):
            crm_forms = self.client.dict(order_response["crmForms"])
            for form in crm_forms["CrmForms"]:
                self.save_crmForm(form_response=form, order=order, case=None, contactRecord=None)

        return order

    def save_product(self, product_response, order):
        # try:
        #     order_product = OrderProduct.objects.get(
        #         productId=product_response.productId,
        #         variationId=product_response.variationId,
        #         order=order
        #     )
        # except OrderProduct.DoesNotExist:
        #     order_product = OrderProduct.objects.create(
        #         productId=product_response.productId,
        #         variationId=product_response.variationId,
        #         order=order
        #     )
        # else:
        #     try:
        #         order_product = OrderProduct.objects.get(productId=product_response.productId, order=order)
        #     except OrderProduct.DoesNotExist:
        order_product = OrderProduct.objects.create(productId=product_response.productId, order=order)
        order_product.productCode = product_response.productCode
        order_product.productDescription = unicode(product_response.productDescription).encode('utf-8').strip()
        order_product.units = product_response.units
        order_product.unitPrice = product_response.unitPrice
        order_product.unitTaxRate = product_response.unitTaxRate
        order_product.totalProductPrice = product_response.totalProductPrice
        order_product.productName = unicode(product_response.productName).encode('utf-8').strip()
        if hasattr(product_response, 'variationId'):
            order_product.variationId = product_response.variationId
        order_product.save()

    def save_payment(self, payment_response, order):
        # try:
        #     order_payment = OrderPayment.objects.get(order=order, paymentDate=payment_response.paymentDate)
        # except OrderPayment.DoesNotExist:
        order_payment = OrderPayment.objects.create(order=order, paymentDate=payment_response.paymentDate)
        order_payment.paymentMethodTypeID = payment_response.paymentMethodTypeID
        order_payment.amount = payment_response.amount
        order_payment.paymentStatusID = payment_response.paymentStatusID
        order_payment.save()

    def save_address(self, address_response, order=None, contactRecord=None):
        try:
            address = addresses.objects.get(addressTypeID=address_response.addressTypeID, order=order, contactRecord=contactRecord)
        except addresses.DoesNotExist:
            address = addresses.objects.create(addressTypeID=address_response.addressTypeID, order=order, contactRecord=contactRecord)

        address.addressLine1 = unicode(address_response.addressLine1).encode('utf-8').strip()
        if hasattr(address_response, 'addressLine2'):
            if address_response.addressLine2 is not None and address_response.addressLine2 != '':
                address.addressLine2 = unicode(address_response.addressLine2).encode('utf-8').strip()
        address.city = unicode(address_response.city).encode('utf-8').strip()
        address.zipcode = address_response.zipcode
        address.state = unicode(address_response.state).encode('utf-8').strip()
        address.countryCode = address_response.countryCode
        address.save()

    def save_crmForm(self, form_response, order=None, case=None, contactRecord=None):
        try:
            crm_form = crmForm.objects.get(formId=form_response.formId, bc_site=self.site)
        except crmForm.DoesNotExist:
            crm_form = crmForm.objects.create(formId=form_response.formId, formName=form_response.formName, bc_site=self.site)
        else:
            crm_form.formName = form_response.formName
            crm_form.save()

        if order is not None:
            order.crmForms.add(crm_form)

        if case is not None:
            case.crmForms.add(crm_form)

        if contactRecord is not None:
            contactRecord.crmForms.add(crm_form)

        crm_fields = self.client.dict(form_response)
        for field in crm_fields["crmFormFields"]:
            for f in field[1]:
                try:
                    crm_field = crmFormField.objects.get(fieldId=f.fieldId, crmForm=crm_form)
                except crmFormField.DoesNotExist:
                    crm_field = crmFormField.objects.create(fieldId=f.fieldId, fieldTypeId=f.fieldTypeId,
                                                            fieldName=f.fieldName, crmForm=crm_form,
                                                            bc_site=self.site)

                # Once we have the field add the value in.
                try:
                    field_value = crmFormFieldValue.objects.get(
                        crmFormField=crm_field,
                        order=order,
                        case=case,
                        contactRecord=contactRecord
                    )
                except crmFormFieldValue.DoesNotExist:
                    field_value = crmFormFieldValue.objects.create(
                        fieldValue=unicode(u"%s").encode('utf8') % f.fieldValue if f.fieldValue else "",
                        crmFormField=crm_field,
                        order=order,
                        case=case,
                        contactRecord=contactRecord
                    )
                else:
                    field_value.fieldValue = unicode(u"%s").encode('utf8') % f.fieldValue if f.fieldValue else ""
                    field_value.save()

    def order_list_retrieve_response(self, utcLastUpdateDate, recordStart=0):
        localLastUpdateDate = self.site.utc_to_local(utcLastUpdateDate).replace(tzinfo=None)

        try:
            response = self.client.service.OrderList_Retrieve(
                str(self.site.admin_username),
                str(self.site.admin_password),
                int(self.site.site_id),
                localLastUpdateDate, recordStart, False
            )
        except WebFault, e:
            #You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the contact
            #result.message in this case will give you something like the following message:
            #u"Server raised fault: 'Server was unable to process request. ---> ERROR: Case details for the given caseId
            #could not be found.'"
            logger.debug("Error retrieving Order List", extra={'stack':True})
            return None
        else:
            return response


    def order_list_retrieve(self, utcLastUpdateDate, recordStart=0):
        """
            Returns a list of Orders that were updated or added to DB since the last update date
        """
        # Convert utcLastUpdateDate to local time
        localLastUpdateDate = self.site.utc_to_local(utcLastUpdateDate).replace(tzinfo=None)

        try:
            response = self.client.service.OrderList_Retrieve(
                str(self.site.admin_username),
                str(self.site.admin_password),
                int(self.site.site_id),
                localLastUpdateDate, recordStart, False
        )
        except WebFault, e:
            #You need to check the result with "isinstance(r,WebFault)" to see if the result is the error or the contact
            #result.message in this case will give you something like the following message:
            #u"Server raised fault: 'Server was unable to process request. ---> ERROR: Case details for the given caseId
            #could not be found.'"
            logger.debug("Error Retrieving Order List", extra={'stack':True})
            return [], []

        if response is None:
            return [], []

        # Now iterate through - see if we can share code with Case Retrieve and Order Retrieve
        new_orders, updated_orders = [], []
        if hasattr(response, "OrderList_RetrieveResult"):
            orders = self.client.dict(response["OrderList_RetrieveResult"])
            for incoming_order in orders['OrderDetails']:
                if incoming_order.entityId == -1:
                    continue
                contact = self.contact_retrieve_by_entity_id(incoming_order.entityId)
                try:
                    db_order = Order.objects.get(orderId=incoming_order.orderId, bc_site=self.site)
                except Order.DoesNotExist:
                    new_order = self.save_order(incoming_order, contact, 2008)
                    print 'Added New OrderID: ' + str(incoming_order.orderId)
                    new_orders.append(new_order)
                else:
                    # check the last update date against the one we have in DB
                    if db_order.lastUpdateDate < self.site.local_to_utc(incoming_order.lastUpdateDate):
                        existing_order = self.save_order(incoming_order, contact, 2008)
                        print 'Updated existing OrderID: ' + str(incoming_order.orderId)
                        updated_orders.append(existing_order)

        return new_orders, updated_orders

    def get_or_update_orders(self, utcLastUpdateDate, recordStart=0):
        lastUpdateDate = self.site.utc_to_local(utcLastUpdateDate).replace(tzinfo=None)

        response = self.client.service.OrderList_Retrieve(
            str(self.site.admin_username),
            str(self.site.admin_password),
            int(self.site.site_id),
            lastUpdateDate, recordStart, False
        )

        orders = self.client.dict(response["OrderList_RetrieveResult"])
        for incoming_order in orders['OrderDetails']:
            if incoming_order.entityId == -1:
                continue

            contact = self.contact_retrieve_by_entity_id(incoming_order.entityId)
            if contact is None:
                continue

            try:
                Order.objects.get(orderId=incoming_order.orderId, bc_site=self.site)
            except Order.DoesNotExist:
                contact = self.contact_retrieve_by_entity_id(incoming_order.entityId)
                if contact is None:
                    continue
            self.save_order(incoming_order, contact, 2008)

        while response.moreRecords:
            recordStart += 100
            response = self.client.service.OrderList_Retrieve(
                str(self.site.admin_username),
                str(self.site.admin_password),
                int(self.site.site_id),
                lastUpdateDate, recordStart, False
            )
            orders = self.client.dict(response["OrderList_RetrieveResult"])

            for incoming_order in orders['OrderDetails']:
                if incoming_order.entityId == -1:
                    continue

                contact = self.contact_retrieve_by_entity_id(incoming_order.entityId)
                if contact is None:
                    continue

                try:
                    Order.objects.get(orderId=incoming_order.orderId, bc_site=self.site)
                except Order.DoesNotExist:
                    contact = self.contact_retrieve_by_entity_id(incoming_order.entityId)
                    if contact is None:
                        continue
                self.save_order(incoming_order, contact, 2008)

    def add_email_to_marketing_list(self, email_address, list_id):
        clist = self.client.factory.create('ArrayOfCampaignList')
        campaign = self.client.factory.create('CampaignList')
        campaign.campaignListID = int(list_id)
        campaign.campaignListUnsubscribe = False
        campaign.campaignListName = "No name"
        clist.CampaignList.append(campaign)
        try:
            response = self.client.service.Contact_CampaignListListUpdateInsert(str(self.site.admin_username), str(self.site.admin_password), int(self.site.site_id), email_address, clist, True)
            return None
        except WebFault as e:
            logger.debug('Adding %s to list %s on site %s failed. Error:' % (email_address, list_id, self.site), extra={'stack':True})
            return e

    def remove_email_from_marketing_list(self, email_address, list_id):
        clist = self.client.factory.create('ArrayOfCampaignList')
        campaign = self.client.factory.create('CampaignList')
        campaign.campaignListID = int(list_id)
        campaign.campaignListUnsubscribe = True
        campaign.campaignListName = "No name"
        clist.CampaignList.append(campaign)
        try:
            response = self.client.service.Contact_CampaignListListUpdateInsert(str(self.site.admin_username), str(self.site.admin_password), int(self.site.site_id), email_address, clist, True)
            return None
        except WebFault as e:
            logger.debug('Removing %s from list %s on site %s failed. Error:' % (email_address, list_id, self.site), extra={'stack': True})
            return e

    def get_subscribed_zones(self, crm_id):
        try:
            response = self.client.service.Contact_RetrieveZonesByEntityID(str(self.site.admin_username), str(self.site.admin_password), int(self.site.site_id), int(crm_id))
        except WebFault, e:
            return None
        else:
            print response

    def order_list_retrieve_by_contact(self, entityId):
        try:
            response = self.client.service.OrderList_RetrieveByContact(str(self.site.admin_username), str(self.site.admin_password), int(self.site.site_id), int(entityId))
        except WebFault, e:
            return None
        else:
            print response

    def get_marketing_lists(self):
        """
        Retrieves the marketing lists from the site and stores them locally
        """
        try:
            response = self.client.service.CampaignListList_Retrieve(str(self.site.admin_username), str(self.site.admin_password), int(self.site.site_id))
        except WebFault, e:
            return None
        else:
            clists = self.client.dict(response)
            generated_lists = []
            for clist in clists['CampaignList']:
                campaign_list, created = MarketingList.objects.get_or_create(bc_site=self.site, list_id=clist.campaignListID, name=clist.campaignListName)
                generated_lists.append(campaign_list)
            return generated_lists

    def case_list_retrieve_by_contact(self, entityId):
        try:
            response = self.client.service.CaseList_EntityRetrieve(str(self.site.admin_username), str(self.site.admin_password), int(self.site.site_id), int(entityId), 0, False)
        except WebFault, e:
            return None
        else:
            print response
