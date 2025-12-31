import ast
import sys
import os
import json
import typing
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QPushButton, QTextBrowser, QTextEdit, QShortcut
from PyQt5 import uic
from PyQt5.QtGui import QKeySequence, QPalette, QColor, QTextCursor, QTextCharFormat, QMouseEvent
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread, QProcess, QPoint

from dotenv import load_dotenv

from bin.download_mb_coverage import MobileCoverageDealer
from bin.download_fixed_coverage import FixedCoverageDealer
from bin.download_challenge_data import Challenger
from guss import GUSS
from guss.gussErrors import GussExceptions

from gui.dark_mode import set_dark_pallet


def tech_split_entry(s: str):
    s_list = [int(x) if x.isdigit() else x.strip(" ") for x in s.split(',')]
    return s_list


class ErrorDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("./gui/error_dialog.ui", self)

    def write_error(self, label_string):
        self.error_dialog_lbl.setText(label_string)

    def show_model(self) -> None:
        self.exec_()


class MobileWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_running = True

    def run(self):
        def print_hook(*args, **kwargs):

            message = f"\n{args[1]}"
            self.progress.emit(message + '\n')

        original_stdout = sys.stdout
        sys.stdout = type('', (), {'write': print_hook, 'flush': lambda: None})()

        try:

            mobile_coverage_dealer = MobileCoverageDealer(**self.params)
            res_dict = mobile_coverage_dealer.download()




        except GussExceptions as e:
            self.progress.emit(f"{e}")
        finally:
            sys.stdout = original_stdout
            self.finished.emit()


class FixedWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_running = True

    def run(self):
        def print_hook(*args, **kwargs):

            message = f"\n{args[1]}"
            self.progress.emit(message + '\n')

        original_stdout = sys.stdout
        sys.stdout = type('', (), {'write': print_hook, 'flush': lambda: None})()

        try:

            fixed_coverage_dealer = FixedCoverageDealer(**self.params)
            res_dict = fixed_coverage_dealer.download()

        except GussExceptions as e:
            self.progress.emit(f"{e}")
        finally:
            sys.stdout = original_stdout
            self.finished.emit()


class ChallengeWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_running = True

    def run(self):
        def print_hook(*args, **kwargs):

            message = f"\n{args[1]}"
            self.progress.emit(message + '\n')

        original_stdout = sys.stdout
        sys.stdout = type('', (), {'write': print_hook, 'flush': lambda: None})()

        try:

            challenge_dealer = Challenger(**self.params)
            res_dict = challenge_dealer.download()

        except GussExceptions as e:
            self.progress.emit(f"{e}")
        finally:
            sys.stdout = original_stdout
            self.finished.emit()


def restart_app():
    # start a new process of the current scipt
    QProcess.startDetached(sys.executable, sys.argv)
    # Quite the current Application
    QApplication.quit()

def quit_app():
    QApplication.quit()

#################################################################################################################
#                                                     Guss                                                      #
#                                                  Main Window                                                  #
#################################################################################################################



class GussMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('./gui/GUSS.ui', self)
        # Set the window flag to remove the title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        #Keyboard Short Cuts
        self.reset_shortcut = QShortcut(QKeySequence("Ctrl+Alt+R"), self)
        self.reset_shortcut.activated.connect(lambda : restart_app())


        self.error_dialog = ErrorDialog()
        self.error_dialog.setWindowModality(2)

        # Redirect stdout to QTextBrowser (initial setup)
        sys.stdout = EmittingStream(self.app_stdOut)

        # Connect submit buttons
        self.m_submitt.clicked.connect(lambda: self.m_submit_clicked(self.is_env_set()))
        self.f_submitt.clicked.connect(lambda: self.f_submit_clicked(self.is_env_set()))
        self.c_submitt.clicked.connect(lambda: self.c_submit_clicked(self.is_env_set()))

        # Connect env browser button
        self.env_file_btn.clicked.connect(lambda: self.load_env())

        # Connect env browser, restart, quit in file menu
        self.actionLoad_Enviroment_file.triggered.connect(lambda: self.load_env())
        self.actionRestart_App.triggered.connect(lambda: restart_app())
        self.actionQuit_2.triggered.connect(lambda: quit_app())

        # cancel download button
        self.cancel_btn.setEnabled(False)  # Initially disabled
        self.cancel_btn.clicked.connect(lambda: self.cancel_worker())

        # clear logs btn
        self.clear_messages_btn.clicked.connect(lambda: self.clear_message_box())

        # Base Output Path
        self.base_file_path.setText(str(GUSS.DATA_OUTPUT))
        self.base_folder_select_btn.clicked.connect(lambda: self.load_base_path())

        # Fixed logic
        self.f_polygonize_radio.toggled.connect(lambda checked: self.enable_other_field(checked))

    def mousePressEvent(self, event: typing.Optional[QMouseEvent]) -> None:
        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event: typing.Optional[QMouseEvent]) -> None:
        delta = QPoint(event.globalPos() - self.oldPosition)
        self.move(self.x()+ delta.x(), self.y() + delta.y())
        self.oldPosition = event.globalPos()


    def toggle_lock_buttons(self, reset_all=False):
        for btn in [self.m_submitt, self.f_submitt, self.c_submitt]:
            # print(f"current stated of button: {btn.isEnabled()}")
            if reset_all:
                btn.setEnabled(True)
            elif btn.isEnabled():
                btn.setEnabled(False)
            else:
                btn.setEnabled(True)

    def clear_message_box(self):
        self.app_stdOut.clear()

    def create_Guss_instance(self):
        credentials = ast.literal_eval(os.environ['credentials'])
        guss = GUSS.Guss(**credentials)
        print(f"\n----------------------------------------------------------------------------")
        print(f"Guss User: {guss}")
        self.guss_instance = guss

    def cancel_worker(self):
        self.guss_instance.stop = True

    def on_worker_finished(self):
        # print("worker finished")
        self.toggle_lock_buttons()

    def set_credentials(self):
        username = self.env_username.text()
        hash = self.env_api_key.text()
        os.environ['credentials'] = json.dumps({'USERNAME': f'{username}', 'HASH_VALUE': f'{hash}'})
        os.environ['BASE_URL'] = 'https://broadbandmap.fcc.gov'

    def load_env(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Env File', '', 'Env File (.env);;')
        if fname:
            load_dotenv(fname)
            credentials = ast.literal_eval(os.environ['credentials'])
            self.env_username.setText(credentials['USERNAME'])
            self.env_api_key.setText(credentials['HASH_VALUE'])

    def load_base_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Output folder')
        if folder_path:
            GUSS.BASE_DIR, GUSS.DATA_DIR, GUSS.DATA_INPUT, \
            GUSS.DATA_OUTPUT, GUSS.CSV_OUTPUT, GUSS.SHP_OUTPUT, \
            GUSS.GPK_OUTPUT = GUSS.create_initial_directories(folder_path)
            self.base_file_path.setText(str(GUSS.BASE_DIR))

    def is_env_set(self):
        if self.env_api_key.text() != "" and self.env_username.text() != "":
            return True
        else:
            self.error_dialog.write_error("Please fill out username and API key in the Environment Settings Tab")
            self.error_dialog.show_model()
            return False

    def enable_other_field(self, checked):
        self.f_GIS_Output_type_com.setEnabled(checked)

    def update_text_browser(self, text):
        self.app_stdOut.moveCursor(self.app_stdOut.textCursor().End)
        self.app_stdOut.insertPlainText(text)

    def m_submit_clicked(self, env_set):

        if env_set:
            self.set_credentials()
            self.create_Guss_instance()
            print("\n----------------------------------------------------------------------------")

            as_of = str(self.m_asOfDate_com.currentText())
            pid_list = [x.strip(" ") for x in self.m_providerIDList.text().split(',')]
            state_fips_list = [x.strip(" ") for x in self.m_state_fips_list.text().split(',')]
            tech_list = tech_split_entry(str(self.m_tech_list.text()))
            tech_type = str(self.m_tech_type_com.currentText())
            subcat = str(self.m_GisCoverageType_com.currentText())
            fiveG_speed_list = tech_split_entry(self.m_5G_speed_list.text())
            gis_output_type = str(self.m_GIS_Output_type_com.currentText())

            params = {
                "run": True,
                'guss_instance': self.guss_instance,
                "as_of_date": as_of,
                "provider_id_list": pid_list,
                "state_fips_list": state_fips_list,
                "technology_list": tech_list,
                "technology_type": tech_type,
                "subcategory": subcat,
                "fiveG_speed_tier_list": fiveG_speed_list,
                "data_type": 'availability',
                "gis_type": gis_output_type
            }
            # 1. Create a QThread object and a Worker object
            self.thread = QThread()
            self.m_worker = MobileWorker(params)

            # 2. Move the worker object to the thread
            self.m_worker.moveToThread(self.thread)

            # 3. Connect signals for communication
            self.thread.started.connect(self.m_worker.run)
            self.m_worker.progress.connect(self.update_text_browser)
            self.m_worker.finished.connect(self.on_worker_finished)

            # 4. Connect cleanup operations (recommended)
            self.m_worker.finished.connect(self.m_worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.m_worker.finished.connect(self.thread.quit)

            # 5. Start the thread
            self.thread.start()
            self.cancel_btn.setEnabled(True)
            self.toggle_lock_buttons()

    def f_submit_clicked(self, env_set):

        if env_set:
            self.set_credentials()
            self.create_Guss_instance()
            print("\n----------------------------------------------------------------------------")

            as_of = str(self.f_asOfDate_com.currentText())
            pid_list = [x.strip(" ") for x in self.f_providerIDList.text().split(',')]
            state_fips_list = [x.strip(" ") for x in self.f_state_fips_list.text().split(',')]
            tech_list = tech_split_entry(str(self.f_tech_list.text()))
            polygonize = True if self.f_polygonize_radio.isChecked() else False
            gis_output_type = str(self.f_GIS_Output_type_com.currentText()) if polygonize else None

            params = {
                "run": True,
                'guss_instance': self.guss_instance,
                "as_of_date": as_of,
                "provider_id_list": pid_list,
                "state_fips_list": state_fips_list,
                "technology_list": tech_list,
                'polygonize': polygonize,
                "data_type": 'availability',
                "gis_type": gis_output_type
            }
            print(params)

            # 1. Create a QThread object and a Worker object
            self.thread = QThread()
            self.f_worker = FixedWorker(params)

            # 2. Move the worker object to the thread
            self.f_worker.moveToThread(self.thread)

            # 3. Connect signals for communication
            self.thread.started.connect(self.f_worker.run)
            self.f_worker.progress.connect(self.update_text_browser)
            self.f_worker.finished.connect(self.on_worker_finished)

            # 4. Connect cleanup operations (recommended)
            self.f_worker.finished.connect(self.f_worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.f_worker.finished.connect(self.thread.quit)

            # 5. Start the thread
            self.thread.start()
            self.cancel_btn.setEnabled(True)
            self.toggle_lock_buttons()

    def c_submit_clicked(self, checked):
        if checked:
            self.set_credentials()
            self.create_Guss_instance()
            print("\n----------------------------------------------------------------------------")

            as_of = str(self.c_asOfDate_com.currentText())
            category = str(self.c_category_com.currentText())
            state_fips_list = [x.strip(" ") for x in self.c_state_fips_list.text().split(',')]

            params = {
                "run": True,
                'guss_instance': self.guss_instance,
                "as_of_date": as_of,
                "category": category,
                "state_fips_list": state_fips_list,
            }
            # print(params)

            # 1. Create a QThread object and a Worker object
            self.thread = QThread()
            self.c_worker = ChallengeWorker(params)

            # 2. Move the worker object to the thread
            self.c_worker.moveToThread(self.thread)

            # 3. Connect signals for communication
            self.thread.started.connect(self.c_worker.run)
            self.c_worker.progress.connect(self.update_text_browser)
            self.c_worker.finished.connect(self.on_worker_finished)

            # 4. Connect cleanup operations (recommended)
            self.c_worker.finished.connect(self.c_worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.c_worker.finished.connect(self.thread.quit)

            # 5. Start the thread
            self.thread.start()
            self.cancel_btn.setEnabled(True)
            self.toggle_lock_buttons()


class EmittingStream:
    def __init__(self, text_browser):
        self.text_browser = text_browser
        self.original_stdout = sys.__stdout__
        self.original_stderr = sys.__stderr__

    def write(self, text):
        if not isinstance(text, str):
            text = str(text)

        self.text_browser.moveCursor(self.text_browser.textCursor().End)
        self.text_browser.insertPlainText(text)

    def flush(self):
        self.original_stdout.flush()
        self.original_stderr.flush()


EXIT_CODE_RESTART = -123


def main():
    while True:
        app = QApplication(sys.argv)
        app.setApplicationName("Guss")
        app.setApplicationDisplayName("Guss")
        app.setStyle("Fusion")
        app.setPalette(set_dark_pallet())
        Guss_window = GussMainWindow()
        Guss_window.setWindowTitle("GUSS")
        Guss_window.show()
        exit_code = app.exec()

        if exit_code != EXIT_CODE_RESTART:
            break
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
