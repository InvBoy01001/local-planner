from query_utils import normalize_user_query


def test_normalize_literal_newlines_and_whitespace():
    assert normalize_user_query(" first  \\nsecond   ") == "first\nsecond"
