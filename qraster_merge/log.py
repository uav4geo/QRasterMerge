from qgis.core import QgsMessageLog, Qgis

_feedback = None
def set_log_feedback(feedback):
    global _feedback
    _feedback = feedback

def INFO(message):
    QgsMessageLog.logMessage(message, "QRasterMerge", level=Qgis.MessageLevel.Info)
    if _feedback is not None:
        _feedback.pushInfo(message)
    
def WARNING(message):
    QgsMessageLog.logMessage(message, "QRasterMerge", level=Qgis.MessageLevel.Warning)
    if _feedback is not None:
        _feedback.pushWarning(message)

def CRITICAL(message):
    QgsMessageLog.logMessage(message, "QRasterMerge", level=Qgis.MessageLevel.Critical)
    if _feedback is not None:
        _feedback.reportError(message, True)