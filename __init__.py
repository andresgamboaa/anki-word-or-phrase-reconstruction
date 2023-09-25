from aqt import gui_hooks
from aqt import mw
from aqt import utils 
from anki.cards import Card
import re
import random
import time

pattern = r'<div id="shuffle-this">(.*?)</div>'

container = """
    (function(){
        $('#answers').remove()
        $('#separator').remove()
        $('#shuffled-options').remove()
        $('.option').remove()
        $('#correct').remove()
"""

styles = """ 
        $('head').append(`
            <style id="asdf-style">
                #answers, #shuffled-options {
                    min-height: 60px!important;
                    max-width: 100%!important;
                    display: flex!important;
                    flex-wrap: wrap!important;
                    justify-content: center!important;
                }
                .option, .answer {
                    user-select: none!important;
                    font-size: 30px!important;
                    cursor: "pointer";
                    min-width: 30px!important;
                    min-height: 30px!important;
                    background-color: "black"!important;
                    border-radius: 4px!important;
                    padding: 4px!important;
                    margin: 2px!important;
                    color: "white"!important;
                }
                .answer {
                    display: none !important;
                }
            </style>` 
        )
"""
# TODO Fix: avoid "[]" in incorrect options

def init(card: Card):
    #utils.showText(str())
    instruction = container
    text = get_target_text(card)
    if text:
        run(card, text, instruction)
        return
    apply(instruction)


def get_target_text(card):
    note = mw.col.get_note(card.nid)
    fields = dict(note.items())

    if fields.get("Correct options"):
        return fields["Correct options"].strip()

    return None
 

def run(card: Card, answer:str, instruction:str):
    instruction += """            
        $('body').append(`
            <div id="answers"></div>
            <hr id="separator"/>
            <div id="shuffled-options"></div>
        `)
    """

    options = []
    split_words = False

    if " " in answer.strip():
        words = answer.split()
        options = [word for word in words if word]
        split_words = True
    else:
        text = should_leave_complete(answer)
        if text:
           split_words = True 
           options = [text]
        else:
            options = list(answer)

    incorrect_options = get_incorrect_options(card, split_words)
    options.extend(incorrect_options)

    random.shuffle(options)


    instruction += """
    let option, answer
    """
    for index, option in enumerate(options):
        instruction += """
        option = $('<button id="option-{0}" class="option">{1}</button>')
        option.on('click', function() {{
            $('#answers').append($('<button id="answer-{0}" class="option">{1}</button>'))
            $('#answer-{0}').on('click', function() {{
                $(this).remove()
                $('#option-{0}').prop("disabled", false)
            }})
            $(this).prop("disabled", true)
        }})
        $('#shuffled-options').append(option)

    """.format(index, option)

    instruction += styles
    apply(instruction)


def should_leave_complete(text):
    pattern = r"\[(.*?)\]"
    match = re.search(pattern, text)

    if match:
        inner_text = match.group(1)  # Get the text within the brackets
        return inner_text
    else:
        return None  # No match found


def get_incorrect_options(card:Card, split_words):
    nid = card.nid
    deck_id = card.did
    # from field
    note = mw.col.get_note(nid)
    fields = dict(note.items())
    incorrect_options = set([x for x in fields["Incorrect options (optional)"].strip().split(" ") if x])


    # from other cards with the tag
    tags = fields["Mix options from cards with tag (optional)"].strip().split(" ")
    tag = None if len(tags) == 0 and tags[0] != "" else tags[0]

    if tag:
        cards = []
        if tag: cards = get_cards_with_tag_in_deck(tag, deck_id)

        for c in cards:
            if c.id == card.id: continue
            if len(incorrect_options) >= 5: break

            card_answer = get_target_text(c)
            if card_answer == None: continue

            remove_brakets = should_leave_complete(card_answer)
            if remove_brakets:
                card_answer = remove_brakets

            if split_words:
                for option in card_answer.split(" "):
                    if len(incorrect_options) >= 5: break
                    if option != " ": incorrect_options.add(option)
            else: 
                for char in card_answer:
                    if len(incorrect_options) >= 5: break
                    incorrect_options.add(char)


    return list(incorrect_options)


def get_cards_with_tag_in_deck(tag, deck_id):
    deck_name = mw.col.decks.name(deck_id)
    card_ids = mw.col.find_cards(f'deck:"{deck_name}" tag:{tag}')

    cards = []

    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        cards.append(card)

    random.shuffle(cards)
    return cards


def apply(instruction):
    instruction += "})()"
    mw.reviewer.web.eval(instruction)
    #utils.showText(instruction)

gui_hooks.reviewer_did_show_question.append(init)
#gui_hooks.reviewer_did_show_answer.append(unInit)