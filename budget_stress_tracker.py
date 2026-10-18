"""
Personal Budget Stress Tester

A monthly budget planner that:
  * takes income, essential expenses, flexible expenses and a savings target
  * calculates category-wise spending limits and savings percentage
  * calculates a financial pressure score (Low / Medium / High)
  * applies "stress events" (higher travel cost, reduced allowance, ...)
  * compares the original budget with revised plans
  * tells which categories can be reduced
  * explains whether a plan is SAFE, TIGHT or UNREALISTIC

This is a learning project for scenario analysis. It is NOT financial advice.
Uses only: lists, dictionaries, loops, conditions, functions, percentages.
"""

import copy


MAX_CUT = 0.60          # a flexible category can be cut by at most 60%
SAFE_BUFFER_PCT = 5     # a SAFE plan keeps at least 5% of income unspent



def money(amount):
       return f"Rs {amount:,.0f}"


def total(category_dict):
    result = 0
    for name in category_dict:
        result += category_dict[name]
    return result


def get_number(prompt, minimum=0.0):
    """Keep asking until the user types a valid number >= minimum."""
    while True:
        text = input(prompt).strip().replace(",", "")
        try:
            value = float(text)
        except ValueError:
            print("  Please type a number, for example 5000.")
            continue
        if value < minimum:
            print(f"  The number must be at least {minimum:g}.")
            continue
        return value


def get_choice(prompt, low, high):
    """Keep asking until the user types a whole number from low to high."""
    while True:
        text = input(prompt).strip()
        if text.isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"  Please type a number from {low} to {high}.")


# GETTING THE BUDGET
def read_categories(title, ask_priority, min_count):
    """
    Ask the user for categories and their monthly amounts.
    For flexible expenses we also ask 'how easy is it to cut?' (1 to 5).
    Returns two dictionaries: amounts and priorities.
    """
    print(f"\n{title}")
    print("Type a category name and press Enter.")
    print("When you have added all categories, just press Enter on an empty name (or type done).")
    amounts = {}
    priorities = {}
    while True:
        name = input("  Category name (Enter or 'done' = finished): ").strip()
        if name == "" or name.lower() == "done":
            if len(amounts) < min_count:
                print("  Please add at least one category first.")
                continue
            break
        if name in amounts:
            print("  You already added that category.")
            continue
        amounts[name] = get_number(f"  Monthly amount for {name} (Rs): ")
        if ask_priority:
            priorities[name] = get_choice(
                "  How easy is it to cut? (1 = very hard ... 5 = very easy): ", 1, 5)
    return amounts, priorities


def enter_plan():
   
    print("\n=== ENTER YOUR MONTHLY BUDGET ===")
    income = get_number("Monthly income / allowance (Rs): ", minimum=1)
    essential, _ = read_categories(
        "ESSENTIAL expenses (rent, food, transport, bills ...)", False, 1)
    flexible, priority = read_categories(
        "FLEXIBLE expenses (eating out, shopping, travel, entertainment ...)", True, 0)
    savings = get_number("Monthly savings target (Rs): ")
    return {
        "name": "Original",
        "note": "Your original budget",
        "income": income,
        "essential": essential,
        "flexible": flexible,
        "priority": priority,
        "savings": savings,
    }


def sample_plan():
    """A ready-made student budget, useful for demo and testing."""
    return {
        "name": "Original",
        "note": "Sample student budget",
        "income": 15000,
        "essential": {"Hostel/Rent": 4500, "Food": 3000,
                      "Transport": 1200, "Phone & Internet": 500},
        "flexible": {"Eating out": 1000, "Entertainment": 800,
                     "Shopping": 1000, "Travel": 700},
        "priority": {"Eating out": 4, "Entertainment": 5,
                     "Shopping": 5, "Travel": 3},
        "savings": 1500,
    }


# STEP 2: ANALYSING A PLAN

