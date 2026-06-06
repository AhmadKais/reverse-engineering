import random

# this function will print a welcome message to the user
def welcome_message():
    print("Hello! I'm going to ask you 10 maths questions.")
    print("Let's see how many you can get right!")

# this function will ask a maths question and return the points awarded (1 or 0)
def ask_question(first_number, second_number):
    print("What is", first_number, "x", second_number)
    answer = input("Answer: ")

    correct_answer = first_number * second_number
    
    if int(answer) == correct_answer:
        print("Correct!")
        points_awarded = 1
    else:
        print("Wrong! The correct answer was", correct_answer)
        points_awarded = 0

    print("")

    return points_awarded

# this function will look at the final scores and print the results
def print_final_scores(final_score, max_possible_score):

    print("That's all the questions done. So...what was your score...?")
    print("You scored", score, "points out of a possible", max_possible_score)

    percentage = (score/max_possible_score)*100
    
    if percentage < 50:
        print("You need to practice your maths!")
    elif percentage < 80:
        print("That's pretty good!")
    elif percentage < 100:
        print("You did really well! Try and get 10 out of 10 next time!")
    elif percentage == 100:
        print("Wow! What a maths star you are!! I'm impressed!")


# display welcome message
welcome_message()


# set the score to zero and the number of questions to 10
score = 0
number_of_questions = 10


# ask questions
for x in range(1,number_of_questions + 1):
    print("Question", x)
    first_number = random.randint(2,12)
    second_number = random.randint(2,12)
    score = score + ask_question(first_number,second_number)
    

# print the final scores
print_final_scores(score, number_of_questions)
