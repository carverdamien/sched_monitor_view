from smv.ViewController import ViewController
from bokeh.layouts import column
from functools import partial
from tornado import gen
from threading import Thread

import dask
import pandas as pd
import numpy as np

from bokeh.plotting import figure
from bokeh.models.widgets import TextInput
from bokeh.models import ColumnDataSource
from bokeh.models.glyphs import Segment
from bokeh.models import Legend, LegendItem
from bokeh.events import LODEnd
from bokeh.models.tools import HoverTool

import datashader as ds
import datashader.transfer_functions as tf
from datashader.bokeh_ext import InteractiveImage

datashader_color=['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5', '#fc8d62', '#8da0cb', '#a6d854', '#ffd92f', '#e5c494', '#ffffb3', '#fb8072', '#fdb462', '#fccde5', '#d9d9d9', '#ccebc5', '#ffed6f']

# Add dummy point because datashader cannot handle emptyframe
def empty_lines():
	df = pd.DataFrame({
		'x0':[0, 1],
		'x1':[0, 1],
		'y0':[0, 1],
		'y1':[0, 1],
		'c':[0, 1],
	})
	df['c'] = df['c'].astype('category')
	return df

def get_image_ranges(FVC):
	xmin = FVC.fig.x_range.start
	xmax = FVC.fig.x_range.end
	ymin = FVC.fig.y_range.start
	ymax = FVC.fig.y_range.end
	w = FVC.fig.plot_width
	h = FVC.fig.plot_height
	return {
		'xmin':xmin,
		'xmax':xmax,
		'ymin':ymin,
		'ymax':ymax,
		'w':w,
		'h':h,
	}

