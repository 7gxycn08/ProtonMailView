import os
import subprocess
import traceback
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QUrl, Slot, Qt
from PySide6.QtWebEngineCore import (QWebEngineSettings, QWebEngineProfile, QWebEnginePage,
                                     QWebEngineNotification, QWebEngineDownloadRequest, QWebEnginePermission)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, QFileDialog)
import ctypes
import sys

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.popup_dialog = QMainWindow()
        self.new_webview = QWebEngineView()

    def createWindow(self, _type):
        self.new_webview.setPage(QWebEnginePage(self.profile(), self.new_webview))
        self.new_webview.page().action(self.new_webview.page().WebAction.SavePage).setVisible(False)
        self.new_webview.page().action(self.new_webview.page().WebAction.ViewSource).setVisible(False)
        self.new_webview.page().action(self.new_webview.page().WebAction.Cut).setVisible(True)
        self.new_webview.page().action(self.new_webview.page().WebAction.Copy).setVisible(True)
        self.new_webview.page().action(self.new_webview.page().WebAction.Paste).setVisible(True)
        self.new_webview.setZoomFactor(0.7)
        self.popup_dialog.setWindowTitle("ProtonMailView v1.2")
        self.popup_dialog.setWindowIcon(QIcon('Resources/mail.ico'))
        self.popup_dialog.setCentralWidget(self.new_webview)
        self.popup_dialog.setGeometry(450, 200, 900, 600)
        self.popup_dialog.show()

        return self.new_webview.page()


class ProtonMail(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.user32 = ctypes.windll.user32
            # Try to dynamically get the SetProcessDPIAware function if it exists
            set_dpi_aware = getattr(self.user32, "SetProcessDPIAware", None)

            if set_dpi_aware:
                # Define the return type and argument types for SetProcessDPIAware
                set_dpi_aware.restype = ctypes.c_int  # Return type
                set_dpi_aware.argtypes = []  # No arguments for this function

                # Call the function
                set_dpi_aware()  # Now the function can be called correctly

            self.setGeometry(450, 200, 900, 600)
            self.setWindowIcon(QIcon('Resources/mail.ico'))
            self.setWindowTitle('ProtonMailView v1.2')
            self.profile = QWebEngineProfile('ProtonMailProfile')
            self.profile.setPersistentStoragePath(fr"C:/Users/{os.getlogin()}/AppData/Local/ProtonMail")
            self.profile.setNotificationPresenter(self.handle_notification)
            self.profile.downloadRequested.connect(self.on_download_requested)
            self.settings = self.profile.settings()

            self.settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            self.settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            self.settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)

            self.web_view = QWebEngineView(self)
            self.web_view.setPage(CustomWebEnginePage(self.profile, self.web_view))
            self.setCentralWidget(self.web_view)
            self.url = QUrl("https://mail.protonmail.com")
            self.web_view.load(self.url)
            self.web_view.page().loadFinished.connect(self.inject_javascript)
            self.web_view.page().permissionRequested.connect(self.on_permission_requested)

            self.web_view.setZoomFactor(0.7)
            self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

            self.web_view.page().action(self.web_view.page().WebAction.CopyLinkToClipboard).setVisible(True)
            self.web_view.page().action(self.web_view.page().WebAction.Cut).setVisible(True)
            self.web_view.page().action(self.web_view.page().WebAction.Copy).setVisible(True)
            self.web_view.page().action(self.web_view.page().WebAction.Paste).setVisible(True)
            self.web_view.page().action(self.web_view.page().WebAction.OpenLinkInNewTab).setVisible(False)
            self.web_view.page().action(self.web_view.page().WebAction.OpenLinkInNewWindow).setVisible(True)
            self.web_view.page().action(self.web_view.page().WebAction.SavePage).setVisible(False)
            self.web_view.page().action(self.web_view.page().WebAction.ViewSource).setVisible(True)

            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setToolTip("ProtonMailView")
            self.tray_icon.setIcon(QIcon("Resources/mail.ico"))
            self.tray_icon.activated.connect(
                lambda reason: self.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
            if self.tray_icon is not None:
                self.tray_icon.hide()
            self.tray_menu = QMenu(self)
            self.restore_action = QAction("About", self)
            self.restore_action.triggered.connect(self.about_page)
            self.tray_menu.addAction(self.restore_action)

            self.quit_action = QAction("Quit", self)
            self.quit_action.triggered.connect(QApplication.instance().quit)
            self.tray_menu.addAction(self.quit_action)

            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.show()
            self.show()
        except Exception as e:
            traceback.print_exception(e)

    def on_permission_requested(self, permission: QWebEnginePermission):
        # permission is a QWebEnginePermission object (has permissionType(), grant(), deny())
        if permission.permissionType() == QWebEnginePermission.PermissionType.Notifications:
            print("Granting notifications for", permission.origin().toString())
            permission.grant()
        else:
            permission.deny()


    @Slot(str)
    def redirect_callback(self, url):
        self.url = QUrl(url)
        self.web_view.load(self.url)

    def about_page(self):
        url = "https://github.com/7gxycn08/ProtonMailView"
        subprocess.Popen(f"start {url}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def on_download_requested(self, download: QWebEngineDownloadRequest):
        # Prompt the user to select a save location
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", download.suggestedFileName())

        if save_path:
            # Set download path and accept the download request
            download.setDownloadDirectory(save_path.rsplit('/', 1)[0])
            download.setDownloadFileName(save_path.rsplit('/', 1)[1])
            download.accept()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def handle_notification(self, notification: QWebEngineNotification):
        self.tray_icon.showMessage(
            notification.title(),  # Title
            notification.message(),  # Message
            QIcon('Resources/mail.ico'),  # Icon type (Information, Warning, Critical)
            5000  # Duration in milliseconds
        )

    def inject_javascript(self):
        # JavaScript to auto-allow notifications
        js = """
        navigator.permissions.query({name: 'notifications'}).then(function(result) {
            if (result.state == 'prompt') {
                Notification.requestPermission().then(function(permission) {
                    if (permission == 'granted') {
                       // new Notification('Notifications enabled automatically.');
                    }
                });
            }
        });
        """
        self.web_view.page().runJavaScript(js)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    """Uncomment lines below to route traffic through Socks5Proxy of your choice"""
    # from PySide6 import QtNetwork
    # proxy = QtNetwork.QNetworkProxy()
    # proxy.setType(QtNetwork.QNetworkProxy.ProxyType.Socks5Proxy)
    # proxy.setHostName("127.0.0.1")
    # proxy.setPort(1080)
    # QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
    window = ProtonMail()
    sys.exit(app.exec())