def calculate_pressure(income, essential, flexible, savings):
    """
    Financial pressure score from 0 to 100 using weighted rules.
      Rule 1 (max 40): how much of income goes to essentials
      Rule 2 (max 40): how much of income is committed in total
      Rule 3 (max 20): how small the savings cushion is
    Returns (score, level, reasons).
    """
    score = 0
    reasons = []

    # essential share
    essential_pct = essential / income * 100
    if essential_pct > 70:
        points = 40
    elif essential_pct > 50:
        points = 25
    elif essential_pct > 35:
        points = 10
    else:
        points = 0
    score += points
    reasons.append(f"Essentials take {essential_pct:.1f}% of income -> +{points} points")

    # everything (essentials + flexible + savings) against income
    committed_pct = (essential + flexible + savings) / income * 100
    if committed_pct > 100:
        points = 40
    elif committed_pct > 90:
        points = 25
    elif committed_pct > 80:
        points = 10
    else:
        points = 0
    score += points
    reasons.append(f"Total planned spending + savings is {committed_pct:.1f}% of income -> +{points} points")

    # savings cushion
    savings_pct = savings / income * 100
    if savings_pct < 5:
        points = 20
    elif savings_pct < 10:
        points = 10
    else:
        points = 0
    score += points
    reasons.append(f"Savings are {savings_pct:.1f}% of income -> +{points} points")

    if score <= 30:
        level = "LOW"
    elif score <= 60:
        level = "MEDIUM"
    else:
        level = "HIGH"
    return score, level, reasons


def suggest_cuts(flexible, priority, shortfall):
    """
    Decide how much to cut from each flexible category.
    Weighted rule: weight = amount x priority (priority 5 = easiest to cut).
    Bigger and easier-to-cut categories give up more money, but no category
    is cut by more than MAX_CUT (60%).
    Returns (cuts_dictionary, money_still_not_covered).
    """
    cuts = {}
    for name in flexible:
        cuts[name] = 0.0

    remaining = shortfall
    # Repeat, because a category that hits its 60% limit passes the rest on
    for _ in range(20):
        if remaining <= 0.01:
            break
        eligible = []
        for name in flexible:
            if cuts[name] < flexible[name] * MAX_CUT - 0.01:
                eligible.append(name)
        if len(eligible) == 0:
            break
        total_weight = 0
        for name in eligible:
            total_weight += flexible[name] * priority[name]
        if total_weight == 0:
            break
        given = 0.0
        for name in eligible:
            share = remaining * (flexible[name] * priority[name]) / total_weight
            room = flexible[name] * MAX_CUT - cuts[name]
            cut = min(share, room)
            cuts[name] += cut
            given += cut
        remaining -= given
    return cuts, max(remaining, 0.0)


def analyse(plan):
   
    income = plan["income"]
    essential = total(plan["essential"])
    flexible = total(plan["flexible"])
    savings = plan["savings"]

    savings_pct = savings / income * 100
    available = income - essential - savings   # money left for flexible spending
    leftover = available - flexible            # negative means a deficit

    score, level, reasons = calculate_pressure(income, essential, flexible, savings)

    # Verdict rules
    lowest_possible_flexible = flexible * (1 - MAX_CUT)
    buffer_needed = income * SAFE_BUFFER_PCT / 100
    if lowest_possible_flexible > available:
        verdict = "UNREALISTIC"
    elif leftover < buffer_needed:
        verdict = "TIGHT"
    else:
        verdict = "SAFE"
    downgraded = False
    if verdict == "SAFE" and level == "HIGH":
        verdict = "TIGHT"
        downgraded = True

    # Cuts needed to remove the deficit
    shortfall = max(-leftover, 0.0)
    cuts, uncovered = suggest_cuts(plan["flexible"], plan["priority"], shortfall)

    # Explanation in plain words
    explanation = []
    if verdict == "SAFE":
        explanation.append(
            f"After essentials, savings and flexible spending you still keep "
            f"{money(leftover)} ({leftover / income * 100:.1f}% of income) unspent.")
        explanation.append("That is above the 5% safety buffer, so the plan can absorb small surprises.")
    elif verdict == "TIGHT":
        if downgraded:
            explanation.append("The numbers fit, but the pressure level is HIGH, so the plan is marked TIGHT.")
        elif leftover >= 0:
            explanation.append(
                f"The plan fits, but only {money(leftover)} ({leftover / income * 100:.1f}% of income) "
                f"is left. A safe plan keeps at least {SAFE_BUFFER_PCT}%.")
        else:
            explanation.append(
                f"Flexible spending is {money(-leftover)} too high. It can be fixed by "
                f"cutting flexible categories (see suggested limits).")
    else:
        explanation.append(
            f"Even after cutting flexible spending by the maximum {MAX_CUT * 100:.0f}% "
            f"(to {money(lowest_possible_flexible)}), it does not fit into the "
            f"{money(available)} available after essentials and savings.")
        explanation.append(
            "Options: lower the savings target, increase income, or reduce essential costs.")

    return {
        "income": income,
        "essential": essential,
        "flexible": flexible,
        "savings": savings,
        "savings_pct": savings_pct,
        "available": available,
        "leftover": leftover,
        "score": score,
        "level": level,
        "reasons": reasons,
        "verdict": verdict,
        "cuts": cuts,
        "uncovered": uncovered,
        "explanation": explanation,
    }



