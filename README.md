# Personal Budget Stress Tester

A beginner-friendly Python program that plans a monthly budget and stress-tests it against unexpected events (higher travel cost, reduced allowance, emergency expense, price rise). It is a learning project in scenario analysis and weighted decision making - not financial advice.

## Features
- Takes income, essential expenses, flexible expenses and a savings target
- Calculates category-wise spending limits and savings percentage
- Calculates a financial pressure score (LOW / MEDIUM / HIGH) using weighted rules
- Applies stress scenarios and creates revised plans
- Compares the original budget with revised plans side by side
- Suggests which flexible categories to reduce
- Explains whether each plan is SAFE, TIGHT or UNREALISTIC

## How to run
Requires Python 3.6 or newer. No extra libraries needed.

```
python budget_stress_tracker.py
```

Choose option 2 in the menu to load a sample budget for a quick demo.

## Rules used
- A flexible category can be cut by at most 60%
- A SAFE plan keeps at least 5% of income unspent
- Pressure score = essentials share (max 40) + total committed share (max 40) + low savings (max 20)
- LOW / MEDIUM / HIGH = 0-30 / 31-60 / 61-100

## Python concepts used
Lists, dictionaries, loops, conditions, functions, percentages, input validation.
