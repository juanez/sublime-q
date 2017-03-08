import sublime, sublime_plugin
from . import Settings as S

def plugin_loaded():

    #stash our list in the sublime module. it aint pretty ;)
    sublime.qtags_list_functions = []
    print("q_ctags.py - plugin loaded!")
    file=S.Settings().get('q_ctags_file')
    with open(file) as f:
        for line in f:
            # name = (line.split('\t'))[0:1]
            
            tag = tuple(line.split('\t'))[0:2]
            print(tag[1])

            if tag[1].endswith('.q'):
                sublime.qtags_list_functions.append(tag)
    # print(sublime.qtags_list_functions[6:])
    # sublime.qtags_list_functions = sublime.qtags_list_functions[6:] # cut out the ctags "header"
    print('q_ctags list:')
    print(sublime.qtags_list_functions)