# SHOWING RESULTS

def print_analysis(plan, result):
    income = plan["income"]
    line = "=" * 62
    print(f"\n{line}")
    print(f"  ANALYSIS: {plan['name']}  ({plan['note']})")
    print(line)
    print(f"  Income                : {money(income)}")
    print(f"  Essential expenses    : {money(result['essential'])}")
    print(f"  Flexible expenses     : {money(result['flexible'])}")
    print(f"  Savings target        : {money(result['savings'])}  ({result['savings_pct']:.1f}% of income)")
    print(f"  Left after everything : {money(result['leftover'])}")

    print(f"\n  {'Category':<22}{'Planned':>11}{'Limit':>11}{'% income':>10}")
    print("  " + "-" * 54)
    print("  ESSENTIAL (fixed, cannot be cut)")
    for name in plan["essential"]:
        amount = plan["essential"][name]
        print(f"  {name:<22}{amount:>11,.0f}{amount:>11,.0f}{amount / income * 100:>9.1f}%")
    print("  FLEXIBLE (limit = planned amount - suggested cut)")
    for name in plan["flexible"]:
        amount = plan["flexible"][name]
        limit = amount - result["cuts"][name]
        print(f"  {name:<22}{amount:>11,.0f}{limit:>11,.0f}{limit / income * 100:>9.1f}%")

    print("\n  Categories that can be reduced:")
    any_cut = False
    for name in plan["flexible"]:
        cut = result["cuts"][name]
        if cut > 0.5:
            any_cut = True
            percent = cut / plan["flexible"][name] * 100
            print(f"    - {name}: reduce by {money(cut)} ({percent:.0f}%)")
    if not any_cut:
        print("    - No cuts needed.")
    if result["uncovered"] > 0.5:
        print(f"    ! Even with maximum cuts, {money(result['uncovered'])} is still missing.")

    print("\n  How the pressure score was calculated:")
    for reason in result["reasons"]:
        print(f"    * {reason}")
    print(f"\n  FINANCIAL PRESSURE : {result['level']}  (score {result['score']}/100)")
    print(f"  FINAL VERDICT      : {result['verdict']}")
    for sentence in result["explanation"]:
        print(f"    {sentence}")
    print(line)


def compare_plans(plans):
    """Print all plans side by side, then list what changed and the cuts."""
    results = []
    for plan in plans:
        results.append(analyse(plan))

    width = 15
    print("\n" + "=" * (24 + width * len(plans)))
    print("  COMPARISON OF PLANS")
    print("=" * (24 + width * len(plans)))

    header = f"{'':<24}"
    for plan in plans:
        header += f"{plan['name']:>{width}}"
    print(header)
    print("-" * (24 + width * len(plans)))

    rows = [
        ("Income", "income", "money"),
        ("Essential expenses", "essential", "money"),
        ("Flexible expenses", "flexible", "money"),
        ("Savings target", "savings", "money"),
        ("Savings % of income", "savings_pct", "percent"),
        ("Left after all", "leftover", "money"),
        ("Pressure score", "score", "plain"),
        ("Pressure level", "level", "text"),
        ("VERDICT", "verdict", "text"),
    ]
    for label, key, kind in rows:
        row = f"{label:<24}"
        for result in results:
            value = result[key]
            if kind == "money":
                text = money(value)
            elif kind == "percent":
                text = f"{value:.1f}%"
            elif kind == "plain":
                text = f"{value}"
            else:
                text = value
            row += f"{text:>{width}}"
        print(row)

    print("\nWhat each plan assumes:")
    for plan in plans:
        print(f"  {plan['name']}: {plan['note']}")

    print("\nSuggested cuts to make each plan work:")
    for index in range(len(plans)):
        plan = plans[index]
        result = results[index]
        cut_list = []
        for name in plan["flexible"]:
            if result["cuts"][name] > 0.5:
                cut_list.append(f"{name} -{money(result['cuts'][name])}")
        if len(cut_list) == 0:
            text = "no cuts needed"
        else:
            text = ", ".join(cut_list)
        if result["uncovered"] > 0.5:
            text += f"  (still short by {money(result['uncovered'])})"
        print(f"  {plan['name']}: {text}")

    original = results[0]
    print("\nChange compared with the original plan:")
    for index in range(1, len(plans)):
        result = results[index]
        diff_pressure = result["score"] - original["score"]
        diff_left = result["leftover"] - original["leftover"]
        print(f"  {plans[index]['name']}: verdict {original['verdict']} -> {result['verdict']}, "
              f"pressure {diff_pressure:+d} points, left-over money changed by Rs {diff_left:+,.0f}")
    print()

