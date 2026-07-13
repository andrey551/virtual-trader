def calculate_mape(actuals, predicteds) -> float:
    errors = []
    for act, pred in zip(actuals, predicteds):
        if act and act > 0:
            errors.append(abs(act - pred) / act)
    if errors:
        return round((sum(errors) / len(errors)) * 100.0, 2)
    return None

def calculate_trend_accuracy(actuals, predicteds, base_price: float) -> float:
    act_prev = base_price
    pred_prev = base_price
    matches = 0
    for act, pred in zip(actuals, predicteds):
        act_dir = 1 if act > act_prev else (-1 if act < act_prev else 0)
        pred_dir = 1 if pred > pred_prev else (-1 if pred < pred_prev else 0)
        if act_dir == pred_dir:
            matches += 1
        act_prev = act
        pred_prev = pred
    return round((matches / len(actuals)) * 100.0, 2)
