#!/usr/bin/python
# -*- coding: utf-8 -*-
import getpass
import socket
import codecs
from rime.core import commands as rime_commands
from rime.core import targets
from rime.core import taskgraph

def SafeUnicode(s):
  if not isinstance(s, unicode):
    s = s.decode('utf-8')
  return s
def tcount(u):
  return sum(1 if ord(c) < 127 else 2 for c in u)

class Project(targets.registry.Project):
  def PreLoad(self, ui):
    super(Project, self).PreLoad(ui)
    self.rstfy_config_defined = False
    def _rstfy_config(path, title):
      self.rstfy_config_defined = True
      self.rstfy_config_path = path
      self.rstfy_config_title = SafeUnicode(title)
    self.exports['rstfy_config'] = _rstfy_config

  @taskgraph.task_method
  def rstfy(self, ui):
    if not self.rstfy_config_defined:
      ui.errors.Error(self, 'rstfy_config() is not defined.')
      yield None
    rst = yield self._generateRST(ui)
    with codecs.open(self.rstfy_config_path, "w", "utf-8") as f:
      f.write(rst)
    ui.console.PrintAction('OUTPUT', None, self.rstfy_config_path)
    yield None

  @taskgraph.task_method
  def _generateRST(self, ui):
    yield self.Clean(ui)
    username = getpass.getuser()
    hostname = socket.gethostname()
    titlecount = tcount((self.rstfy_config_title)) + 4
    rst = u"=" * titlecount + u"\n"
    rst += self.rstfy_config_title + u"\n"
    rst += u"=" * titlecount + u"\n"
    rst += u"""
このセクションは rstfy plugin により自動生成されています．
(run by %(username)s@%(hostname)s)

""" % {'username': username, 'hostname': hostname}
    results = yield taskgraph.TaskBranch([
        self._generateRowInfo(problem, ui)
        for problem in self.problems])
    rst += self._joinTable(results)
    yield rst
  
  def _joinTable(self, rows):
    maxlen = [4, 4, 4, 8, 4, 4, 4]
    for r in rows:
      for i, s in enumerate(r):
        maxlen[i] = max(maxlen[i], tcount(s))
    rst = u""
    partition = u"+" + u"+".join([u"-" * (n + 2) for n in maxlen]) + u"+\n"
    rst += partition
    rst += "|" + "|".join([" %s " % s + " " * (maxlen[i] - tcount(s)) for i, s in enumerate((u"正答", u"担当", u"正答", u"想定誤答", u"入力", u"出力", u"入検"))]) + "|\n"
    rst += u"+" + u"+".join([u"=" * (n + 2) for n in maxlen]) + u"+\n"
    for r in rows:
      rst += "|" + "|".join([" %s " % s + " " * (maxlen[i] - tcount(s)) for i, s in enumerate(r)]) + "|\n"
      rst += partition
    return rst

  @taskgraph.task_method
  def _generateRowInfo(self, problem, ui):
    title = SafeUnicode(problem.title) or 'No Title'
    assignees = problem.assignees
    if isinstance(assignees, list):
      assignees = ','.join(assignees)
    assignees = SafeUnicode(assignees)
    # Fetch test results.
    results = yield problem.Test(ui)
    # Get various information about the problem.
    num_solutions = len(results)
    correct_solution_results = [result for result in results
                                if result.solution.IsCorrect()]
    num_corrects = len(correct_solution_results)
    corrects = unicode(num_corrects)
    num_tests = len(problem.testset.ListTestCases())
    inputs = unicode(num_tests)
    num_incorrects = num_solutions - num_corrects
    incorrects = unicode(num_incorrects)
    num_accepts = len([result for result in correct_solution_results
                      if result.expected])
    outputs = u"%d/%d" % (num_accepts, num_corrects)
    if problem.testset.validators:
      validators = u"OK"
    else:
      validators = u"NO"
    # Done
    yield (title, assignees, corrects, incorrects, inputs, outputs, validators)

class Problem(targets.registry.Problem):
  def PreLoad(self, ui):
    super(Problem, self).PreLoad(ui)
    base_problem = self.exports['problem']
    def _problem(assignees=None, **kwargs):
      if assignees:
        self.assignees = assignees
      else:
        ui.console.PrintWarning('assignees was not set in %s PROBLEM' % kwargs['title'])
        self.assignees = ""
      return base_problem(**kwargs)
    self.exports['problem'] = _problem

class RSTfy(rime_commands.CommandBase):
  def __init__(self, parent):
    super(RSTfy, self).__init__(
      'rstfy',
      '',
      'Upload test results to reStructuredText. (RSTfy plugin)',
      '',
      parent)

  def Run(self, obj, args, ui):
    if args:
      ui.console.PrintError('Extra argument passed to RSTfy command!')
      return None

    if isinstance(obj, Project):
      return obj.rstfy(ui)

    ui.console.PrintError('RSTfy is not supported for the specified target.')
    return None

targets.registry.Override('Project', Project)
targets.registry.Override('Problem', Problem)

rime_commands.registry.Add(RSTfy)
