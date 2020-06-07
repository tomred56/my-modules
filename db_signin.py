'''
Sign in to mariadb


'''
__version_info__ = (0, 0, 1)
__version__ = '.'.join(map(str, __version_info__))

import pymysql.cursors
import wxf_dialog

class SignInDialog(wxf_dialog.db_sign_in):
    
    def __init__(self, parent, db_details, db_tables, status):
        super().__init__(parent)
        self.db_details = db_details
        self.db_tables = db_tables
        self.status = status
        self.activity = None
        if self.status & CX_CONNECTED:
            self.b_disconnect.Enable()
            self.b_connect.Disable()
            self.b_test.Disable()
        else:
            self.status = CX_FAILED
            self.b_connect.Enable()
            self.b_disconnect.Disable()
            self.b_test.Enable()
        self.user_name.SetValue(db_details['user'])
        self.use_db.SetValue(db_details['name'])
        self.host_name.SetValue(db_details['host'])
        self.password.SetValue('')
        self.message1.SetValue('')
        # self.message0.Hide()
        # self.message1.Hide()
        self.progress.Hide()
        # self.SetSizerAndFit(self.top_sizer)
        self.Raise()

    def select_db(host='', use_db='', user='', password=''):
        message = 'connection successful'
        is_valid = True
        db_connect = None
        try:
            db_connect = pymysql.connect(host=f'{host}',
                                         user=f'{user}',
                                         password=f'{password}',
                                         db=f'{use_db}',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
        
        except (pymysql.err.InterfaceError, pymysql.err.InternalError, pymysql.err.IntegrityError,
                pymysql.err.ProgrammingError) as e:
            message = f"could not initialise database:\nsql error {e.args}"
            is_valid = False
        except Exception as exc:
            message = f"could not initialise database:\ngeneral error {exc.args}"
            is_valid = False
        
        return is_valid, message, db_connect


    def on_test_button(self, event):
            self.activity = 'test'
            if self.validated():
                is_valid, message, database = select_db(host=self.host_name.GetValue(),
                                                           use_db=self.use_db.GetValue(),
                                                           user=self.user_name.GetValue(),
                                                           password=self.password.GetValue())
                if is_valid:
                    database.close()
                    self.send_message(CX_CONNECTED, 'connection works')
                    self.status = CX_DISCONNECTED
                else:
                    self.send_message(CX_FAILED, f'error connecting\n{message}')
                    self.status = CX_FAILED
            else:
                self.send_message(CX_FAILED, f'name, password (if required), host, and database must be entered')
    
    def on_connect_button(self, event):
        self.activity = 'connect'
        if self.validated():
            is_valid, message, database = select_db(host=self.host_name.GetValue(),
                                                       use_db=self.use_db.GetValue(),
                                                       user=self.user_name.GetValue(),
                                                       password=self.password.GetValue())
            if is_valid:
                self.db_details['db'] = database
                self.db_details['host'] = self.host_name.GetValue()
                self.db_details['name'] = self.use_db.GetValue()
                self.db_details['user'] = self.user_name.GetValue()
                db.get_structure(database)
                self.progress.SetRange(len(db._T_STRUCTURE))
                self.progress.SetValue(0)
                self.progress.Show()
                self.Layout()
                # self.SetSizerAndFit(self.top_sizer)
                for table in db._T_STRUCTURE.keys():
                    self.db_tables[table] = db.DataTables(database, table)
                    # self.db_tables[table].process()
                    self.progress.SetValue(self.progress.GetValue() + 1)
                self.progress.Hide()
                self.status = CX_CONNECTED
                self.close_dialog()
            else:
                self.send_message(CX_FAILED, f'error connecting\n{message}')
                self.status = CX_FAILED
        else:
            self.send_message(CX_FAILED, f'name, host and database must be entered')
    
    def on_disconnect_button(self, event):
        self.activity = 'disconnect'
        try:
            self.db_details['db'].close()
        finally:
            self.db_tables = {}
            self.db_details['db'] = None
            self.status = CX_DISCONNECTED
            self.b_connect.Enable()
            self.b_disconnect.Disable()
            self.b_test.Enable()
            self.send_message(CX_FAILED, f'not connected')
    
    def validated(self):
        is_valid = True
        if not self.user_name.GetValue() or not self.host_name.GetValue() or not self.use_db.GetValue():
            self.status = CX_FAILED
            is_valid = False
        return is_valid
    
    def send_message(self, status, message):
        if status == CX_CONNECTED:
            self.message1.SetForegroundColour(wx.GREEN)
            # self.message0.Hide()
        else:
            self.message1.SetForegroundColour(wx.RED)
            # self.message0.Show()
        self.message1.Show()
        self.message1.SetValue(message)
        # self.message1.Layout()
        # self.message_sizer.Layout()
        self.Layout()
        # self.SetSizerAndFit(self.top_sizer)
    
    def on_left_dclick(self, event):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.message1.GetLabelText()))
            wx.TheClipboard.Close()
    
    def on_cancel_button(self, event):
        self.close_dialog()
    
    def on_exit_button(self, event):
        if self.status != CX_CONNECTED:
            self.status = CX_FAILED
        self.close_dialog()
    
    def close_dialog(self):
        if not self.activity or self.status != CX_CONNECTED:
            self.EndModal(CX_FAILED)
        else:
            self.EndModal(self.status)
            
def _main():
    pass

if (__name__ == '__main__'):
    _main()
