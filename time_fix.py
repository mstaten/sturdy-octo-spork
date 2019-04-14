
def rotate_hr(hour):
    rot = -5
    return (hour + rot) % 24
    

def convert_hr(hour):
    if hour > 12:
        hour -= 12
    return hour


def rotate_day(pub_date):
    day = pub_date.day
    hr = pub_date.hour
    if day == 1: # it'll just have to be wrong, whatever
        return day
    elif hr < 5:
        # it's tomorrow, change day
        day -= 1
    return day


def rotate_time(pub_date):
    hr = pub_date.hour
    minute = pub_date.minute
    if minute < 10:
        minute = '0' + str(minute)

    rotated = rotate_hr(hr)
    converted = convert_hr(rotated)
    
    if rotated >= 12 and rotated != 24:
        period = 'PM'
    else:
        period = 'AM'
    time = '{0}:{1} {2}'.format(converted, minute, period)
    return time