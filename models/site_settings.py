from django.db import models
from bc_api.models.crm import BCSite


class Categories(models.Model):
    """
        Contains all site categories
    """
    name = models.CharField("Category Name", max_length=200)
    category_id = models.IntegerField("Category ID", default=-1)
    rel = models.CharField("Rel", max_length=100, null=True, blank=True, default="self")
    uri = models.CharField("URI", max_length=250, null=True, blank=True, default="self")
    parentId = models.IntegerField("Parent ID", default=-1)
    publicAccess = models.BooleanField("Public Access", default=False)
    fullPath = models.CharField("Full Path", max_length=200, null=True, blank=True)

    db_creation_date = models.DateTimeField("DB Creation Date", auto_now_add=True)
    db_modified_date = models.DateTimeField("DB Modified Date", auto_now=True)

    bc_site = models.ForeignKey(BCSite, related_name='categories')

    class Meta:
        app_label = 'bc_api'

    def __unicode__(self):
        return unicode("Name: %s | ID %s" % (self.name, self.category_id))
