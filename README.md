rime-rstfy-plugin
====================

[rime](https://github.com/nya3jp/rime) plugin for generating reStructuredText

## at PROJECT

	import os
	
	## You can load plugins here.
	use_plugin('rstfy')
	
	autorst = os.path.join("..", "..", "problems", "source", "auto.rst")
	rstfy_config(path=autorst, title="automatic")

## at PROBLEM

	problem(title = "Problem A",
	        id = "A",
	        time_limit = 1.0,
	        assignees = "assignees"
	        )

