from django import template
from django.utils.safestring import mark_safe
from django.utils.timezone import datetime,timedelta
from django.core.exceptions import FieldDoesNotExist
import re

register = template.Library()		#对象名register不可变

# 显示app表的详细名称
@register.simple_tag       #1 simple_tag用法
def render_table_name(admin_class):
    return admin_class.model._meta.verbose_name_plural

# 显示表字段名字 与 点击字段名进行排序
@register.simple_tag
def build_table_header_column(column,admin_class,filter_conditions,search_filter_text,orderby_key,):
    filters = ''
    for k,v in filter_conditions.items():
        filters += "&%s=%s"%(k,v)
    if orderby_key:
        if orderby_key.startswith('-'):
            sort_icon = '''<span class="glyphicon glyphicon-menu-up" aria-hidden="true"></span>'''
        else:
            sort_icon = '''<span class="glyphicon glyphicon-menu-down" aria-hidden="true"></span>'''
        if orderby_key.strip('-') == column:
            orderby_key = orderby_key
        else:
            orderby_key = column
            sort_icon = ''
    else:
        sort_icon = ''
        orderby_key = column
    try:    #这里的try是因为显示数据库未定义字段时会报错
        column_verbose_name = admin_class.model._meta.get_field(column).verbose_name.upper()
        ele = '''<th><a href="?o={orderby_key}&_q={search_filter_text}&{filters}">{column_verbose_name}</a>{sort_icon}</th>'''\
            .format(orderby_key=orderby_key,filters=filters,column_verbose_name=column_verbose_name,sort_icon=sort_icon,search_filter_text=search_filter_text)
    except FieldDoesNotExist as e:  # 在前端显示数据库中不存在的字段
        column_verbose_name = getattr(admin_class, column).display_name.upper()
        ele = ''' <th><a href="javascript:void(0);">%s</a></th>''' % column_verbose_name
    return mark_safe(ele)

# 显示list_display要显示字段具体内容
@register.simple_tag
def build_table_row(request,obj,admin_class,search_filter_text):
    ele = ''
    for index,colunm in enumerate(admin_class.list_display):
        try:     #这里的try是因为显示数据库未定义字段时会报错
            field_obj = obj._meta.get_field(colunm)
            field_val = getattr(obj,colunm)
            if field_obj.choices:
                column_data = getattr(obj,'get_%s_display'%colunm)()
            elif hasattr(field_val,"select_related"):
                data_list = []
                column_data = field_val.all().values_list()
                for data in column_data:
                    data_list.append(data[1])
                column_data = ' '.join(data_list)
            else:
                column_data = getattr(obj, colunm)
            if type(column_data).__name__ == 'datetime':
                column_data = column_data.strftime("%Y-%m-%d")
            if len(str(column_data)) > 20:
                column_data = str(column_data[0:20])+'...'
            if colunm in admin_class.search_fields:
                if column_data:
                    column_data = re.sub(search_filter_text,'''<span style="color: red">%s</span>'''%search_filter_text,column_data)
            if index == 0:
                ele += '''<td><a href="{request_path}{obj_id}/change/">{column_data}</a></td>'''.format(request_path=request.path,obj_id=obj.id,column_data=column_data)
            else:
                ele += '''<td>{column_data}</td>'''.format(column_data=column_data)
        except FieldDoesNotExist as e:   # 在前端显示数据库中不存在的字段
            if hasattr(admin_class, colunm):
                column_func = getattr(admin_class, colunm)
                admin_class.instance = obj
                admin_class.request = request
                column_data = column_func()
            ele += "<td>%s</td>" % column_data
    return mark_safe(ele)

