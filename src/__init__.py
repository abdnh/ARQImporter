import sys

if "unittest" not in sys.modules:
    # pylint: disable=import-error, no-name-in-module
    # pylint: disable=invalid-name
    import aqt
    from aqt.qt import QAction  # type: ignore
    from aqt.utils import showWarning

    from .arqimporter_dialog import ARQImporterDialog
    from . import models

    def open_dialog():
        current_version = aqt.mw.col.get_config(
            "arqimporter_model_version", default="none"
        )
        if not models.ARQOne.is_at_version(current_version):
            showWarning(
                "نوع ملحوظة ARQImporter الخاص بك قديم ويجب ترقيته "
                "قبل أن تستطيع استخدام ARQImporter. للترقية، أعد تشغيل أنكي "
                "وجاوب بنعم على النافذة التي ستظهر."
            )
            return
        dialog = ARQImporterDialog(aqt.mw)
        dialog.exec_()

    if aqt.mw is not None:
        action = QAction(aqt.mw)
        action.setText("استيراد الأسئلة العربية")
        aqt.mw.form.menuTools.addAction(action)
        action.triggered.connect(open_dialog)

        aqt.gui_hooks.profile_did_open.append(models.ensure_note_type)
