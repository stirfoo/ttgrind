# util.py
# S. Edward Dolan
# Sunday, January 26 2025

def ms2hms(ms):
    """Convert milliseconds to hours, minutes and seconds.
    Return a string.
    """
    s = int(ms/1000) % 60
    m = int(ms/(1000*60)) % 60
    h = int(ms/(1000*60*60)) % 60
    if h > 0:
        return '%dh %02dm %02ds' % (h, m, s)
    elif m > 0:
        return '%dm %02ds' % (m, s)
    else:
        return '%ds' % s
    
