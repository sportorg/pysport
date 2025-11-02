from chardet import UniversalDetector


def detect_encoding(file, default_encoding="utf-8"):
    detector = UniversalDetector()
    with open(file, "rb") as fh:
        for line in fh:
            detector.feed(line)
            if detector.done:
                break
        detector.close()

    detected_encoding = detector.result["encoding"]

    supported_encodings = ["utf-8", "UTF-8-SIG", "windows-1251", "UTF-32"]
    if detected_encoding in supported_encodings:
        return detected_encoding

    ret_encoding = default_encoding
    if not ret_encoding:
        ret_encoding = (
            "utf-8"  # for Russia and people with OCAD < 11.0 use windows-1251
        )
    return ret_encoding
