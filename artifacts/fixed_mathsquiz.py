"""FIXED: mathsquiz/mathsquiz.py — all bugs corrected by the Fixer agent.

Bugs fixed:
  1. Python 2 print statements → Python 3 print()
  2. if answer = N  →  if int(answer) == N   (assignment used as comparison)
  3. Wrong answers:  8×7=55→56, 4×9=49→36, 12×6=126→72, 6×8=668→48, 7×7=77→49, 11×6=60→66
  4. Score never incremented → score += 1 added inside each correct branch
  5. All questions labelled "Question 1:" → correct numbering
  6. Only 6 questions instead of 10 → added questions 7–10
  7. else if → elif
  8. if score = 10  → if score == 10
"""

print("Hello! I'm going to ask you 10 maths questions.")
print("Let's see how many you can get right!")

score = 0

# question 1
print("Question 1:")
print("What is 8 x 7?")
answer = input("Answer: ")
if int(answer) == 56:          # FIX 2+3: == and correct answer
    print("Correct!")
    score += 1                 # FIX 4
else:
    print("Wrong! The answer is 56.")

# question 2
print("Question 2:")           # FIX 5
print("What is 4 x 9?")
answer = input("Answer: ")
if int(answer) == 36:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 36.")

# question 3
print("Question 3:")
print("What is 12 x 6?")
answer = input("Answer: ")
if int(answer) == 72:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 72.")

# question 4
print("Question 4:")
print("What is 6 x 8?")
answer = input("Answer: ")
if int(answer) == 48:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 48.")

# question 5
print("Question 5:")
print("What is 7 x 7?")
answer = input("Answer: ")
if int(answer) == 49:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 49.")

# question 6
print("Question 6:")
print("What is 11 x 6?")
answer = input("Answer: ")
if int(answer) == 66:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 66.")

# question 7  (FIX 6: added missing questions)
print("Question 7:")
print("What is 9 x 9?")
answer = input("Answer: ")
if int(answer) == 81:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 81.")

# question 8
print("Question 8:")
print("What is 3 x 12?")
answer = input("Answer: ")
if int(answer) == 36:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 36.")

# question 9
print("Question 9:")
print("What is 5 x 8?")
answer = input("Answer: ")
if int(answer) == 40:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 40.")

# question 10
print("Question 10:")
print("What is 7 x 8?")
answer = input("Answer: ")
if int(answer) == 56:
    print("Correct!")
    score += 1
else:
    print("Wrong! The answer is 56.")

# final scores
print("That's all the questions done. So...what was your score...?")
print("You scored", score, "points out of a possible 10.")
if score < 5:
    print("You need to practice your maths!")
elif score < 8:                # FIX 7: elif not else if
    print("That's pretty good!")
elif score == 10:              # FIX 7+8: elif and == not =
    print("Wow! What a maths star you are!! I'm impressed!")
else:
    print("Almost there — keep practicing!")
