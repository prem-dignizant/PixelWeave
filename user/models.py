from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from uuid import uuid4

# Create your models here.


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email=None, password=None, **extra_fields):
        if extra_fields.get('is_superuser', False)==False:
            if not email:
                raise ValueError("The given email must be set")
        if email:
            email = self.normalize_email(email)
            extra_fields['email'] = email
        
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)        
        return self._create_user(email, password, **extra_fields)

class Base(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractBaseUser, PermissionsMixin, Base):
    user_id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, unique=True
    )
    email = models.EmailField(db_index=True, max_length=100, unique=True,null=True,blank=True)
    user_name=models.CharField(max_length=128,unique=True,null=False,blank=False)
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    credit = models.IntegerField(default=0)
    USERNAME_FIELD = "user_name"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.user_name or ""

