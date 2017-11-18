from django.db.models import Q

# 将前端下拉菜单过滤条件变成字典形式（并去除关键字）
def select_filter(request,admin_class):
	filter_conditions = {}
	keywords = ['_q','page','o']
	for k,v in request.GET.items():
		if k in keywords:
			continue
		if v:
			filter_conditions[k]=v
	return admin_class.model.objects.filter(**filter_conditions),filter_conditions

# 返回input搜索框过滤后的内容
def search_filter(request,admin_class,obj_list):
	search_key = request.GET.get('_q','')
	q_obj = Q()
	q_obj.connector = "OR"
	for column in admin_class.search_fields:
		q_obj.children.append(('%s__contains'%column,search_key))
	return obj_list.filter(q_obj)

# 将过滤完成的数据进行排序
def table_sort(request,admin_class,obj_list):
	orderby_key = request.GET.get('o','')
	if orderby_key:
		res = obj_list.order_by(orderby_key)
		if orderby_key.startswith("-"):
			orderby_key = orderby_key.strip("-")
		else:
			orderby_key = "-%s"%(orderby_key)
	else:
		res = obj_list.order_by('-id')
	return res,orderby_key