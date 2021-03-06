#
# parse a tipical nginx error log like this
#
# 2012/11/29 19:30:02
# [error] 15596#0: *4 open() "/srv/active/collected-static/50x.html" failed (2: No such file or directory),
# client: 65.44.217.34,
# server: ,
# request: "GET /api/megapage/poll/?cursor=1354216956 HTTP/1.1",
# upstream: "http://0.0.0.0:9000/api/megapage/poll/?cursor=1354216956",
# host: "165.225.132.103",
# referrer: "http://165.225.132.103/megapage/"


from string import strip
import re
import logging
from datetime import datetime, timedelta
from dateutil.tz import tzoffset

def nginx_error_parser(line, addcalltime=False):
    csv_list = line.split(",")
    date_time_message = csv_list.pop(0).split(" ",2)
    otherinfo = dict()

    for l in csv_list:
        kv = l.split(":",1)
        if len(kv)>0:
            value = strip(kv[1])
            if not value:
                value = "-"
        else:
            value = "-"
        otherinfo[strip(kv[0])] = value

    otherinfo['log_level'] = logging.ERROR

    return date_time_message, otherinfo

def nginx_access_parser(line, addcalltime=False, basepath="http://localhost:5000"):
    re_str = '^(?P<ip>[\d]{1,3}.[\d]{1,3}.[\d]{1,3}.[\d]{1,3})[\s]+-[\s]+-[\s]+\[(?P<date>[\w\W]+)\][\s]+"(?P<request>[\w\W^"]+)"[\s]+(?P<status>[\d]{3})[\s]+(?P<proc>[\d]+)[\s]+"(?P<referrer>[\w\W^"]+)"[\s]+"(?P<useragent>[\w\W^"]+)'
    re_str += '[\s]+(?P<calltime>[\d]+.[\d]+)$' if addcalltime else "$"
    m = re.search(re_str, line)

    dt = m.group('date')
    dt_str = dt.split(" ")
    dt = datetime.strptime(dt_str[0], "%d/%b/%Y:%H:%M:%S")
    dt = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tzoffset(None, timedelta(hours=int(dt_str[1][0:-2]), minutes=int(dt_str[1][-2:])).total_seconds()))
    
    request_object = {}
    temp = m.group('request').split(" ")
    
    request_object["method"] = temp[0]
    path = "-"
    try:
        query_temp = temp[1].split("?")
    except:
        q_obj = "-"
    else:
        request_object["url"] = "%s%s" % (basepath, query_temp[0])
        path = query_temp[0]
        if len(query_temp) > 1:
            request_object["query_string"] = query_temp[1]
            
            q_temp = query_temp[1].split("&")
            q_obj = {}
            for q in q_temp:
                if "=" in q:
                    k, v = q.split("=")
                    q_obj[k] = v
            if not q_obj:
                q_obj = "-"
        else:
            q_obj = "-"
    request_object["User-Agent"] = m.group('useragent')

    otherinfo = dict(ip=m.group('ip'), request=request_object, status=m.group('status'), referrer=m.group('referrer'), useragent=m.group('useragent'), QueryObject=q_obj, urlpath=path)

    if addcalltime:
        otherinfo["call_time"] = m.group('calltime')

    otherinfo['log_level'] = logging.INFO

    return dt.strftime("%Y/%b/%d %H:%M:%S").split(" ")+[m.group('request')], otherinfo
