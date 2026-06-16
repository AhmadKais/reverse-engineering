# print_final_scores

**Kind**: `function`  
**File**: `mathsquiz/mathsquiz-step3.py`  
**Lines**: 27–41  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
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
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
