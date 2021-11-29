"""
Mostly based on models.py from the LPCG add-on: https://github.com/sobjornstad/AnkiLPCG/blob/master/src/models.py

"""
from abc import ABC
from textwrap import dedent
from typing import Callable, Dict, Tuple, Type
import os

import aqt
from aqt.utils import askUser, showInfo
from anki.consts import MODEL_CLOZE


class TemplateData(ABC):
    """
    Self-constructing definition for templates.
    """

    name: str
    front: str
    back: str

    @classmethod
    def to_template(cls) -> Dict:
        "Create and return an Anki template object for this model definition."
        assert aqt.mw is not None, "Tried to use models before Anki is initialized!"
        mm = aqt.mw.col.models
        t = mm.new(cls.name)
        t["qfmt"] = dedent(cls.front).strip()
        t["afmt"] = dedent(cls.back).strip()
        return t


class ModelData(ABC):
    """
    Self-constructing definition for models.
    """

    name: str
    fields: Tuple[str, ...]
    templates: Tuple[Type[TemplateData]]
    styling: str
    sort_field: str
    is_cloze: bool
    version: str
    upgrades: Tuple[Tuple[str, str, Callable[[Dict], None]], ...]

    @classmethod
    def to_model(cls) -> Tuple[Dict, str]:
        """
        Create and return a pair of (Anki model object, version spec)
        for this model definition.
        """
        assert aqt.mw is not None, "Tried to use models before Anki is initialized!"
        mm = aqt.mw.col.models
        model = mm.new(cls.name)
        for i in cls.fields:
            field = mm.new_field(i)
            field["rtl"] = True
            mm.add_field(model, field)
        for template in cls.templates:
            t = template.to_template()
            mm.addTemplate(model, t)
        model["css"] = dedent(cls.styling).strip()
        model["sortf"] = cls.fields.index(cls.sort_field)
        if cls.is_cloze:
            model["type"] = MODEL_CLOZE
        return model, cls.version

    @classmethod
    def upgrade_from(cls, current_version: str) -> str:
        """
        Given that the model is at version current_version (typically stored
        in the add-on config), run all functions possible in the updates tuple
        of the model. The updates tuple must be presented in chronological order;
        each element is itself a 3-element tuple:

        [0] Version number to upgrade from
        [1] Version number to upgrade to
        [2] Function taking one argument, the model, and mutating it as required;
            raises an exception if update failed.

        Returns the new version the model is at.
        """
        assert aqt.mw is not None, "Tried to use models before Anki is initialized!"
        model = aqt.mw.col.models.by_name(cls.name)

        at_version = current_version
        for cur_ver, new_ver, func in cls.upgrades:
            if at_version == cur_ver:
                func(model, cls)
                at_version = new_ver
        if at_version != current_version:
            aqt.mw.col.models.save(model)
        return at_version

    @classmethod
    def in_collection(cls) -> bool:
        """
        Determine if a model by this name exists already in the current
        Anki collection.
        """
        assert aqt.mw is not None, "Tried to use models before Anki is initialized!"
        mm = aqt.mw.col.models
        model = mm.by_name(cls.name)
        return model is not None

    @classmethod
    def can_upgrade(cls, current_version: str) -> bool:
        """
        Return True if we know of a newer version of the model than supplied.
        """
        if cls.is_at_version(current_version):
            return False
        for cur_ver, _, __ in cls.upgrades:
            if current_version == cur_ver:
                return True
        return False

    @classmethod
    def is_at_version(cls, current_version: str) -> bool:
        "Return True if this model is at the version current_version."
        return current_version == cls.version


SRCDIR = os.path.dirname(os.path.realpath(__file__))


class ARQOne(ModelData):
    class ARQOneTemplate(TemplateData):
        name = "ARQ1"
        with open(
            os.path.join(SRCDIR, "upgrades/1.1.0/front.txt"), encoding="utf-8"
        ) as f:
            front = f.read()
        with open(
            os.path.join(SRCDIR, "upgrades/1.1.0/back.txt"), encoding="utf-8"
        ) as f:
            back = f.read()

    name = "ARQ 1.0"
    fields = (
        "سؤال",
        "جواب",
        "رقم السؤال",
        "عنوان",
        "باب",
        "كل الأسئلة",
        "إضافي",
        "مصادر",
    )
    templates = (ARQOneTemplate,)
    with open(
        os.path.join(SRCDIR, "upgrades/1.1.0/styling.txt"), encoding="utf-8"
    ) as f:
        styling = f.read()
    sort_field = "سؤال"
    is_cloze = False
    version = "1.1.0"
    upgrades = ()


def ensure_note_type() -> None:
    assert aqt.mw is not None, "Tried to use models before Anki is initialized!"
    mod = ARQOne

    if not mod.in_collection():
        model_data, new_version = mod.to_model()
        aqt.mw.col.models.add(model_data)
        aqt.mw.col.set_config("arqimporter_model_version", new_version)
        return

    # "none": the "version number" pre-versioning
    current_version = aqt.mw.col.get_config("arqimporter_model_version", default="none")
    if mod.can_upgrade(current_version):
        r = askUser(
            "لاستيراد ملحوظات جديدة في إصدار مستورد الأسئلة العربية هذا، "
            "يجب تحديث قالب ARQImporter الخاص بك. "
            "قد يتطلب هذا مزامنة كاملة لمجموعتك بعد الاكتمال. "
            "هل تريد تحديث نوع الملحوظة الآن؟ "
            "إذا لم توافق، ستُسأل عندما تشغل أنكي المرة القادمة."
        )
        if r:
            new_version = mod.upgrade_from(current_version)
            aqt.mw.col.set_config("arqimporter_model_version", new_version)
            showInfo(
                "تم تحديث قالب ARQImporter الخاص بك بنجاح. "
                "يرجى التأكد من أن بطاقات ARQImporter الخاصة بك "
                "تظهر بشكل صحيح لكي تستطيع الاسترجاع من نسخة احتياطية "
                "في حال كان هناك خطب ما."
            )
        return

    assert mod.is_at_version(aqt.mw.col.get_config("arqimporter_model_version")), (
        "قالب ARQImporter الخاص بك قديم، لكنني لم أعثر على طريقة تحديث صالحة. "
        "من المرجح أن تصادف مشاكل. "
        "الرجاء التواصل مع المطور أو طلب الدعم لحل هذه المشكلة."
    )
