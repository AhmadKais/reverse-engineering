# print_final_scores

**Kind**: `function`  
**File**: `mathsquiz/mathsquiz-step2.py`  
**Lines**: 23–33  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
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
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
