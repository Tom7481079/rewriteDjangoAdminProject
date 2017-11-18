from django.forms import ModelForm,ValidationError
from django.utils.translation import ugettext as _          #国际化

#创建动态生成ModelForm类的函数
def create_model_form(request,admin_class):
	'''
	创建动态生成ModelForm类的函数
	:param request:
	:param admin_class:
	:return:
	'''
	def default_clean(self):
		'''给所有form默认加一个clean验证：readonly字段验证，对整张只读表验证，clean钩子对整体验证'''
		error_list = []
		if self.instance.id:        #这是一个修改的表单，如果为空就是一个添加表单，才判断字段字段值是否改变
			for field in admin_class.readonly_fields:
				field_val = getattr(self.instance,field)        #从数据库中取到对应字段的值

				if hasattr(field_val,"select_related"):       #多对多字段只读
					m2m_objs = getattr(field_val,"select_related")().select_related()
					m2m_vals = [i[0] for i in m2m_objs.values_list('id')]
					set_m2m_vals = set(m2m_vals)			# print("cleaned data",self.cleaned_data)
					set_m2m_vals_from_frontend = set([i.id for i in self.cleaned_data.get(field)])
					if set_m2m_vals != set_m2m_vals_from_frontend: #1 判断多对多字段是否修改
						self.add_error(field,"readonly field")
					continue
				field_val_from_frontand = self.cleaned_data.get(field)
				if field_val != field_val_from_frontand:  #2 判断非多对多字段是否修改
					error_list.append(
						ValidationError(
							_('Field %(field)s is readonly,data should be %(val)s'),
							code='invalid',
							params={'field':field,'val':field_val},
						))
				#readonly_table check
				# if admin_class.readonly_table:      #3 防止黑客自己写提交按钮提交整张表都是只读权限的表
		if admin_class.readonly_table:      #3 防止黑客自己写提交按钮提交整张表都是只读权限的表
			raise ValidationError(
					_('Table is readonly,cannot be modified ro added'),
					code='invalid',
				)
		print(11112222)
		self.ValidationError = ValidationError  #这样用户自己验证时就可以不必导入了

		#在这个cleaned方法中定义一个允许用户自己定义的方法做验证
		response = admin_class.default_form_validation(self)  #4 clean钩子对整体验证
		if response:
			error_list.append(response)

		if error_list:
			raise ValidationError(error_list)
	def __new__(cls,*args,**kwargs):
		'''在创建form时添加样式，为每个字段预留钩子'''
		for field_name,field_obj in cls.base_fields.items():
			field_obj.widget.attrs['class'] = "form-control"
			if not hasattr(admin_class,"is_add_form"):
				if field_name in admin_class.readonly_fields:
					field_obj.widget.attrs['disabled'] = "disabled"

			# clean_字段名 是字段钩子（每个字段都有对应的这个钩子）
			if hasattr(admin_class, "clean_%s" % field_name):  # 用户自定义字段验证
				field_clean_func = getattr(admin_class, "clean_%s" % field_name)
				setattr(cls, "clean_%s" % field_name, field_clean_func)
		return ModelForm.__new__(cls)  #调用一下ModelForm的__new__方法否则不往下走


	'''动态生成ModelForm'''
	class Meta:
		model = admin_class.model
		fields = "__all__"
		exclude = admin_class.modelform_exclude_fields  # 那些字段不显示
		# exclude = ("qq",)
	attrs = {'Meta':Meta}
	_model_form_class = type("DynamicModelForm",(ModelForm,),attrs)
	setattr(_model_form_class,"__new__",__new__)
	setattr(_model_form_class,'clean',default_clean)        #动态将_default_clean__函数添加到类中
	return _model_form_class