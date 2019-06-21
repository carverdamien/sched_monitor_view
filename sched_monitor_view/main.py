# External imports
from bokeh.layouts import row, column
from bokeh.plotting import curdoc, figure
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from bokeh.models.widgets import Select, CheckboxGroup, Button, Dropdown, ColorPicker, RangeSlider, Slider, TextAreaInput, RadioButtonGroup, DataTable, TableColumn
from bokeh.models import ColumnDataSource
from tornado import gen
from functools import partial
# Internal imports
import feeds.fspath
import state

######################################################
################ Build the components ################
######################################################
doc = curdoc()
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
OBJECTS[USER_VIEW].extend([select_hdf5,button_add_or_rm_hdf5])
################ JSON View ################
textareainput_json = TextAreaInput(visible=False)
button_import_json = Button(
	label="Import",
	align="end",
    button_type="success",
    width_policy="min",
    visible=False,
)
OBJECTS[JSON_VIEW].extend([textareainput_json, button_import_json])
################ Data View ################
source = ColumnDataSource()
datatable = DataTable(source=source, visible=False)
OBJECTS[DATA_VIEW].extend([datatable])
################ Plot View ################
figure_plot = figure(
    sizing_mode='stretch_both',
    tools="xpan,reset,save,xwheel_zoom,hover",
    active_scroll='xwheel_zoom',
    output_backend="webgl",
    visible=False,
)
OBJECTS[PLOT_VIEW].extend([figure_plot])
###########################################
################ Add feeds ################
###########################################
@gen.coroutine
def coroutine_fspath(l):
    select_hdf5.options = l
    select_hdf5.value = l[0]
def callback_fspath(l):
    doc.add_next_tick_callback(partial(coroutine_fspath, l))
feeds.fspath.feed('./raw', '.hdf5',callback_fspath).start()
###################################################
################ Add interactivity ################
###################################################
################ TABS View ################
def on_click_radiobuttongroup_tab(new):
	selected = radiobuttongroup_tab.active
	for f in UPDATES[selected]:
		f()
	for view in TABS:
		for o in OBJECTS[view]:
			if view == selected:
				o.visible = True
			else:
				o.visible = False
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
	select_hdf5.disabled = False
	button_add_or_rm_hdf5.disabled = False
	update_button_add_or_rm_hdf5()
def on_click_loadhdf5(new):
	path = select_hdf5.value
	if state.hdf5_is_loaded(path):
		state.unload_hdf5(path)
		update_button_add_or_rm_hdf5()
	else:
		select_hdf5.disabled = True
		button_add_or_rm_hdf5.disabled = True
		state.load_hdf5(path, load_done)
button_add_or_rm_hdf5.on_click(on_click_loadhdf5)
UPDATES[USER_VIEW].extend([update_button_add_or_rm_hdf5])
################ JSON View ################
def from_json_done():
	update_button_import_json()
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
	value = state.to_json()
	textareainput_json.value = value
def on_change_textareainput_json(attr, old, new):
	update_button_import_json()
textareainput_json.on_change('value', on_change_textareainput_json)
UPDATES[JSON_VIEW].extend([
	update_textareainput_json,
	update_button_import_json,
])
################ Data View ################
def update_dataview():
	state.update_source(source)
	state.update_table(datatable)
UPDATES[DATA_VIEW].extend([update_dataview])
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
		sizing_mode = 'scale_width',
    ),
    textareainput_json,
    datatable,
    figure_plot,
    sizing_mode = 'stretch_both',
)
doc.add_root(root)
