import logging
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.views.decorators.csrf import csrf_exempt
from bc_api.crm_wrapper import CrmWrapper
from bc_api.models.crm import BCSite


CASE_TYPE = 2001
ORDER_TYPE = 2008

logger = logging.getLogger(__name__)


@csrf_exempt
def notifications(request, site_code, object_type_param=None):
    if request.method == "POST":
        objectID = request.POST.get("ObjectID")
        objectType = request.POST.get("ObjectType")

        try:
            site = BCSite.objects.get(site_code=site_code)
        except BCSite.DoesNotExist:
            return HttpResponse("Site doesn't exist!")
        bc_wrap = CrmWrapper(site)

        if object_type_param is None:
            try:
                if int(objectType) == CASE_TYPE:
                    case = bc_wrap.case_retrieve(int(objectID), int(objectType))
                    if case is None:
                        return  HttpResponse("Could not retrieve Case, this Case ID most likely does not exist")
                else:
                    order = bc_wrap.order_retrieve(int(objectID), int(objectType))
                    if order is None:
                        return HttpResponse("Could not retrieve Order, this Order ID most likely does not exist")
            except Exception as e:
                print e
                return HttpResponse("Could not retrieve case/order, BC returned an error. Please try again later")
        else:
            try:
                if object_type_param == CASE_TYPE:
                    case = bc_wrap.case_retrieve(int(objectID), int(objectType))
                    if case is None:
                        return  HttpResponse("Could not retrieve Case, this Case ID most likely does not exist")
                else:
                    order = bc_wrap.order_retrieve(int(objectID), int(objectType))
                    if order is None:
                        return HttpResponse("Could not retrieve Order, this Order ID most likely does not exist")
            except Exception, e:
                return HttpResponse("Could not retrieve case/order, BC returned an error. Please try again later")

    else:
        return HttpResponsePermanentRedirect("http://127.0.0.1")
    return HttpResponse("OKAY")


@csrf_exempt
def order_notifications(request, site_code):
    return notifications(request, site_code, ORDER_TYPE)


@csrf_exempt
def case_notifications(request, site_code):
    return notifications(request, site_code, CASE_TYPE)
