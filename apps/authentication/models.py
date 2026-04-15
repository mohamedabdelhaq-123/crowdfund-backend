from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,BaseUserManager

from django.core.validators import RegexValidator





class UserManager(BaseUserManager): # when make custom user so make custom manager to handle creation 
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email) # convert to lowercase to prevent duplic. acc. bec. casting diff.
        user = self.model(email=email, **extra_fields)
        
        user.set_password(password) # hash pass
        user.save(using=self._db) #It tells the save() method: "Save this object to the same database this manager was called from.
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        
        extra_fields.setdefault('is_staff', True)   # Force the correct permissions and status for an admin
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_activated', True)
        extra_fields.setdefault('role', 'admin')

        #more safety
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields) #now create the user
    


class User(AbstractBaseUser, PermissionsMixin):
    objects=UserManager() # Tells Django to use our custom rules (like setting roles) when creating users.

    egyptian_phone_regex = RegexValidator(
        regex=r'^01[0125][0-9]{8}$',
        message="Phone number must start with 010, 011, 012, or 015 followed by 8 digits."
    )
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    

    profile_pic = models.URLField(null=True, blank=True) 
    profile_pic_public_id = models.CharField(max_length=255, null=True, blank=True)
   
    mobile_number = models.CharField(validators=[egyptian_phone_regex], max_length=11, unique=True) # need validator
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    birthdate = models.DateField(null=True, blank=True)
    fb_profile = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    is_activated = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)
    last_activation_sent = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_staff = models.BooleanField(default=False)    # Required for Django Admin access


    USERNAME_FIELD = 'email' # user log in using the email
    REQUIRED_FIELDS = ['first_name', 'last_name', 'mobile_number'] #must enter when create superuser




