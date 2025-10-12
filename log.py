def note(text: str):
    """Prints a note to the console."""
    print(">>>>>>", text)


def alert(text: str):
    """Prints an alert to the console."""
    print("!!!!!!", text)


def fyi(text: str):
    """Prints a message for the user's information."""
    print("      ", text)


def fyi_ignore(text: str):
    """Prints a message about an ignored item."""
    print("        -> ignore", text)
