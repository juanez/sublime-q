import sublime
import sublime_plugin

from .qpython.qtype import QException
from socket import error as socket_error
import numpy

from . import q_chain
from . import QCon as Q

class QSendRawCommand(q_chain.QChainCommand):

    def do(self, edit=None, input=None):
        con = Q.QCon.loadFromView(self.view)
        if con:
            return self.send(con, input)
        else:
            #connect first
            sublime.message_dialog('Sublime-q: Choose your q connection first!')
            self.view.window().run_command('show_connection_list')
   
    def send(self, con, s):
        try:
            q = con.q
            q.open()
            res = q(s)
            res = self.decode(res)
        except QException as e:
            res = "error: `" + self.decode(e) + '\r\n'
        except socket_error as serr:
            sublime.error_message('Sublime-q cannot to connect to \n"' + con.h() + '"\n\nError message: ' + str(serr))
            raise serr
        finally:
            q.close()

        self.view.set_status('q', con.status())
        
        #return itself if query is define variable or function
        if res is None:
            res = s
        return res

    def decode(self, s):
        if type(s) is bytes or type(s) is numpy.bytes_:
            return s.decode('utf-8')
        elif type(s) is QException:
            return str(s)[2:-1] #extract error from b'xxx'
        else:
            return str(s)

class QSendCommand(QSendRawCommand):
    def do(self, edit=None, input=None):
        if (input[0] == "\\"):
            input = "value\"\\" + input + "\""
        input = ".Q.s .st.tmp:" + input  #save to temprary result, so we can get dimension later
        return super().do(input=input)

class QSendJsonCommand(QSendRawCommand):
    def do(self, edit=None, input=None):
        if (input[0] == "\\"):
            input = "value\"\\" + input + "\""

        input = ".j.j .st.tmp:" + input  #save to temprary result, so we can get dimension later
        return super().do(input=input)

class QSendTypeCommand(QSendCommand):
    def do(self, edit=None, input=None):
        input = "{$[.Q.qt x;meta x;100h=type x;value x;.Q.ty each x]} " + input
        return super().do(input=input)

class QSendEnvCommand(QSendCommand):
    def do(self, edit=None, input=None):
        input = '((enlist `ns)!(enlist(key `) except `q`Q`h`j`o)),{(`$/:x )! system each x } \"dvabf\"'
        return super().do(input=input)

class QSendMemCommand(QSendCommand):
    def do(self, edit=None, input=None):
        input = '.Q.w[]'
        return super().do(input=input)

class QSendTableCommand(QSendCommand):
    def do(self, edit=None, input=None):
        input = '(tables `.)!cols each tables `.'
        return super().do(input=input)
