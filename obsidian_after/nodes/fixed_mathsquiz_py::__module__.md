# fixed_mathsquiz

**Kind**: `module`  
**File**: `fixed_mathsquiz.py`  
**Lines**: 1–129  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

> FIXED: mathsquiz/mathsquiz.py — all bugs corrected by the Fixer agent.

Bugs fixed:
  1. Python 2 print statements → Python 3 print()
  2. if answer = N  →  if int(answer) == N   (assignment used as c

## Source

```python
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
    # … (truncated)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
