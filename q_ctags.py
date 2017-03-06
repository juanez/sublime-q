import sublime, sublime_plugin

# class Qtags




def plugin_loaded():

    #stash our list in the sublime module. it aint pretty ;)
    sublime.qtags_list_functions = []
    print("qtags.py - plugin loaded!")
    with open('Z://dev/sysmon/tags') as f:
        for line in f:
            name = (line.split('\t'))[0:1]

            sublime.qtags_list_functions.append([name[0],name[0]])
    # print(sublime.qtags_list_functions[6:])
    sublime.qtags_list_functions = sublime.qtags_list_functions[6:] # cut out the ctags "header"