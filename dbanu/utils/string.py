def to_var_name(text: str | None, *alternatives: str | None) -> str | None:
    for alternative in [text, *alternatives]:
        if alternative is None:
            continue
        var_name = "".join(
            c for c in alternative.title().replace(" ", "") if c.isalnum()
        ).lstrip("0123456789")
        if var_name != "":
            return var_name
    return None
