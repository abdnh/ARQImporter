# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QDesktopServices, QTextOption
from PyQt5.QtCore import QUrl, Qt

import aqt
import aqt.editor
from aqt.utils import getFile, showWarning, askUser, tooltip
from anki.notes import Note


from . import import_dialog as arqimporter_form
from .gen_notes import add_notes, cleanse_text
from . import models


class ARQImporterDialog(QDialog):
    def __init__(self, mw):
        self.mw = mw

        QDialog.__init__(self)
        self.form = arqimporter_form.Ui_Dialog()
        self.form.setupUi(self)
        self.deckChooser = aqt.deckchooser.DeckChooser(self.mw, self.form.deckChooser)

        self.form.addCardsButton.clicked.connect(self.accept)
        self.form.cancelButton.clicked.connect(self.reject)
        self.form.openFileButton.clicked.connect(self.onOpenFile)
        self.form.helpButton.clicked.connect(self.onHelp)
        self.form.recognizeChaptersCheckBox.toggled.connect(
            lambda t: self.form.chapterLineEdit.setEnabled(t)
        )
        self.form.recognizeExtraCheckBox.toggled.connect(
            lambda t: self.form.extraLineEdit.setEnabled(t)
        )
        self.form.previosImportedQuestionsCheckBox.toggled.connect(
            lambda t: self.form.previosImportedQuestionsNumber.setEnabled(t)
        )

        opt = QTextOption()
        opt.setTextDirection(Qt.RightToLeft)
        opt.setAlignment(Qt.AlignRight)
        self.form.textBox.document().setDefaultTextOption(opt)

    def accept(self):
        "On close, create notes from the contents of the text editor."
        title = self.form.titleBox.text().strip()

        if not title:
            showWarning("يجب أن تدخل عنوانًا لمجموعة الأسئلة.")
            return

        prev_imported_number = (
            self.form.previosImportedQuestionsNumber.value()
            if self.form.previosImportedQuestionsCheckBox.isChecked()
            else 0
        )
        escaped_title = title.replace('"', '\\"')
        if (prev_imported_number == 0) and self.mw.col.find_notes(
            f'"note:{models.ARQOne.name}" ' f'"عنوان:{escaped_title}"'
        ):
            showWarning(
                "لديك بالفعل مجموعة أسئلة لها العنوان نفسه في مجموعتك. "
                "انظر ما إذا كنت بالفعل قد أضفت هذه الأسئلة، "
                "أو استخدم اسمًا مختلفًا."
            )
            return

        if not self.form.textBox.toPlainText().strip():
            showWarning(
                "لا يوجد شيء لتوليد البطاقات! "
                "اكتب نصًا في الصندوق النصي، أو "
                'استخدم زر "فتح ملف" لاستيراد ملف نصي.'
            )
            return

        tags = self.mw.col.tags.split(self.form.tagsBox.text())
        text = cleanse_text(self.form.textBox.toPlainText().strip())
        did = self.deckChooser.selectedId()
        qa_marker = self.form.qa_marker.text()
        question_marker = self.form.questionMarkerRadioButton.isChecked()
        chapter_marker = (
            self.form.chapterLineEdit.text()
            if self.form.recognizeChaptersCheckBox.isChecked()
            else None
        )
        extra_marker = (
            self.form.extraLineEdit.text()
            if self.form.recognizeExtraCheckBox.isChecked()
            else None
        )

        try:
            notes_generated = add_notes(
                self.mw.col,
                Note,
                title,
                tags,
                text,
                did,
                qa_marker,
                question_marker,
                chapter_marker,
                extra_marker,
                prev_imported_number
            )
        except KeyError as e:
            showWarning(
                "تعذر إيجاد حقل {field} في نوع ملحوظة {name} في مجموعتك. "
                "إذا لم يكن لديك أي ملحوظات ARQImporter بعد، تستطيع حذف "
                "نوع الملحوظة من خلال أدوات > إدارة أنواع الملحوظات وإعادة تشغيل "
                "أنكي لحل المشكلة. أو أضف الحقل إلى نوع الملحوظة.".format(
                    field=str(e), name=models.ARQOne.name
                )
            )  # pylint: disable=no-member
            return

        if notes_generated:
            super(ARQImporterDialog, self).accept()
            self.mw.reset()
            tooltip("%i notes added." % notes_generated)

    def onOpenFile(self):
        if self.form.textBox.toPlainText().strip() and not askUser(
            "سيؤدي استيراد ملف إلى استبدال المحتوى الحالي لمحرر النص. "
            "هل تريد الاستمرار؟"
        ):
            return
        filename = getFile(self, "استيراد نص", None, key="import")
        if not filename:
            return
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
        self.form.textBox.setPlainText(text)

    def onHelp(self):
        QDesktopServices.openUrl(QUrl("https://t.me/Ankiarabic_QA"))
