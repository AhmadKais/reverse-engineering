# welcome the player and explain stuff

# fixed: python 3 requires brackets around print statements
print("Hello! I'm going to ask you 10 maths questions.")
print("Let's see how many you can get right!")

# set the score to zero
score = 0

# fixed: added additional questions so that there are 10 of them

# question 1

# fixed: need to use double equals for comparison operations
# fixed: need to convert the user's answer to an integer for comparison
# fixed: the answer to the question (they were all incorrect)
# fixed: score variable is incremented by 1 if the answer is correct
# fixed: every question printed "Question 1"

print("Question 1:")
print("What is 8 x 7")
answer = input("Answer: ")
if int(answer) == 56:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")


# question 2

print("Question 2:")
print("What is 4 x 9")
answer = input("Answer: ")
if int(answer) == 36:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")



# question 3

print("Question 3:")
print("What is 12 x 6")
answer = input("Answer: ")
if int(answer) == 72:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")



# question 4

print("Question 4:")
print("What is 6 x 8")
answer = input("Answer: ")
if int(answer) == 48:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")



# question 5

print("Question 5:")
print("What is 7 x 7")
answer = input("Answer: ")
if int(answer) == 49:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")




# question 6

print("Question 6:")
print("What is 11 x 6")
answer = input("Answer: ")
if int(answer) == 66:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")



# question 7

print("Question 7:")
print("What is 9 x 2")
answer = input("Answer: ")
if int(answer) == 18:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")

# question 8

print("Question 8:")
print("What is 7 x 9")
answer = input("Answer: ")
if int(answer) == 63:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")


# question 9

print("Question 9:")
print("What is 6 x 6")
answer = input("Answer: ")
if int(answer) == 36:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")


# question 10

print("Question 10:")
print("What is 4 x 8")
answer = input("Answer: ")
if int(answer) == 32:
    print("Correct!")
    score = score + 1
else:
    print("Wrong!")


# print the final scores

# fixed: 'else if' needs to be 'elif'
# fixed: another comparison error from using = instead of ==
# fixed: if the score was 8 or 9 then no message was printed

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
