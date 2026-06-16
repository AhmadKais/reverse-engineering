# mathsquiz-step1

**Kind**: `module`  
**File**: `mathsquiz/mathsquiz-step1.py`  
**Lines**: 1–158  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
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
    # … (truncated)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
