from labourlens.data.pdf_extract import looks_garbled, looks_tabular

# Real garbage shape seen on the last page of the 2Q 2026 report (unmapped font); synthetic reproduction.
GARBLED = "+RZZRXOG\\RXUDWH WKLV VHUYLFH" + " 6HUYLFHUHDGHUVIHHGEDFNIRUPTXHVWLRQ " * 4 + "(OHFWURQLF&RPPHQWV$QGVXJJHVWLRQVWRZDUGV"
PROSE = ("The resident unemployment rate was little changed at 2.9 per cent in the second quarter, while the overall "
         "rate eased as hiring in services continued. Retrenchments rose, led by services industries.")
GLOSSARY = "SA: seasonally adjusted. NSA: not seasonally adjusted. MDW: migrant domestic worker. LMS: Labour Market Survey. MRSD: Manpower Research and Statistics Department."


def test_garbled_block_is_flagged():
    assert looks_garbled(GARBLED)[0]


def test_normal_prose_and_abbreviation_lists_are_not_flagged():
    assert not looks_garbled(PROSE)[0]
    assert not looks_garbled(GLOSSARY)[0]


def test_short_text_never_flagged():
    assert looks_garbled("+RZZR")[0] is False


def test_tabular_detector():
    assert looks_tabular("Total 1,200 3,400 -5.6% 7,800 2,100 9.0%")
    assert not looks_tabular(PROSE)