class FigureViewController(ViewController):
	"""docstring for FigureViewController"""
	def __init__(self, 
			x_range=(0,1), # datashader cannot handle 0-sized range
			y_range=(0,1), # datashader cannot handle 0-sized range
			lines=empty_lines(), 
			get_image_ranges=get_image_ranges,
			doc=None,
			log=None,
		):
		self.query = ''
		self.lines = lines
		self.lines_to_render = lines
		self.get_image_ranges = get_image_ranges
		fig = figure(
			x_range=x_range,
			y_range=y_range,
			sizing_mode='stretch_both',
		)
		# fig.add_layout(Legend(click_policy='hide'))
		query_textinput = TextInput(
			title="query",
			sizing_mode="stretch_width",
			value='',
			width=100
		)
		view = column(fig, query_textinput, sizing_mode='stretch_both')
		super(FigureViewController, self).__init__(view, doc, log)
		self.fig = fig
		self.query_textinput = query_textinput
		# Has to be executed before inserting fig in doc
		self.fig.on_event(LODEnd, self.callback_LODEnd)
		# Has to be executed before inserting fig in doc
		self.img = InteractiveImage(self.fig, self.callback_InteractiveImage)
		self.query_textinput.on_change('value', self.on_change_query_textinput)
		assert(len(self.fig.renderers) == 1)
		self.datashader = self.fig.renderers[0]
		self.source = None
		self.segment = None
		self.hovertool = None

	def is_valid_query(self, q):
		# TODO: improve test
		return q is not None and q.strip() != ''

	def on_change_query_textinput(self, attr, old, new):
		if self.is_valid_query(self.query_textinput.value):
			self.query = self.query_textinput.value
			self.update_image()

	def callback_LODEnd(self, event):
		self.update_image()

	@ViewController.logFunctionCall
	def compute_lines_to_render(self, ranges):
		self.lines_to_render = self.lines
		if self.is_valid_query(self.query):
			self.lines_to_render = self.apply_query()
		def target():
			try:
				self.compute_hovertool(ranges)
			except Exception as e:
				print(e)
		Thread(target=target).start()

	@ViewController.logFunctionCall
	def compute_hovertool(self, ranges):
		MAX = 100000.
		xmin = ranges['xmin']
		xmax = ranges['xmax']
		xspatial = "({})|({})|({})".format(
			"x0>={} & x0<={}".format(xmin,xmax),
			"x1>={} & x1<={}".format(xmin,xmax),
			"x0<={} & x1>={}".format(xmin,xmax),
		)
		ymin = ranges['ymin']
		ymax = ranges['ymax']
		yspatial = "({})|({})|({})".format(
			"y0>={} & y0<={}".format(ymin,ymax),
			"y1>={} & y1<={}".format(ymin,ymax),
			"y0<={} & y1>={}".format(ymin,ymax),
		)
		spatial = "({})&({})".format(xspatial, yspatial)
		lines_to_render = self.lines_to_render.query(spatial)
		n = len(lines_to_render)
		if n > MAX:
			frac = MAX/n
			self.log('Sampling hovertool frac={}'.format(frac))
			lines_to_render = lines_to_render.sample(frac=frac)
		else:
			self.log('Full hovertool')
		df = dask.compute(lines_to_render)[0]
		if len(df) > 0:
			@gen.coroutine
			def coroutine(df):
				self.source.data = ColumnDataSource.from_df(df)
			self.doc.add_next_tick_callback(partial(coroutine, df))

	@ViewController.logFunctionCall
	def update_image(self):
		try:
			self._update_image()
		except Exception as e:
			self.log(e)

	def _update_image(self):
		ranges = self.get_image_ranges(self)
		self.compute_lines_to_render(ranges)
		self.img.update_image(ranges)

	@ViewController.logFunctionCall
	def apply_query(self):
		try:
			lines = self.lines.query(self.query)
			if len(lines) == 0:
				raise Exception(
					'QUERY ERROR',
					'{} => len(lines) == 0'.format(self.query)
				)
			return lines
		except Exception as e:
			self.log(e)
		return self.lines

	@ViewController.logFunctionCall
	def callback_InteractiveImage(self, x_range, y_range, plot_width, plot_height, name=None):
		cvs = ds.Canvas(
			plot_width=plot_width, plot_height=plot_height,
			x_range=x_range, y_range=y_range,
		)
		agg = cvs.line(self.lines_to_render,
			x=['x0','x1'], y=['y0','y1'],
			agg=ds.count_cat('c'), axis=1,
		)
		img = tf.shade(agg,min_alpha=255)
		return img

	def plot(self, width, height, lines=empty_lines(), xmin=None, xmax=None, ymin=None, ymax=None):
		if self.doc is not None:
			@gen.coroutine
			def coroutine():
				self._plot(width, height, lines=lines, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
			self.doc.add_next_tick_callback(partial(coroutine))

	@ViewController.logFunctionCall
	def _plot(self, width, height, lines, xmin=None, xmax=None, ymin=None, ymax=None):
		if xmin is None:
			xmin = min(*dask.compute((lines['x0'].min(),lines['x1'].min())))
		if xmax is None:
			xmax = max(*dask.compute((lines['x0'].max(),lines['x1'].max())))
		if ymin is None:
			ymin = min(*dask.compute((lines['y0'].min(),lines['y1'].min())))
		if ymax is None:
			ymax = max(*dask.compute((lines['y0'].max(),lines['y1'].max())))
		self.fig.x_range.start = xmin
		self.fig.x_range.end = xmax
		self.fig.y_range.start = ymin
		self.fig.y_range.end = ymax
		self.fig.plot_width = width
		self.fig.plot_height = height
		self.lines = lines
		self.source = ColumnDataSource({k:[] for k in lines.columns})
		glyph = Segment(
				x0='x0',
				x1='x1',
				y0='y0',
				y1='y1',
				line_alpha=0,
			)
		self.segment = self.fig.add_glyph(self.source, glyph)
		self.update_image()
		if self.hovertool is None:
			tooltips = [
				("(x,y)","($x, $y)"),
			]
			for k in lines.columns:
				tooltips.append((k,"@"+str(k)))
			self.hovertool = HoverTool(tooltips = tooltips)
			self.fig.add_tools(self.hovertool)
			# self.fig.legend.items = [LegendItem(label='Datashader', renderers=[self.datashader], index=0)]
		pass
