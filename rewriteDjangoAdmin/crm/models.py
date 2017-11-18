from django.db import models
from django.utils.translation import ugettext_lazy as _      #国际化
from django.utils.safestring import mark_safe
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,PermissionsMixin
)

#1. 创建用户时调用这个类
class UserProfileManager(BaseUserManager):   #这个方法用来创建普通用户
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(      #验证email
            email=self.normalize_email(email),
            name=name,
        )
        user.set_password(password)     #让密码更安全，设置密码,给密码加盐
        self.is_active = True           #指定创建用户默认是active
        user.save(using=self._db)       #保存创建信息
        return user
    def create_superuser(self, email, name, password):   #这个方法用来创建超级用户
        user = self.create_user(
            email,
            password=password,
            name=name,
        )
        user.is_active = True
        user.is_admin = True
        user.save(using=self._db)
        return user

#2 创建UserProfile表替代Django admin中的user表做用户登录
class UserProfile(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        null=True
    )
    password = models.CharField(_('password'),
            max_length=128,help_text=mark_safe('''<a href='password/'>修改密码</a>'''))
    name = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    #roles = models.ManyToManyField("Role",blank=True)

    objects = UserProfileManager()      #创建用户时会调用这里类

    USERNAME_FIELD = 'email'        #自己指定那个字段作为用户名
    REQUIRED_FIELDS = ['name',]      #那些字段是必须的

    # 下面这些是默认方法不必修改它
    def get_full_name(self):  # The user is identified by their email address
        return self.email
    def get_short_name(self):  # The user is identified by their email address
        return self.email
    def __str__(self):              # __unicode__ on Python 2
        return self.email
    # def has_perm(self, perm, obj=None):		#对用户授权（如果注释掉用户登录后没任何表权限）
    #     return True
    # def has_module_perms(self, app_label):          #对用户授权（如果注释掉用户登录后没任何表权限）
    #     return True
    @property
    def is_staff(self):
        #return self.is_admin		#这个必须是指定admin才能登陆Django admin后台
        return self.is_active				#这个只要用户时is_active的即可登陆Django admin后台

    class Meta:
        verbose_name_plural = '用户表'

        # 这里是定义权限管理组件
        permissions = (
            ('can_access_userprofile_list','可以访问用户表'),
            ('can_add_userprofile_get','可以访问添加用户表界面'),
            ('can_add_userprofile_post','可以添加用户表记录'),
        )




