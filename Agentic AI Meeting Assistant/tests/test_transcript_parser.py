from src.transcript_parser import parse_transcript_file


def test_parse_vtt():
    vtt = b"WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nPriya: I will ship the API.\n"
    text = parse_transcript_file(vtt, "meeting.vtt")
    assert "Priya" in text
    assert "ship the API" in text


def test_parse_srt():
    srt = b"1\n00:00:01,000 --> 00:00:04,000\nRahul: Migration by Tuesday.\n"
    text = parse_transcript_file(srt, "meeting.srt")
    assert "Rahul" in text
    assert "Migration" in text
