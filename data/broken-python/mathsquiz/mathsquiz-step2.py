
# this function will print a welcome message to the user
def welcome_message():
    print("Hello! I'm going to ask you 10 maths questions.")
    print("Let's see how many you can get right!")

# this function will ask a maths question and return the points awarded (1 or 0)
def ask_question(first_number, second_number):
    print("What is", first_number, "x", second_number)
    answer = input("Answer: ")
    if int(answer) == first_number * second_number:
        print("Correct!")
        points_awarded = 1
    else:
        print("Wrong!")
        points_awarded = 0

    print("")

    return points_awarded

# this function will look at the final scores and print the results
def print_final_scores(final_score):
    print("That's all the questions done. So...what was your score...?")
    print("You scored", score, "points out of a possible 10.")
    if score < 5:
        print("You need to practice your maths!")
    elif score < 8:
        print("That's pretty good!")
    elif score < 10:
        print("You did really well! Try and get 10 out of 10 next time!")
    elif score == 10:
        print("Wow! What a maths star you are!! I'm impressed!")




# display welcome message
welcome_message()

# set the score to zero
score = 0

# ask questions
score = score + ask_question(8,7)
score = score + ask_question(4,9)
score = score + ask_question(12,6)
score = score + ask_question(6,8)
score = score + ask_question(7,7)
score = score + ask_question(11,6)
score = score + ask_question(11,2)
score = score + ask_question(7,9)
score = score + ask_question(6,6)
score = score + ask_question(4,8)

# print the final scores
print_final_scores(score)
