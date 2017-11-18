from django.shortcuts import HttpResponse,render,redirect
from kind_admin.permissions import permission_list     #定义权限
from django.core.urlresolvers import resolve    #将绝对url转成相对url

def perm_check(*args,**kwargs):
	'''在装饰器中调用的函数，用来做权限检测的逻辑'''
	request = args[0]
	if request.user.is_authenticated():     #判断用户是否登录
		for permission_name, v in permission_list.perm_dic.items():
			url_matched = False
			if v['url_type'] == 1:   # v['url_type'] == 1 代表是绝对路径
				if v['url'] == request.path:  #绝对url匹配上
					url_matched = True
			else:                    # 否则匹配的就是相对路径
				#把request.path中的绝对url请求转成相对url名字
				resolve_url_obj = resolve(request.path)
				if resolve_url_obj.url_name == v['url']:   #相对url别名匹配上了
					url_matched = True
			if url_matched:     #如果url路径匹配上了才会走这步
				if v['method'] == request.method:   #请求方法也匹配上了（如：POST/GET）
					arg_matched = True
					for request_arg in v['args']:   #当某些url中要求必须有某些参数，判断这些必须参数没有为空的
						request_method_func = getattr(request,v['method']) #获取： request.POST 或 request.GET方法
						if not request_method_func.get(request_arg):       #只要有一个参数没有数据就返回FALSE
							arg_matched = False
					if arg_matched:   #走到这里，仅仅代表这个请求和这条权限的定义规则 匹配上了
						if request.user.has_perm(permission_name):  #判断当前用户是否有这个权限
							#能走到这里代表：有权限
							return True
	else:       #用户未登录返回到登录界面
		return redirect("/account/login/")

def check_permisssion(func):
	'''检测权限的装饰器'''
	def inner(*args,**kwargs):
		print("---permissson:",*args,**kwargs)
		perm_check(*args,**kwargs)
		if perm_check(*args,**kwargs) is True:  #如果返回True代表有权限
			return func(*args,**kwargs)
		else:
			return HttpResponse('没权限')
		return func(*args,**kwargs)
	return inner
