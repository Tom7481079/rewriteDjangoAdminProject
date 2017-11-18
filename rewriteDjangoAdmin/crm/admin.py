#解决我们改写的Django admin 中user表验证时密码明文问题
from crm import models
from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class UserCreationForm(forms.ModelForm):   #不必改什么（创建用户时调用这个类）
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = models.UserProfile
        fields = ('email', 'name')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):    #不必改什么（修改用户时调用这个类）
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = models.UserProfile
        fields = ('email', 'password', 'name', 'is_active', 'is_admin')

    def clean_password(self):
        return self.initial["password"]

class UserProfileAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'name', 'is_admin',"is_staff",)
    list_filter = ('name','email')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ("user_permissions",)  #django admin显示多对多的选项框


    fieldsets = (			#fields这里指定了在表中修改界面显示的字段有哪些
        (None, {'fields': ('email', 'password')}),		#前面是None就不会显示一个分割线，fields后面显示的是要显示的字段
        ('Personal', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_admin',"is_active","user_permissions",'groups')}),		#这里指定在修改界面中要显示的字段
    )
    #Permissions后的字典记得加上，is_admin，is_active否则我们无法再前端勾选，
    # 那么我们自己新建的用户无法登陆Django Admin后台

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2')}		#指定添加用户时必须有的字段
        ),
    )

admin.site.register(models.UserProfile, UserProfileAdmin)
admin.site.unregister(Group)