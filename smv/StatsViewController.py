from smv.ViewController import ViewController
from bokeh.models.widgets import DataTable
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
import pandas as pd
from tornado import gen
from functools import partial
from threading import Lock, Thread

class StatsViewController(ViewController):
	"""docstring for StatsViewController"""
	def __init__(self, **kwargs):
		# Provide source. (Do not use defaut)
		self.lock = Lock()
		self.source = kwargs.get('source', ColumnDataSource({}))
		self.table = DataTable(
			source=self.source,
			sizing_mode='stretch_both',
			width_policy='max',
		)
		view = self.table
		super(StatsViewController, self).__init__(view, **kwargs)


	##########################
	# Non-blocking Functions #
	##########################

	def update_stats(self, **kwargs):
		fname = self.update_stats.__name__
		if not self.lock.acquire(False):
			self.log('Could not acquire ock in {}'.format(fname))
			return
		def target(**kwargs):
			try:
				data = kwargs['data']
				df = self.compute_stats(data)
				self.update_source(df)
			except Exception as e:
				self.log('Exception({}) in {}:{}'.format(type(e), fname, e))
				self.log(traceback.format_exc())
				self.set_failed()
			else:
				self.lock.release()
		Thread(target=target, kwargs=kwargs).start()

	####################################
	# Functions modifying the document #
	####################################

	def update_source(self, df):
		@gen.coroutine
		def coroutine(df):
			self.table.columns = [TableColumn(field=c, title=c) for c in df.columns]
			self.source.data = ColumnDataSource.from_df(df)
		if self.doc:
			self.doc.add_next_tick_callback(partial(coroutine, df))

	###############################
	# Compute intensive functions #
	###############################

	def compute_stats(self, data):
		# TODO
		df = pd.DataFrame({'a':[0,1],'b':[2,3]})
		return df