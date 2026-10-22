from app.greet import greet


def test_greet_names_the_person():
    assert greet("Ada") == "Hello, Ada!"
