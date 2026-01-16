from django.db import models
from user.models import User
# Create your models here.

class Base(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Wardrobe(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='wardrobe')
    image = models.ImageField(upload_to='wardrobe/',null=True,blank=True)
    bg_color = models.CharField(max_length=128,null=True,blank=True)

class Studio(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='studio')
    wardrobe = models.ForeignKey(Wardrobe, on_delete=models.CASCADE,related_name='studio',null=True,blank=True)
    image = models.ImageField(upload_to='images/',null=True,blank=True)  
    mockup = models.ImageField(upload_to='mockups/',null=True,blank=True)