from sportorg.models.memory import Qualification


def test_get_qual_by_name_is_case_insensitive_for_kms_and_ms():
    assert Qualification.get_qual_by_name("кмс") == Qualification.KMS
    assert Qualification.get_qual_by_name("мс") == Qualification.MS


def test_get_qual_by_name_supports_common_aliases():
    assert Qualification.get_qual_by_name("I") == Qualification.I
    assert Qualification.get_qual_by_name("ii") == Qualification.II
    assert Qualification.get_qual_by_name("3") == Qualification.III
    assert Qualification.get_qual_by_name("1р") == Qualification.I
    assert Qualification.get_qual_by_name("2Р") == Qualification.II
    assert Qualification.get_qual_by_name("3р") == Qualification.III
    assert Qualification.get_qual_by_name("1ю") == Qualification.I_Y
    assert Qualification.get_qual_by_name("IIIЮ") == Qualification.III_Y
    assert Qualification.get_qual_by_name("б.р.") == Qualification.NOT_QUALIFIED