# STRESS SCENARIOS

def apply_scenario(base, number):
    """Make a COPY of the original plan and change it. Returns the new plan."""
    new_plan = copy.deepcopy(base)   # deepcopy so the original stays untouched
    new_plan["name"] = f"Revised {number}"

    print("\nChoose a stress event:")
    print("  1. Higher expense in one category (example: travel costs more)")
    print("  2. Reduced allowance / income")
    print("  3. One-time emergency cost (medical, repair ...)")
    print("  4. Price rise on all essential expenses")
    choice = get_choice("Your choice (1-4): ", 1, 4)

    if choice == 1:
        names = list(base["essential"]) + list(base["flexible"])
        print("\nWhich category?")
        for i in range(len(names)):
            print(f"  {i + 1}. {names[i]}")
        picked = names[get_choice("Category number: ", 1, len(names)) - 1]
        percent = get_number(f"By how many % does {picked} increase? ")
        if picked in new_plan["essential"]:
            new_plan["essential"][picked] *= 1 + percent / 100
        else:
            new_plan["flexible"][picked] *= 1 + percent / 100
        new_plan["note"] = f"{picked} expense up by {percent:g}%"

    elif choice == 2:
        percent = get_number("By how many % does income drop? ")
        if percent >= 100:
            percent = 99
            print("  (Limited to 99% so that income stays above zero.)")
        new_plan["income"] *= 1 - percent / 100
        new_plan["note"] = f"Income / allowance down by {percent:g}%"

    elif choice == 3:
        amount = get_number("Emergency cost this month (Rs): ")
        old = new_plan["essential"].get("Emergency cost", 0)
        new_plan["essential"]["Emergency cost"] = old + amount
        new_plan["note"] = f"One-time emergency cost of {money(amount)}"

    else:
        percent = get_number("By how many % do essential prices rise? ")
        for name in new_plan["essential"]:
            new_plan["essential"][name] *= 1 + percent / 100
        new_plan["note"] = f"All essential prices up by {percent:g}%"

    return new_plan


# MAIN MENU

def choose_plan(plans):
    """If there are several plans, ask which one to show."""
    if len(plans) == 1:
        return plans[0]
    print("\nWhich plan?")
    for i in range(len(plans)):
        print(f"  {i + 1}. {plans[i]['name']} - {plans[i]['note']}")
    return plans[get_choice("Plan number: ", 1, len(plans)) - 1]


def main():
    print("=" * 62)
    print("        PERSONAL BUDGET STRESS TESTER")
    print("  (learning project - this is NOT financial advice)")
    print("=" * 62)

    plans = []   # plans[0] is the original, the rest are revised plans

    while True:
        print("\n--- MAIN MENU ---")
        print("  1. Enter my own budget")
        print("  2. Load the sample budget (quick demo)")
        print("  3. Analyse a plan")
        print("  4. Add a stress scenario (creates a revised plan)")
        print("  5. Compare original with revised plans")
        print("  6. Exit")
        choice = get_choice("Choose an option (1-6): ", 1, 6)

        if choice == 1:
            plans = [enter_plan()]
            print("\nBudget saved. Any old revised plans were cleared.")
        elif choice == 2:
            plans = [sample_plan()]
            print("\nSample budget loaded.")
        elif choice == 6:
            print("\nThank you for using the Budget Stress Tester. Goodbye!")
            break
        elif len(plans) == 0:
            print("\nPlease enter a budget first (option 1 or 2).")
        elif choice == 3:
            plan = choose_plan(plans)
            print_analysis(plan, analyse(plan))
        elif choice == 4:
            new_plan = apply_scenario(plans[0], len(plans))
            plans.append(new_plan)
            print(f"\n'{new_plan['name']}' created: {new_plan['note']}")
            print_analysis(new_plan, analyse(new_plan))
        elif choice == 5:
            if len(plans) < 2:
                print("\nAdd at least one stress scenario first (option 4).")
            else:
                compare_plans(plans)


if __name__ == "__main__":
    main()