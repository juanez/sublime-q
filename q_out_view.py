import sublime, sublime_plugin
from . import q_chain

#show_q_output


class QOutViewCommand(q_chain.QChainCommand):

    # globals for now..
    qoutviewname = "Q_OUTPUT_VIEW"
    qoutview = None
    def do(self, edit, input=None):
        input = input.replace('\r', '')
        ws = sublime.windows()
        for w in ws:
            for v in w.views():
                # print(v.name())
                if v.name() == QOutViewCommand.qoutviewname:
                    QOutViewCommand.qoutview = v
      

        if None == QOutViewCommand.qoutview:
            QOutViewCommand.qoutview = self.view.window().new_file()
            QOutViewCommand.qoutview.set_name(QOutViewCommand.qoutviewname)


        try:
            QOutViewCommand.qoutview.set_syntax_file("Packages/sublime-q/syntax/q_output.tmLanguage")
        except Exception:
            print ("Unable to load syntax file: ", syntax_file)
 
        QOutViewCommand.qoutview.settings().set("word_wrap", False)
        QOutViewCommand.qoutview.set_read_only(False)
        QOutViewCommand.qoutview.insert(edit, QOutViewCommand.qoutview.size(), input)
        QOutViewCommand.qoutview.set_read_only(True)

        return '' #return something so that the chain will continue

# class QHideOutViewCommand(q_chain.QChainCommand):
#    def do(self, edit, input=None):
#        self.view.window().run_command("hide_panel", {"panel": "output.q"})
#        return ''   #return something so q_chain can continue
    