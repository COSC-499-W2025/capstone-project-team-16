#scoring system

def compute_project_score(
    *,
    volume_score,
    activity_score,
    variety_score,
    duration_score,
    collab_bonus,
    branch_bonus,
    merge_bonus,
    commit_bonus,
):
    """
    Centralized project scoring formula.

    Keeps scoring logic in one place so it can be
    tuned without touching analysis code.
    """

    return (
        volume_score
        + activity_score
        + variety_score
        + duration_score
        + collab_bonus
        + branch_bonus
        + merge_bonus
        + commit_bonus
    )
