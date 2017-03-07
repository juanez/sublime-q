import sublime, sublime_plugin, inspect
from . import QCon as Q
from . import q_send as QS
from . import Settings as S

import re
import time
from os.path import basename

# limits to prevent bogging down the system
MIN_WORD_SIZE = 3
MAX_WORD_SIZE = 50

MAX_VIEWS = 20
MAX_WORDS_PER_VIEW = 100
MAX_FIX_TIME_SECS_PER_VIEW = 0.01

class QEvent(sublime_plugin.EventListener):
	settings = S.Settings()

	#update connection status when view is activated
	def on_activated_async(self, view):
		if (view.score_selector(0, 'source.q') != 0):				#only activated for q
			# use associated Q Connection
			qcon = Q.QCon.loadFromView(view)
			if qcon:
				view.set_status('q', qcon.status())



	def on_query_completions(self, view, prefix, locations):
		words=[]

		# Limit number of views but always include the active view. This
		# view goes first to prioritize matches close to cursor position.
		other_views = [v for v in sublime.active_window().views() if v.id != view.id]
		views = [view] + other_views
		views = views[0:MAX_VIEWS]

		"""
		for v in views:
			if len(locations) > 0 and v.id == view.id:
				view_words = view.extract_completions(prefix, locations[0])
			else:
				view_words = v.extract_completions(prefix)
			view_words = filter_words(view_words)
			view_words = fix_truncation(v, view_words)
			words += [(w, v) for w in view_words]
		"""
		
		view_words = view.extract_completions(prefix,locations[0]);
		view_words = filter_words(view_words)
		view_words = fix_truncation(view, view_words)
		words += [(w, view) for w in view_words]


		matches = []
		for w, v in words:
			# print("ITER:")
			trigger = w
			contents = w.replace('$', '\\$')
			# print(trigger)
			if v.id != view.id and v.file_name():
				trigger += '\t(%s)' % basename(v.file_name())
				# print(trigger)
			matches.append((trigger, contents))

		print(matches)

		allsyms = list(sublime.qtags_list_functions) # make a copy. super inefficient i suppose.. lets see how it works out
		# print(sublime.qtags_list_functions)
		# for word in view.extract_completions(prefix):
		for sym in allsyms:
			if prefix in sym[0]:
				matches.append((sym[0]+'\t(%s)' % sym[1],sym[0]))

		print(matches)
		return matches


def filter_words(words):
	words = words[0:MAX_WORDS_PER_VIEW]
	return [w for w in words if MIN_WORD_SIZE <= len(w) <= MAX_WORD_SIZE]


# keeps first instance of every word and retains the original order
# (n^2 but should not be a problem as len(words) <= MAX_VIEWS*MAX_WORDS_PER_VIEW)
def without_duplicates(words):
	result = []
	used_words = []
	for w, v in words:
		if w not in used_words:
			used_words.append(w)
			result.append((w, v))
	return result


# Ugly workaround for truncation bug in Sublime when using view.extract_completions()
# in some types of files.
def fix_truncation(view, words):
	fixed_words=[]
	start_time=time.time()

	for i, w in enumerate(words):
		#The word is truncated if and only if it cannot be found with a word boundary before and after

		# this fails to match strings with trailing non-alpha chars, like
		# 'foo?' or 'bar!', which are common for instance in Ruby.
		match = view.find(r'\b' + re.escape(w) + r'\b', 0)
		truncated = is_empty_match(match)
		if truncated:
			#Truncation is always by a single character, so we extend the word by one word character before a word boundary
			extended_words = []
			view.find_all(r'\b' + re.escape(w) + r'\w\b', 0, "$0", extended_words)
			if len(extended_words) > 0:
				fixed_words += extended_words
			else:
				# to compensate for the missing match problem mentioned above, just
				# use the old word if we didn't find any extended matches
				fixed_words.append(w)
		else:
			#Pass through non-truncated words
			fixed_words.append(w)

		# if too much time is spent in here, bail out,
		# and don't bother fixing the remaining words
		if time.time() - start_time > MAX_FIX_TIME_SECS_PER_VIEW:
			return fixed_words + words[i+1:]

	return fixed_words


if sublime.version() >= '3000':
	def is_empty_match(match):
		return match.empty()
else:
	def is_empty_match(match):
		return match is None
	


		# for sym in view.symbols():
		#	allsyms.insert(0,[sym[1],sym[1]])
		# compl1 = (allsyms)
		
		# get words from current buffer/view here for auto_completions
		# view_words = v.extract_completions(prefix, locations[0])
		# print(view.extract_completions(prefix))



		


class QUpdateCompletionsCommand(QS.QSendRawCommand):
	settings = S.Settings()

	def query(self):
		t = '(tables `.)!cols each tables `.'
		v = '(system "v") except system"a"'
		f = 'system "f"'
		q = '1 _ key `.q'
		ns = "raze {(enlist x)!enlist 1 _ key x} each `$\".\",' string except[;`q] key `"
		return '`t`v`f`q`ns!({0}; {1}; {2}; {3}; {4})'.format(t, v, f, q, ns)

	def send(self, con, s):
		print("updating completions??")
		if not self.settings.get('use_completion'):
			return
		try:
			q = con.q
			q.open()
			res = q(self.query())
			#print(res)
			compl = []

			tb = res[b't']
			for x in tb.iteritems():
				t = x[0].decode('utf-8')
				compl.append((t + '\tTable', t))
				for c in x[1]:
					c = c.decode('utf-8')
					#print(c)
					compl.append((t + '\t' + c, c))
					compl.append((c + '\t' + t, c))

			compl.extend(self.makeCompletions(res[b'v'], 'Variable'))
			compl.extend(self.makeCompletions(res[b'f'], 'Function'))          
			compl.extend(self.makeCompletions(res[b'q'], 'q'))       
			compl.extend(self.makeCompletions(['select', 'from', 'update', 'delete'], 'q'))       

			ns = res[b'ns']
			for x in ns.iteritems():
				n = x[0].decode('utf-8')
				compl.append((n + '\tNamespace', n[1:]))
				for c in x[1]:
					c = c.decode('utf-8')
					#print(c)
					f = n + '.' + c
					compl.append((f + '\t' + n, f[1:]))

			self.view.settings().set('q_compl', compl)
		finally:
			q.close()

	def makeCompletions(self, l, t):
		out = []
		for x in l:
			#v = x.decode('utf-8')
			v = self.decode(x)
			out.append((v + '\t' + t, v))
		return out

"""
	def on_query_completions(self, view, prefix, locations):
		if not view.match_selector(locations[0], "source.q") or not self.settings.get('use_completion'):
			return []

		print("on_query_completions!")
		compl = view.settings().get('q_compl')

		# print(view.settings())
		allsyms = list(sublime.qtags_list_functions) # make a copy. super inefficient i suppose.. lets see how it works out
		print(sublime.qtags_list_functions)
		# for word in view.extract_completions(prefix):
		for word in view.extract_completions(prefix, locations[0]):
			print(word)
			allsyms.insert(0,[word,word])

		return allsyms
"""