# mathsquiz-step3

**Kind**: `module`  
**File**: `mathsquiz/mathsquiz-step3.py`  
**Lines**: 1–62  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
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
    # … (truncated)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
