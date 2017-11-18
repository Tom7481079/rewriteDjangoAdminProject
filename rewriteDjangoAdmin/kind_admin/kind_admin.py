from crm import models
from django.shortcuts import render,HttpResponse,redirect

enabled_admins = {}
class BaseAdmin(object):
	using_add_func = True         #如果需要有单独的添加页面继承时改为false
	using_change_func = True      #如果需要有单独的修改页面继承时改为false
	list_display = []
	readonly_fields = []
	list_filter = []
	search_fields = []
	actions = ['delete_selected_objs']
	list_per_page = 5
	modelform_exclude_fields = []
	readonly_table = False
	filter_horizontal =[]
	def delete_selected_objs(self, request, selected_ids):
		app_name = self.model._meta.app_label
		table_name = self.model._meta.model_name
		if self.readonly_table:
			errors = {"readonly_table": "table is readonly,cannot be deleted" }
		else:
			errors = {}
		if request.POST.get("delete_confirm") == "yes":
			if not self.readonly_table:     #整张表readonly时不能删除
				objs = self.model.objects.filter(id__in=selected_ids).delete()
			return redirect("/kind_admin/%s/%s/"%(app_name,table_name))   #删除后返回到/kind_admin/crm/customer/页面
		# 这里是通过table_obj_delete.html页面向 /kind_admin/crm/customer/ 的url传送post请求
		return render(request, 'kind_admin/table_obj_delete.html',
		              {'app_name': app_name,
		               'table_name': table_name,
		               'selected_ids': ','.join(selected_ids),
		               'action': request._admin_action})

	def default_form_validation(self):  # clean钩子对整体验证
		''' 每个class_admin都可以重写这个方法来对整体验证'''

def register(model_class,admin_class=BaseAdmin):
	app_name = model_class._meta.app_label
	table_name = model_class._meta.model_name
	if app_name not in enabled_admins:
		enabled_admins[app_name] = {}
	admin_class.model = model_class
	enabled_admins[app_name][table_name] = admin_class

class UserProfileAdmin(BaseAdmin):
	using_add_func = False
	list_display = ('email','name','is_admin','enroll')
	readonly_fields = ('password',)
	modelform_exclude_fields = ["last_login",]
	filter_horizontal = ('user_permissions',)
	search_fields = ['name',]
	modelform_exclude_fields = ['last_login','groups','roles','is_superuser']

	def rewrite_add_page(self,request,app_name,table_name,model_form_class):
		errors = {}
		if request.method == 'POST':
			_password1 = request.POST.get("password")
			_password2 = request.POST.get("password2")
			if _password1 == _password2:
				if len(_password2) > 5:
					form_obj = model_form_class(request.POST)
					if form_obj.is_valid():
						obj = form_obj.save()
						print('obj',obj,type(obj))
						obj.set_password(_password1)  #
						obj.save()
					return redirect(request.path.replace("/add/", '/'))
				else:
					errors['password_too_short'] = "muset not less than 6 letters"
			else:
				errors['invalid_password'] = "passwords are not the same"
		form_obj = model_form_class()
		return render(request, 'kind_admin/rewrite_add_user_page.html',
		              {'form_obj': form_obj,
		               'app_name': app_name,
		               'table_name': table_name,
		               'table_name_detail': self.model._meta.verbose_name_plural,
		               'admin_class': self,
		               'errors': errors,
		               })

	# 在前端显示数据库中不存在的字段
	def enroll(self):
		if self.instance == 1:
			link_name = "报名新课程"
		else:
			link_name = "报名"
		return '''<a href="/crm/customer/%s/enrollment/"> %s </a>''' %(self.instance.id,link_name)
	enroll.display_name = "报名链接"

	def clean_name(self):  # clean_字段名 是字段钩子（每个字段都有对应的这个钩子）
		print("name clean validation:", self.cleaned_data["name"])
		if not self.cleaned_data["name"]:
			self.add_error('name', "cannot be null")
		else:
			return self.cleaned_data["name"]


register(models.UserProfile,UserProfileAdmin)
