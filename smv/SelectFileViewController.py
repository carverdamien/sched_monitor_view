from smv.ViewController import ViewController
from bokeh.models.widgets import Select, Button, TextAreaInput
from bokeh.layouts import row, column
import os, io

def find_files(directory, ext):
	for root, dirs, files in os.walk(directory, topdown=False):
		for name in files:
			path = os.path.join(root, name)
			if ext == os.path.splitext(name)[1]:
				yield path

def preview(path):
	if path is None:
		return 'There is nothing to preview'
	return 'This is a preview of {}'.format(path)

class SelectFileViewController(ViewController):
	"""docstring for SelectFileViewController"""
	def __init__(self, directory, ext, doc=None, log=None):
		options=sorted(list(find_files(directory,ext)))
		options0 = None
		if len(options) > 0:
			options0 = options[0]
		select = Select(
			title="Select File:",
			value=options0,
			options=options,
			height=40,
			height_policy="fixed",
		)
		select_button = Button(
			label='Select',
			align="end",
			button_type="success",
			width=100,
			width_policy="fixed",
			height=40,
			height_policy="fixed",
		)
		file_preview = TextAreaInput(
			value=preview(options0),
			sizing_mode='stretch_both',
			max_length=2**20,
		)
		view = column(
			row(select, select_button, sizing_mode = 'scale_width',),
			file_preview,
			sizing_mode='stretch_both',
		)
		super(SelectFileViewController, self).__init__(view, doc, log)
		self.select = select
		self.select_button = select_button
		self.on_selected_callback = None
		self.select_button.on_click(self.select_on_click)
		self.file_preview = file_preview

	def on_selected(self, callback):
		self.on_selected_callback = callback

	def select_on_click(self):
		if self.on_selected_callback is None:
			return
		path = self.select.value
		self.on_selected_callback(path)
