from src.formatters import format_duration, kda_ratio, queue_name


def test_kda_ratio_standard() -> None:
    assert kda_ratio(10, 5, 8) == 3.6


def test_kda_ratio_perfect_game() -> None:
    assert kda_ratio(12, 0, 9) == 21.0


def test_format_duration() -> None:
    assert format_duration(1935) == "32:15"


def test_queue_name_known() -> None:
    assert queue_name(420) == "Ranked Solo/Duo"


def test_queue_name_unknown() -> None:
    assert queue_name(999) == "Queue 999"
