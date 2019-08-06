# External imports
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models.tools import PanTool, ResetTool, SaveTool, WheelZoomTool
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from bokeh.models.widgets import Select, CheckboxGroup, Button, Dropdown, ColorPicker, RangeSlider, Slider, TextAreaInput, RadioButtonGroup, DataTable, TableColumn, TextInput, Paragraph
from bokeh.models import ColumnDataSource
from tornado import gen
from functools import partial
# Internal imports
import sched_monitor_view.feeds.fspath as fspath
from sched_monitor_view.state import State
import sched_monitor_view.Types as Types
from sched_monitor_view.bokehext.UploadFile import UploadFile

def modify_doc(doc):
	######################################################
	################ Build the components ################
	######################################################
	USER_VIEW = 0
	JSON_VIEW = 1
	DATA_VIEW = 2
	PLOT_VIEW = 3
	TABS        = [   USER_VIEW,   JSON_VIEW,   DATA_VIEW,   PLOT_VIEW, ]
	labels_TABS = [ "User View", "JSON View", "Data View", "Plot View", ]
	OBJECTS = {
		k:[]
		for k in TABS
	}
	UPDATES = {
		k:[]
		for k in TABS
	}
	################ TABS View ################
	radiobuttongroup_tab = RadioButtonGroup(
		labels=labels_TABS,
	)
	################ lim bar ################
	select_lim_mode = Select(
		title="Mode",
		options=["index","time"],
		value="index",
		width=60,
		sizing_mode="fixed",
		visible=False,
	)
	textinput_lim_witdh = TextInput(
		title="Width",
		sizing_mode="fixed",
		value='1',
		width=100,
		visible=False,
	)
	slider_lim_cursor = Slider(
		align="center",
	    start=0,
	    end=1,
	    value=0,
	    step=1,
	    width_policy="max",
	    sizing_mode="scale_width",
	    callback_policy="mouseup",
	    visible=False,
	)
	button_fit = Button(
		label="Fit",
	    align="end",
	    button_type="success",
	    width_policy="min",
	    visible=False,
	)
	################ User View ################
	select_hdf5 = Select(
	    title ='Path:',
	    sizing_mode="fixed",
	    visible=False,
	)
	button_add_or_rm_hdf5 = Button(
	    align="end",
	    button_type="success",
	    width_policy="min",
	    visible=False,
	)
	paragraph_info = Paragraph()
	OBJECTS[USER_VIEW].extend([select_hdf5,button_add_or_rm_hdf5,paragraph_info])
	################ JSON View ################
	textareainput_json = TextAreaInput(
		visible=False,
		max_length=2**20,
	)
	button_import_json = Button(
		label="Import",
		align="end",
	    button_type="success",
	    width_policy="min",
	    visible=False,
	)
	upload_json = UploadFile(
		label="Upload",
		align="end",
		button_type="success",
		width_policy="min",
		visible=False,
	)
	OBJECTS[JSON_VIEW].extend([textareainput_json, button_import_json, upload_json.button])
	################ Data View ################
	datatable = DataTable(source=ColumnDataSource(), visible=False)
	OBJECTS[DATA_VIEW].extend([datatable, select_lim_mode, slider_lim_cursor, textinput_lim_witdh, button_fit])
	################ Plot View ################
	figure_plot = figure(
		x_range=(0,1), # datashader cannot handle 0-sized range
		y_range=(0,1), # datashader cannot handle 0-sized range
	)
	figure_plot.sizing_mode='stretch_both'
	active_scroll = WheelZoomTool(dimensions="width")
	tools = [
		PanTool(dimensions="width"),
		# ResetTool(),
		SaveTool(),
		active_scroll,
	]
	figure_plot.tools = tools
	figure_plot.toolbar.active_scroll = active_scroll
	figure_plot.output_backend="webgl"
	figure_plot.visible=False
	figure_plot.add_layout(Legend(click_policy='hide'))
	OBJECTS[PLOT_VIEW].extend([figure_plot, select_lim_mode, slider_lim_cursor, textinput_lim_witdh, button_fit])
	################ State ################
	state = State(doc, datatable, figure_plot)
	###########################################
	################ Add feeds ################
	###########################################
	@gen.coroutine
	def coroutine_fspath(l):
	    select_hdf5.options = l
	    select_hdf5.value = l[0]
	def callback_fspath(l):
	    doc.add_next_tick_callback(partial(coroutine_fspath, l))
	fspath.feed('./raw', '.hdf5',callback_fspath).start()
	###################################################
	################ Add interactivity ################
	###################################################
	################ lim bar ################
	def update_lim_bar():
		mode, cursor, width, end = state.get_truncate()
		select_lim_mode.value = mode
		slider_lim_cursor.value = 0
		slider_lim_cursor.end = end
		slider_lim_cursor.value = cursor
		textinput_lim_witdh.value = str(width)
	def on_change_lim(attr, old, new):
		mode = select_lim_mode.value
		cursor = slider_lim_cursor.value
		try:
			width = int(textinput_lim_witdh.value)
			cursor, width = state.truncate(mode, cursor, width)
		except Exception as e:
			print(e)
	def on_change_select_lim_mode(attr, old, new):
		mode = select_lim_mode.value
		cursor = slider_lim_cursor.value
		try:
			width = int(textinput_lim_witdh.value)
			cursor, width = state.truncate(mode, cursor, width)
			update_lim_bar()
		except Exception as e:
			print(e)
	def on_click_button_fit(new):
		state.fit()
	button_fit.on_click(on_click_button_fit)
	select_lim_mode.on_change('value', on_change_select_lim_mode)
	slider_lim_cursor.on_change('value_throttled', on_change_lim)
	textinput_lim_witdh.on_change('value', on_change_lim)
	################ TABS View ################
	def on_click_radiobuttongroup_tab(new):
		selected = radiobuttongroup_tab.active
		for view in TABS:
			for o in OBJECTS[view]:
				o.visible = False
		for o in OBJECTS[selected]:
			o.visible = True
		for f in UPDATES[selected]:
			f()
		pass
	radiobuttongroup_tab.on_click(on_click_radiobuttongroup_tab)
	################ User View ################
	def update_button_add_or_rm_hdf5():
		path = select_hdf5.value
		if state.hdf5_is_loaded(path):
			button_add_or_rm_hdf5.label = 'rm'
			button_add_or_rm_hdf5.button_type = 'warning'
		else:
			button_add_or_rm_hdf5.label = 'add'
			button_add_or_rm_hdf5.button_type = 'success'
	def on_change_select_hdf5(attr, old, new):
	    update_button_add_or_rm_hdf5()
	select_hdf5.on_change('value', on_change_select_hdf5)
	def load_done():
		update_lim_bar()
		select_hdf5.disabled = False
		button_add_or_rm_hdf5.disabled = False
		update_button_add_or_rm_hdf5()
	def on_click_loadhdf5(new):
		path = select_hdf5.value
		if state.hdf5_is_loaded(path):
			select_hdf5.disabled = True
			button_add_or_rm_hdf5.disabled = True
			state.unload_hdf5(path)
			update_lim_bar()
			update_button_add_or_rm_hdf5()
			select_hdf5.disabled = False
			button_add_or_rm_hdf5.disabled = False
		else:
			select_hdf5.disabled = True
			button_add_or_rm_hdf5.disabled = True
			state.load_hdf5(path, load_done)
	button_add_or_rm_hdf5.on_click(on_click_loadhdf5)
	def update_paragraph_info():
		paragraph_info.text = "{}{}{}{}".format(
			'\n'.join(state.description),
			[(i,Types.EVENT[i]) for i in range(len(Types.EVENT))],
			[(state.perf_event[k]["id"],hex(state.perf_event[k]["config1"])) for k in state.perf_event],
			[
				("0x063bc0","LLC_MISS.REMOTE_DRAM"),
				("0x060400","LLC_MISS.LOCAL_DRAM"),
			]
		)
		pass
	UPDATES[USER_VIEW].extend([update_button_add_or_rm_hdf5, update_paragraph_info])
	################ JSON View ################
	def from_json_done():
		update_button_import_json()
		update_lim_bar()
	def on_click_button_import_json(new):
		new_state = textareainput_json.value
		button_import_json.disabled = True
		state.from_json(new_state, from_json_done)
	button_import_json.on_click(on_click_button_import_json)
	def update_button_import_json():
		new_state = textareainput_json.value
		if state.is_valid(new_state):
			button_import_json.disabled = False
		else:
			button_import_json.disabled = True
	def update_textareainput_json():
		value = state.to_pretty_json()
		textareainput_json.value = value
	def on_change_textareainput_json(attr, old, new):
		update_button_import_json()
	def on_click_button_upload_json(fname, fio):
		textareainput_json.value = fio.read().decode()
		pass
	upload_json.callback = on_click_button_upload_json
	textareainput_json.on_change('value', on_change_textareainput_json)
	UPDATES[JSON_VIEW].extend([
		update_textareainput_json,
		update_button_import_json,
	])
	################ Data View ################
	################ Plot View ################
	UPDATES[PLOT_VIEW].extend([state.update_datashader])
	#####################################################
	################ Assamble components ################
	#####################################################
	root = column(
	    row(
	        radiobuttongroup_tab,
	        sizing_mode = 'scale_width',
	    ),
	    row(
			select_hdf5,
			button_add_or_rm_hdf5,
			button_import_json,
			upload_json.button,
			sizing_mode = 'scale_width',
	    ),
	    paragraph_info,
	    textareainput_json,
	    datatable,
	    figure_plot,
	    row(select_lim_mode, slider_lim_cursor, textinput_lim_witdh, button_fit, sizing_mode='scale_width'),
	    sizing_mode = 'stretch_both',
	)
	doc.add_root(root)