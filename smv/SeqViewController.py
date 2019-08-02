from bokeh.layouts import column
from smv.ViewController import ViewController

class SeqViewController(ViewController):
	"""docstring for SeqViewController"""
	def __init__(self, controllers, doc=None, log=None):
		views = [c.view for c in controllers]
		view = column(*views, sizing_mode = 'stretch_both')
		super(SeqViewController, self).__init__(view, doc, log)
		self.controllers = controllers
		self.views = views
		for v in self.views:
			v.visible = False
		self.current = 0

	def next(self):
		if self.current - 1 >= 0:
			self.controllers[self.current-1].hide()
		self.controllers[self.current].show()
		if self.current+1 >= len(self.controllers):
			return
		self.current += 1
