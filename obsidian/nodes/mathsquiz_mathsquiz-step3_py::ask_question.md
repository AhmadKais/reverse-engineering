# ask_question

**Kind**: `function`  
**File**: `mathsquiz/mathsquiz-step3.py`  
**Lines**: 9–24  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
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
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
