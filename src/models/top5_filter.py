import pandas as pd


def passes_filter(jodi, df, digit_scores, config):
    j = str(jodi).zfill(2)

    d1, d2 = int(j[0]), int(j[1])

    # ---------------------------
    # Rule 1: Digit Strength
    # ---------------------------
    digit_score = (digit_scores.get(d1, 0) + digit_scores.get(d2, 0)) / 2
    if digit_score < config.FILTER_MIN_DIGIT_SCORE:
        return False

    # ---------------------------
    # Rule 2: Avoid last result repeat
    # ---------------------------
    last_jodi = str(df.iloc[-1]["jodi"]).zfill(2)
    if j == last_jodi:
        return False

    # ---------------------------
    # Rule 3: Absence control
    # ---------------------------
    last_seen = df[df["jodi"] == j]["date"].max()
    if pd.isna(last_seen):
        return False

    days_absent = (df["date"].max() - last_seen).days
    if days_absent > config.FILTER_MAX_ABSENCE:
        return False

    # ---------------------------
    # Rule 4: Must have signal
    # ---------------------------
    recent_df = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]
    recent_freq = recent_df["jodi"].value_counts(normalize=True).get(j, 0)

    if recent_freq < config.FILTER_MIN_RECENT and days_absent < config.FILTER_MIN_DELAY:
        return False

    return True


def select_top5(top10, df, digit_scores, config):
    selected = []

    for j in top10:
        if passes_filter(j, df, digit_scores, config):
            selected.append(j)

        if len(selected) == 5:
            break

    # fallback (very important)
    if len(selected) < 5:
        for j in top10:
            if j not in selected:
                selected.append(j)
            if len(selected) == 5:
                break

    return selected
