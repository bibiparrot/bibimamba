import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSlot, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QProgressBar, QProgressDialog, QMessageBox

from bibimamba.mainwindow import Ui_MainWindow

PYTHON_VERSIONS = ['3.12.3', '3.12.2', '3.12.1', '3.12.0', '3.11.9', '3.11.8', '3.11.7', '3.11.6', '3.11.5', '3.11.4',
                   '3.11.3', '3.11.2', '3.11.1', '3.11.0', '3.10.1', '3.10.1', '3.10.1', '3.10.1', '3.10.1', '3.10.9',
                   '3.10.8', '3.10.7', '3.10.6', '3.10.5', '3.10.4', '3.10.3', '3.10.2', '3.10.1', '3.10.0', '3.9.19',
                   '3.9.18', '3.9.17', '3.9.16', '3.9.15', '3.9.14', '3.9.13', '3.9.12', '3.9.11', '3.9.10', '3.9.9',
                   '3.9.8', '3.9.7', '3.9.6', '3.9.5', '3.9.4', '3.9.3', '3.9.2', '3.9.1', '3.9.0', '3.8.19', '3.8.18',
                   '3.8.17', '3.8.16', '3.8.15', '3.8.14', '3.8.13', '3.8.12', '3.8.11', '3.8.10', '3.8.9', '3.8.8',
                   '3.8.7', '3.8.6', '3.8.5', '3.8.4', '3.8.3', '3.8.2', '3.8.1', '3.8.0', '3.7.17', '3.7.16', '3.7.15',
                   '3.7.14', '3.7.13', '3.7.12', '3.7.11', '3.7.10', '3.7.9', '3.7.8', '3.7.7', '3.7.6', '3.7.5',
                   '3.7.4', '3.7.3', '3.7.2', '3.7.1', '3.7.0', '3.6.15', '3.6.14', '3.6.13', '3.6.12', '3.6.11',
                   '3.6.10', '3.6.9', '3.6.8', '3.6.7', '3.6.6', '3.6.5', '3.6.4', '3.6.3', '3.6.2', '3.6.1', '3.6.0',
                   '3.5.10', '3.5.8', '3.5.7', '3.5.6', '3.5.5', '3.5.4', '3.5.3', '3.5.2', '3.5.1', '3.5.0', '3.4.10',
                   '3.4.9', '3.4.8', '3.4.7', '3.4.6', '3.4.5', '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0', '3.3.7',
                   '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0', '3.2.6', '3.2.5', '3.2.4', '3.2.3',
                   '3.2.2', '3.2.1', '3.2', '3.1.5', '3.1.4', '3.1.3', '3.1.2', '3.1.1', '3.1', '3.0.1', '3.0',
                   '2.7.18', '2.7.17', '2.7.16', '2.7.15', '2.7.14', '2.7.13', '2.7.12', '2.7.11', '2.7.10', '2.7.9',
                   '2.7.8', '2.7.7', '2.7.6', '2.7.5', '2.7.4', '2.7.3', '2.7.2', '2.7.1', '2.7']


def subprocess_run(args, exit=True):
    """
    Wrapper-function around subprocess.run.

    When the sub-process exits with a non-zero return code,
    prints out a message and exits with the same code.
    """
    cp = subprocess.run(args, capture_output=True, text=True)
    print(cp.stdout)
    try:
        cp.check_returncode()
    except subprocess.CalledProcessError as exc:
        print(exc)
        print(cp.stderr)
        if exit:
            sys.exit(cp.returncode)
    return cp.returncode


class SingleWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, conda_path, python_version):
        super().__init__()
        self.conda_path = Path(conda_path)
        self.python_version = python_version
        self.subdir_name = f"conda_python_{'.'.join(self.python_version.split('.')[:2])}"
        self.subdir_path = Path(conda_path) / self.subdir_name
        self.environment_name = f"conda_python_{self.python_version}"
        self.python_exe = Path(conda_path) / 'envs' / self.environment_name / 'python.exe'

    def run(self):
        micromamba_path = Path(__file__).parent.absolute()
        micromamba_exes = list(micromamba_path.glob('micromamba*.exe'))
        if len(micromamba_exes) < 1:
            print(f'NO micromamba.exe under [{micromamba_path}]')
            return
        micromamba_exe = sorted(micromamba_exes, key=lambda file: Path(file).lstat().st_mtime, reverse=True)[
            0].resolve()

        print(f'micromamba [{micromamba_exe}]')
        conda_path = self.subdir_path
        if not self.python_exe.exists():
            subprocess_run([
                micromamba_exe, 'create', '--yes', '-n', self.environment_name, f'python={self.python_version}',
                '-c', 'conda-forge', '--root-prefix', conda_path
            ])

        self.finished.emit()


class bibimamba(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.setWindowFlags(MainWindow.windowFlags() & ~ Qt.WindowType.WindowMaximizeButtonHint)
        self.setWindowFlags(Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle('bibimamba')
        self.setWindowIcon(QIcon(str(Path(__file__).parent / 'bibimamba.png')))

        self.show()

        self.pushButton.clicked.connect(self.open_conda_install_directory)
        self.comboBox.addItems(PYTHON_VERSIONS)
        self.pushButton_2.clicked.connect(self.run_single_processing)

    @pyqtSlot()
    def run_single_processing(self):
        try:
            conda_path = self.lineEdit.text()
            python_version = self.comboBox.currentText()
            if '.' not in python_version:
                python_version = '3.10.3'
            subdir_name = f"conda_python_{'.'.join(python_version.split('.')[:2])}"
            subdir_path = Path(conda_path) / subdir_name
            if conda_path is None or len(conda_path.strip()) == 0:
                QMessageBox.warning(
                    self, f"Empty Path",
                    f"Please select installation root",
                    QMessageBox.StandardButton.Ok
                )
                return

            if Path(conda_path).is_dir() and Path(conda_path).exists():
                if subdir_path.exists():
                    QMessageBox.warning(
                        self, f"Exist {subdir_name}",
                        f"Please remove '{subdir_path.resolve()}'",
                        QMessageBox.StandardButton.Ok
                    )
                    return

                self.label_4.setText(" Waiting ... ")
                worker = SingleWorker(conda_path, python_version)
                progress_dialog = QProgressDialog("Processing ...", "Close", 0, 0, self,
                                                  Qt.WindowType.FramelessWindowHint)
                progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                progress_dialog.setCancelButton(None)
                progress_dialog.show()
                worker.finished.connect(progress_dialog.close)
                worker.finished.connect(self.single_processing_finished)
                worker.start()
                self.pushButton_2.setEnabled(False)
                while worker.isRunning():
                    QApplication.processEvents()
                worker.deleteLater()
        except Exception as ex:
            print(ex)

    def single_processing_finished(self):
        self.pushButton_2.setEnabled(True)
        conda_path = self.lineEdit.text()
        python_version = self.comboBox.currentText()
        python_dir = Path(conda_path) / 'envs' / f"conda_python_{python_version}"
        python_exe = python_dir / 'python.exe'
        linkage = f"<a href={str(python_dir.resolve().as_uri())}>{str(python_exe.resolve())}</a>  "

        self.label_4.setText(linkage)
        self.label_4.setOpenExternalLinks(True)

    @pyqtSlot()
    def open_conda_install_directory(self):
        try:
            dirpath = QFileDialog.getExistingDirectory(
                self,
                caption="Open Directory",
                directory=os.getcwd(),
                options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )
            if Path(dirpath).exists():
                self.lineEdit.setText(str(Path(dirpath).resolve()))
        except Exception as ex:
            print(ex)


def main():
    app = QApplication([])
    window = bibimamba()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