#搜索功能（下拉框）
@register.simple_tag
def render_filter_ele(filter_field,admin_class,filter_conditions):
    select_ele = '<select name="{filter_field}" class="form-control select-width">'
    select_ele += '''<option value=''>-----------</ option >'''
    field_obj = admin_class.model._meta.get_field(filter_field)
    if field_obj.choices:
        for choice_item in field_obj.choices:
            selected = ''
            if filter_conditions.get(filter_field) == str(choice_item[0]):
                selected = 'selected'
            option_ele = '''<option value='%s' %s>%s</ option >'''%(choice_item[0],selected,choice_item[1])
            select_ele += option_ele
    if type(field_obj).__name__ == 'ForeignKey':
        for choice_item in field_obj.get_choices()[1:]:
            selected = ''
            if filter_conditions.get(filter_field) == str(choice_item[0]):
                selected = 'selected'
            option_ele = '''<option value='%s' %s>%s</ option >'''%(choice_item[0],selected,choice_item[1])
            select_ele += option_ele

    if type(field_obj).__name__ in ['DateTimeField', 'DateField']:
        date_els = []
        today_ele = datetime.now().date()

        date_els.append(['今天', datetime.now().date()])
        date_els.append(['昨天', today_ele - timedelta(days=1)])
        date_els.append(['近七天', today_ele - timedelta(days=7)])
        date_els.append(['本月', today_ele.replace(day=1)])
        date_els.append(['近30天', today_ele - timedelta(days=30)])
        date_els.append(['近90天', today_ele - timedelta(days=90)])
        date_els.append(['近180天', today_ele - timedelta(days=180)])
        date_els.append(['本年', today_ele.replace(month=1, day=1)])
        date_els.append(['近365天', today_ele - timedelta(days=365)])
        selected = ''
        for item in date_els:
            if filter_conditions.get('date__gte') == str(item[1]):  # choice_item[0]选中的choices字段值的id
                selected = 'selected'
            select_ele += '''<option value='%s' %s>%s</option>''' % (item[1], selected, item[0])
            selected = ''
        filter_field_name = "%s__gte" % filter_field
    else:
        filter_field_name = filter_field
    select_ele += '</select>'
    select_ele = select_ele.format(filter_field=filter_field_name)
    return mark_safe(select_ele)

#分页
@register.simple_tag
def render_page_ele(loop_counter,query_sets,filter_conditions,search_text,previous_orderby):
   #query_sets.number 获取当前页
   #loop_counter循环到第几页
   filters = ''
   for k,v in filter_conditions.items():
       filters += "&%s=%s"%(k,v)

   if abs(query_sets.number -loop_counter) <= 3:
      ele_class = ""
      if query_sets.number == loop_counter:
         ele_class = 'active'
      ele = '''<li class="%s"><a href="?page=%s&_q=%s&o=%s&%s">%s</a></li>'''%(ele_class,loop_counter,search_text,previous_orderby,filters,loop_counter)
      return mark_safe(ele)
   return ''

#获取下拉菜单过滤后拼接的url格式字符串格式
@register.simple_tag
def render_filter_conditions(filter_conditions):
    filters = ''
    for k, v in filter_conditions.items():
        filters += "&%s=%s" % (k, v)
    return filters

# 返回已选中的m2m数据（filter_horizontal）
@register.simple_tag
def get_m2m_selected_obj_list(form_obj,field):
	'''
	:param form_obj:    要修改的那条ModelForm实例
	:param field:       ModelForm对应字段类（field.name获取字段名）
	:return:
	'''
	if form_obj.instance.id:
		field_obj = getattr(form_obj.instance,field.name)
		return field_obj.all()

# 返回所有未选中m2m数据（filter_horizontal）
@register.simple_tag
def get_m2m_obj_list(admin_class,field,form_obj):
	'''
	:param admin_class:
	:param field:       多选select标签（field.name获取字段名）
	:param form_obj:    自动生成的ModelForm类
	:return:           返回m2m字段所有为选中数据
	'''
	field_obj = getattr(admin_class.model, field.name)  #获取表结构中的字段类
	all_obj_list = field_obj.rel.to.objects.all()   #取出所有数据（多对多字段）
	#单条数据的对象中的某个字段
	if form_obj.instance.id:  #这样就要求我们创建的表必须有id字段
		obj_instance_field = getattr(form_obj.instance,field.name)  #获取单条数据的某个字段instance
		selected_obj_list = obj_instance_field.all()                #取出所有已选数据（多对多字段）
	else:   #代表这是创建一条心数据
		return all_obj_list
	standby_obj_list = []
	for obj in all_obj_list:
		if obj not in selected_obj_list:        #selected_obj_list：所有已选数据
			standby_obj_list.append(obj)
	return standby_obj_list

