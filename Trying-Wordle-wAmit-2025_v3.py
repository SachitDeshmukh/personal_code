# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 16:43:33 2025
@author: Sachit Deshmukh
Now packages downloaded:
    1. termcolor
    2. nltk
"""

# importing libraries
from termcolor import colored
import sys
from nltk.corpus import wordnet

# defining all globals
INVALID_INPUT = 0 # storing validity value
COLORS_KEY = {0:"dark_grey", 1:"yellow", 2:"green"} # storing color coding

def Clr_Line(): # clears text on terminal and goes to next line
    sys.stdout.write("\033[F") 
    sys.stdout.write("\033[K")

def Take_Word(): # takes asnwer word and length of wordle
    while True:
        user_answer = input("Please enter your word:")
        user_answer, check_valid = Valid_Answer(user_answer)
        if check_valid == INVALID_INPUT:
            continue
        else:
            user_answer = user_answer.upper()
            len_wordle = len(user_answer)
            break
    return user_answer, len_wordle

def Valid_Answer(input_word): # validates answer word
    in_dictionary = wordnet.synsets(input_word)
    if not isinstance(input_word, str) or not input_word.isalpha() \
        or not in_dictionary:
        Clr_Line()
        print(colored("ERR: This is not a valid word!", "red"))
        return None, INVALID_INPUT
    else:
        return input_word, None

def Valid_Guess(input_word, len_wordle): # validates user guesses
    in_dictionary = wordnet.synsets(input_word)
    if not isinstance(input_word, str) or len(input_word) !=\
    len_wordle or not input_word.isalpha() or not in_dictionary:
        Clr_Line()
        print(colored(f"ERR: Guess is not a {len_wordle}-lettered valid word!", "red"))
        return None, INVALID_INPUT
    else:
        return input_word, None

def Take_Check(user_answer, len_wordle): # takes guess and checks accuracy
    while True:
        user_guess = input("Enter your guess:")
        user_guess, check_valid = Valid_Guess(user_guess, len_wordle)
        if check_valid == INVALID_INPUT:
            continue
        else:
            user_guess = user_guess.upper()
            break

    check_answer = [0]*len_wordle
    guessed_letter = [0]*len_wordle

    for i in range(len_wordle):
        if user_guess[i] == user_answer[i]:
            check_answer[i] = 2
            guessed_letter[i] = 1

    for i in range(len_wordle):
        if check_answer[i]:
            continue
        for j in range(len_wordle):
            if guessed_letter[j] == 0 and user_guess[i] == user_answer[j]:
                check_answer[i] = 1
                guessed_letter[j] = 1
                break

    obtain_color_key = [0]*len_wordle

    Clr_Line()
    for i in range(len_wordle):
        obtain_color_key[i] = COLORS_KEY[check_answer[i]]
        print(colored(user_guess[i], obtain_color_key[i]), end = "")    
    print()

    return user_guess, check_answer

#==============================================================================
# CODE STARTS HERE
#==============================================================================

user_answer, len_wordle = Take_Word()
Clr_Line()

while True: # taking the number of guesses allowed
    guess_count = input("Please enter # guesses allowed: ")
    if not guess_count.isnumeric():
        print(colored("Please enter a numeric value", "red"))
        continue
    else:
        Clr_Line()
        guess_count = int(guess_count)
        break

print(f"This is a {len_wordle}-letter word.")
print(f"You have a total of {guess_count} chances to guess this word.")

while guess_count != 0:
    user_guess, check_answer = Take_Check(user_answer, len_wordle)
    guess_count -= 1
    correct_guesses = sum(check_answer)
    if correct_guesses != 2*len_wordle:
        continue
    else:
        print(f"Great Job! The word is: {user_guess}")
        break
else: print("Sorry, you are out of valid guesses.")

# END OF CODE =================================================================