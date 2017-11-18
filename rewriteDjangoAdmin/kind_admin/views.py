from django.shortcuts import render,HttpResponse,redirect
from crm import  models
import os

#1 将表注册到我们的kind_admin中
from kind_admin import kind_admin

#2 过滤 排序
from kind_admin.utils import select_filter,search_filter,table_sort

#3 分页
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

#4 动态生成ModelForm类
from kind_admin.forms import create_model_form

#5 这里是登录和注销需要的模块
from django.contrib.auth import login,authenticate,logout
from django.contrib.auth.decorators import login_required    #装饰器，用来验证用户是否登录

#6 导入我们自己写的 通用权限管理组件
from kind_admin.permissions import permission

@login_required
def kind_admin_index(request):
	'''在前端展示app和表名'''
	return render(request,'kind_admin/kind_admin_index.html',{"table_list":kind_admin.enabled_admins})

# @permission.check_permisssion
@login_required
def display_table_obj(request,app_name,table_name):
	'''分页展示每个表中具体内容'''
	admin_class = kind_admin.enabled_admins[app_name][table_name]
	#1. 对select下拉菜单过滤
	obj_list,filter_conditions = select_filter(request,admin_class)
	#2. 对search搜索过滤
	obj_list = search_filter(request,admin_class,obj_list)
	#3. 对表头排序
	obj_list,orderby_key = table_sort(request,admin_class,obj_list)

	search_text = request.GET.get('_q','')
	if not search_text:               #没有搜索时显示能够匹配搜索的字段
		search_text = "serach by: %s"%(','.join(admin_class.search_fields))

	if request.method == 'POST':    #分发Django admin的action操作
		action = request.POST.get('action')
		selected_ids = request.POST.get('selected_ids')
		if selected_ids:
			selected_ids = selected_ids.split(',')
			selected_objs = admin_class.model.objects.filter(id__in=selected_ids)
		else:
			raise KeyError("No object selected.")
		if hasattr(admin_class,action):
			action_func = getattr(admin_class,action)
			request._admin_action = action
			return action_func(admin_class,request,selected_ids)

	#分页
	paginator = Paginator(obj_list, admin_class.list_per_page)  # Show 25 contacts per page
	page = request.GET.get('page')
	try:
		contacts = paginator.page(page)
	except PageNotAnInteger:  # 页数为负数（或不是整数）返回第一页
		contacts = paginator.page(1)
	except EmptyPage:
		contacts = paginator.page(paginator.num_pages)  # 页数超出范围返回最后一页
	return render(request,'kind_admin/display_table_obj.html',
	              {'admin_class':admin_class,
	               'obj_list': contacts,
	               'filter_conditions':filter_conditions,
	               'app_name':app_name,
	               'table_name':table_name,
	               'table_name_detail':admin_class.model._meta.verbose_name_plural,
	               'search_text':search_text,
	               'search_filter_text':request.GET.get('_q',''),
	               'orderby_key':orderby_key,
	               'previous_orderby':request.GET.get('o',''),
	               })

# @permission.check_permisssion
@login_required
def table_obj_add(request,app_name,table_name):
	admin_class = kind_admin.enabled_admins[app_name][table_name]
	admin_class.is_add_form = True
	model_form_class = create_model_form(request,admin_class)
	if not admin_class.using_add_func:
		rewrite_add_page = admin_class.rewrite_add_page(admin_class,request,app_name,table_name,model_form_class)
		return rewrite_add_page
	if request.method == 'POST':
		form_obj = model_form_class(request.POST)
		if form_obj.is_valid():
			form_obj.save()
			return redirect(request.path.replace("/add/",'/'))
	form_obj = model_form_class()
	return render(request,'kind_admin/table_obj_add.html',
	              {'form_obj':form_obj,
	               'app_name':app_name,
	               'table_name':table_name,
	               'table_name_detail': admin_class.model._meta.verbose_name_plural,
	               'admin_class': admin_class,
	               })

# @permission.check_permisssion
@login_required
def table_obj_change(request,app_name,table_name,obj_id):
	admin_class = kind_admin.enabled_admins[app_name][table_name]
	model_form_class = create_model_form(request,admin_class)
	obj = admin_class.model.objects.get(id=obj_id)
	form_obj = model_form_class(instance=obj)
	if request.method == 'POST':
		form_obj = model_form_class(request.POST,instance=obj)
		if form_obj.is_valid():
			form_obj.save()
		else:
			print('errors',form_obj.errors)
	return render(request,'kind_admin/table_obj_change.html',
	              {'form_obj':form_obj,
	               'app_name':app_name,
	               'table_name':table_name,
	               'table_name_detail': admin_class.model._meta.verbose_name_plural,
	               'admin_class':admin_class,
	               'obj_id':obj_id})

@login_required
def password_reset(request,app_name,table_name,obj_id):
	admin_class = kind_admin.enabled_admins[app_name][table_name]
	model_form_class = create_model_form(request,admin_class)
	obj = admin_class.model.objects.get(id=obj_id)
	errors = {}
	if request.method == 'POST':
		_password1 = request.POST.get("password1")
		_password2 = request.POST.get("password2")
		if _password1 == _password2:
			if len(_password2) >5:
				print('obj reset',obj,type(obj))
				obj.set_password(_password1)         #
				obj.save()
				return redirect(request.path.rstrip('password/'))
			else:
				errors['password_too_short'] = "muset not less than 6 letters"
		else:
			errors['invalid_password'] = "passwords are not the same"
	return render(request,'kind_admin/password_reset.html',{'obj':obj,
	                                                        'errors':errors,
	                                                        'app_name':app_name,
	                                                        'table_name':table_name,
	                                                        'table_name_detail': admin_class.model._meta.verbose_name_plural,
	                                                        'obj_id':obj_id
	                                                        })

# @permission.check_permisssion
@login_required
def table_obj_delete(request,app_name,table_name,obj_id):
	admin_class = kind_admin.enabled_admins[app_name][table_name]
	obj = admin_class.model.objects.get(id=obj_id)
	if request.method == "POST":
		obj.delete()
		return redirect("/kind_admin/%s/%s/"%(app_name,table_name))

	return render(request,'kind_admin/table_obj_delete.html',
	              {'app_name':app_name,
	               'table_name':table_name,
	               'table_name_detail': admin_class.model._meta.verbose_name_plural,
	               'obj_id':obj_id})



############################# 下面这一块用来做用户登录注销功能  #####################################
def acc_login(request):
	errors = {}
	if request.method == 'POST':
		_email = request.POST.get('email')
		_password = request.POST.get('password')
		user = authenticate(username= _email, password=_password)   #通过验证会返回一个user对象
		print('user',user)
		if user:
			login(request,user)         #Django自动登录，然后创建session
			next_url = request.GET.get("next","/kind_admin/")    #登录成功后会跳转的页面，没有next时是/kind_admin/
			#未登录时直接输入url时跳转到登录界面是会加上"next"参数
			return redirect(next_url)
		else:
			errors['error'] = "Wrong username or password!"
	return render(request,'kind_admin/login.html',{'errors':errors})

def acc_logout(request):
	logout(request)
	return redirect("/kind_admin/login/")
