from iterfzf import iterfzf
from time import sleep


def selection(iterable: list):
    """
    Takes in a list and allows the user to choose among the list using fzf

    Args:
        iterable (list): The list from which user should choose an option

    Return:
        Generator Function for iterfzf
    """

    for item in iterable:
        yield item.strip()
        sleep(0.01)


def fzf(iterable: list, prompt: str, choose_multiple: bool = False) -> list | str:
    """
    Takes in a list and allows the user to choose among the list using fzf

    Args:
        iterable (list): The list from which user should choose an option
        prompt (str): Prompt to show in the fzf interface
        choose_multiple (bool): True if user can choose multiple options; False if user cannot

    Return:
        list | str: list of chosen items if 'choose_multiple' is true; string of chosen item otherwise
    """

    return iterfzf(selection(iterable), prompt=prompt, multi=choose_multiple)
