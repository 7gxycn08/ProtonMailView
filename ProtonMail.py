import os
import subprocess
import traceback
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import (QWebEngineSettings, QWebEngineProfile, QWebEnginePage,
                                     QWebEngineNotification, QWebEngineDownloadRequest)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QFileDialog
from notifypy import Notify
import ctypes
import sys


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        # Connect the feature permission requested signal to the slot
        self.featurePermissionRequested.connect(self.on_feature_permission_requested)

    def on_feature_permission_requested(self, url, feature):
        # Check if the requested feature is notifications
        if feature == QWebEnginePage.Feature.Notifications:
            # Grant permission for notifications
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)


class ProtonMail(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.user32 = ctypes.windll.user32
            self.user32.SetProcessDPIAware()
            self.setGeometry(450, 200, 900, 600)
            self.setWindowIcon(QIcon('Resources/mail.ico'))
            self.setWindowTitle('ProtonMailView v1.0')
            self.profile = QWebEngineProfile('ProtonMailProfile', self)
            self.profile.setPersistentStoragePath(fr"C:/Users/{os.getlogin()}/AppData/Local/ProtonMail")
            self.profile.setNotificationPresenter(self.handle_notification)
            self.profile.downloadRequested.connect(self.on_download_requested)
            self.settings = self.profile.settings()
            self.settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            self.settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            self.settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)
            self.webview = QWebEngineView(self)
            self.page = QWebEnginePage(self.profile, self.webview)
            self.page = CustomWebEnginePage(self.profile, self.webview)
            self.webview.setPage(self.page)
            self.setCentralWidget(self.webview)
            self.url = QUrl("https://mail.protonmail.com")
            self.webview.load(self.url)
            self.webview.loadFinished.connect(self.inject_javascript)
            self.webview.setZoomFactor(0.7)
            self.webview.page().action(self.webview.page().WebAction.CopyLinkToClipboard).setVisible(True)
            self.webview.page().action(self.webview.page().WebAction.Cut).setVisible(True)
            self.webview.page().action(self.webview.page().WebAction.Copy).setVisible(True)
            self.webview.page().action(self.webview.page().WebAction.Paste).setVisible(True)
            self.webview.page().action(self.webview.page().WebAction.OpenLinkInNewTab).setVisible(False)
            self.webview.page().action(self.webview.page().WebAction.OpenLinkInNewWindow).setVisible(False)
            self.webview.page().action(self.webview.page().WebAction.SavePage).setVisible(False)
            self.webview.page().action(self.webview.page().WebAction.ViewSource).setVisible(False)
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

    @staticmethod
    def about_page():
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

    @staticmethod
    def handle_notification(notification: QWebEngineNotification):
        # Create a notification object
        noti = Notify(default_notification_application_name="ProtonMailView")

        # Set the title and message for the notification
        noti.title = notification.title()
        noti.message = notification.message()

        # Set the urgency level
        noti.urgency = "normal"

        # Set the path to the notification icon
        noti.icon = "Resources/mail.ico"

        # Set the timeout for the notification
        noti.timeout = 5000  # 10 seconds

        # Display the notification
        noti.send()

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
        self.webview.page().runJavaScript(js)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProtonMail()
    sys.exit(app.exec())
