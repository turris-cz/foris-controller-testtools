stored_enabled = True
stored_approvals = False
stored_auto_approve_time = 0


def enabled():
    return stored_enabled


def set_enabled(enabled):
    global stored_enabled
    stored_enabled = enabled


def approvals():
    return stored_approvals


def set_approvals(enabled):
    global stored_approvals
    stored_approvals = enabled


def auto_approve_time():
    return stored_auto_approve_time


def set_auto_approve_time(approve_time):
    global stored_auto_approve_time
    stored_auto_approve_time = approve_time
