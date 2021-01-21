#!/usr/bin/env python3

import os
import argparse
import pytz
import json 

from time import sleep
from enum import Enum
from datetime import datetime as dt
from datetime import date
from datetime import timedelta

from returncodes import ReturnCodes as rc
from simplelogger import *


VERSION_STRING="1.0.0"
AUTHOR="Florian Oertel";
AUTHOR_EMAIL="florian.oertel@outlook.com";

SCRIPT_DIR=os.path.dirname(os.path.realpath(__file__))
LOCAL_TIMEZONE=dt.now().astimezone().tzinfo

#default vars
wipe_check_interval_seconds=10
date_parse_format="%Y-%m-%d"
date_parse_format_repstring="%%Y-%%m-%%d"
bp_wipe_command=os.path.join(SCRIPT_DIR, "wipe.sh bpwipe")
map_wipe_command=os.path.join(SCRIPT_DIR, "wipe.sh mapwipe")
log_file_location=os.path.join(SCRIPT_DIR, "autowipe.log")
log_level=6
logger_obj=None
last_bp_wipe_date=None
last_map_wipe_date=None
wipe_command_retries_on_fail=2
current_bp_wipe_retries=0
current_map_wipe_retries=0
append_date_to_logfile_name=True


class WipeAction(Enum):
    NONE=0,
    BP_WIPE=1,
    MAP_WIPE=2

def __load_configuration(configuration_location):
    global bp_wipe_days
    global map_wipe_days
    global bp_wipe_time
    global map_wipe_time
    global bp_wipe_types
    global map_wipe_types
    global first_bp_wipe_date
    global first_map_wipe_date
    global configuration_path

    global wipe_check_interval_seconds
    global date_parse_format
    global bp_wipe_command
    global map_wipe_command
    global log_file_location
    global log_level
    global time_zone
    global wipe_command_retries_on_fail
    global append_date_to_logfile_name

    try:
        with open(configuration_location) as json_file:
            data = json.load(json_file)
            
            # check first dateformat!!! so we can parse dates in correct way
            if 'date_parse_format' in data:
                date_parse_format = data['date_parse_format']

            # now parse req elems
            if 'bp_wipe_days' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('bp_wipe_days'))
            else:
                bp_wipe_days = [int(numeric_string) for numeric_string in data['bp_wipe_days']]

            if 'map_wipe_days' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('map_wipe_days'))
            else:
                map_wipe_days = [int(numeric_string) for numeric_string in data['map_wipe_days']]

            if 'bp_wipe_time' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('bp_wipe_time'))
            else:
                bp_wipe_time = data['bp_wipe_time']

            if 'map_wipe_time' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('map_wipe_time'))
            else:
                map_wipe_time = data['map_wipe_time']

            if 'bp_wipe_types' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('bp_wipe_types'))
            else:
                bp_wipe_types = [int(numeric_string) for numeric_string in data['bp_wipe_types']]

            if 'map_wipe_types' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('map_wipe_types'))
            else:
                map_wipe_types = [int(numeric_string) for numeric_string in data['map_wipe_types']]

            if 'first_bp_wipe' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('first_bp_wipe'))
            else:
                first_bp_wipe_date = dt.strptime(data['first_bp_wipe'], date_parse_format).date()

            if 'first_map_wipe' not in data:
                raise Exception('Missing Configuration Element \'{0}\''.format('first_map_wipe'))
            else:
                first_map_wipe_date = dt.strptime(data['first_map_wipe'], date_parse_format).date()


            # optional elems
            if 'wipe_check_interval_seconds' in data:
                wipe_check_interval_seconds = int(data['wipe_check_interval_seconds'])

            if 'bp_wipe_command' in data:
                bp_wipe_command = data['bp_wipe_command']

            if 'map_wipe_command' in data:
                map_wipe_command = data['map_wipe_command']

            if 'log_file_location' in data:
                log_file_location = data['log_file_location']

            if 'log_level' in data:
                log_level = int(data['log_level'])
                

            if 'time_zone' in data:
                try:
                    time_zone = pytz.timezone(data['time_zone'])
                except Exception:
                    log("Invalid timezone: '{0}'! Using local timezone '{1}' instead.".format(data['time_zone'], LOCAL_TIMEZONE), LogLevel.WARN)
                    time_zone=LOCAL_TIMEZONE
            else:
                time_zone=LOCAL_TIMEZONE

            if 'wipe_command_retries_on_fail' in data:
                wipe_command_retries_on_fail = int(data['wipe_command_retries_on_fail'])

            if 'append_date_to_logfile_name' in data:
                append_date_to_logfile_name = bool(data['append_date_to_logfile_name'])

    except Exception as ex:
        raise Exception("Error while loading configuration file '{0}'! Error Message: '{1}'".format(configuration_location, str(ex)))

def __parse_args():
    global bp_wipe_days
    global map_wipe_days
    global bp_wipe_time
    global map_wipe_time
    global bp_wipe_types
    global map_wipe_types
    global first_bp_wipe_date
    global first_map_wipe_date
    global configuration_path

    global wipe_check_interval_seconds
    global date_parse_format
    global bp_wipe_command
    global map_wipe_command
    global log_file_location
    global log_level
    global time_zone
    global wipe_command_retries_on_fail

    try:

        parser = argparse.ArgumentParser(description="Available Arguments:".format(VERSION_STRING))

        req = parser.add_argument_group("Required Arguments if -c|--configuration <configuration_path> argument is not present!")
        req.add_argument("-B", '--bp-wipe-days', nargs='+', type=int, choices=range(1, 8), help="List of blueprint wipe days in a week, where 1 = Monday and 7 = Sunday.")
        req.add_argument("-M", '--map-wipe-days', nargs='+', type=int, choices=range(1, 8), help="List of map wipe days in a week, where 1 = Monday and 7 = Sunday.")
        req.add_argument("-T", '--bp-wipe-time', type=str, help="Specifies time of blueprint wipes in format 'HHMM'.")
        req.add_argument("-t", '--map-wipe-time', type=str, help="Specifies time of map wipes in format 'HHMM'.")
        req.add_argument('--bp-wipe-types', nargs='+', type=int, choices=range(1, 8), help="List of wipe types used to check for blueprint wipes.")
        req.add_argument('--map-wipe-types', nargs='+', type=int, choices=range(1, 8), help="List of wipe types used to check for map wipes.")
        req.add_argument('--first-bp-wipe', type=str, help="Date of first blueprint wipe in format requarding to date_format. See optional argument 'date-format'.")
        req.add_argument('--first-map-wipe', type=str, help="Date of first map wipe in format requarding to date_format. See optional argument 'date-format'.")

        opt = parser.add_argument_group("Optional Arguments")
        opt.add_argument('-c', '--configuration', type=str, help="Sets location of autowipe script configuration. If argument is present, any other given argument is ignored.")
        opt.add_argument('-i', '--interval', type=int, help="Wipe check interval in seconds'. Default is {0}".format(wipe_check_interval_seconds))
        opt.add_argument('--date-format', type=str, help="Overwrites the default date format '{0}', that is used to parse dates from arguments.".format(date_parse_format_repstring))
        opt.add_argument('--bp-wipe-command', type=str, help="Overwrites the default blueprint wipe command '{0}'.".format(bp_wipe_command))
        opt.add_argument('--map-wipe-command', type=str, help="Overwrites the default map wipe command '{0}'.".format(map_wipe_command))
        opt.add_argument('--log-file-location', type=str, help="Overwrites the default logfile location '{0}'.".format(log_file_location))
        opt.add_argument('--log-level', type=int, choices=range(1, 7), help="Overwrites the default log level '{0}'.".format(log_level))
        opt.add_argument('--time-zone', type=str, help="Default is local timezone. Used to calculate current and future dates")
        opt.add_argument('--retries', type=int, help="Amount of retries before this script terminates when a wipe command failed. Default: {0}".format(wipe_command_retries_on_fail))

        args = parser.parse_args()

    except argparse.ArgumentError as ex:
        log(str(ex), LogLevel.ERROR)
        exit(rc.EXIT_ARGUMENT_ERROR)

    if args.configuration:
        __load_configuration(args.configuration)
        return

    # check first dateformat!!! so we can parse dates in correct way
    if args.date_format:
        date_parse_format = args.date_format

    #req args if config path not present
    bp_wipe_days = args.bp_wipe_days
    map_wipe_days = args.map_wipe_days
    bp_wipe_time = args.bp_wipe_time
    map_wipe_time = args.map_wipe_time
    bp_wipe_types = args.bp_wipe_types
    map_wipe_types = args.map_wipe_types
    first_bp_wipe_date = dt.strptime(args.first_bp_wipe, date_parse_format).date()
    first_map_wipe_date = dt.strptime(args.first_map_wipe, date_parse_format).date()


    #opt args if config path is not present
    if args.interval:
        if args.interval > 5:
            wipe_check_interval_seconds = args.interval
        else:
            raise ValueError("Value of paramter --interval is below 5!")
    
    
    
    if args.bp_wipe_command:
        bp_wipe_command = args.bp_wipe_command

    if args.map_wipe_command:
        map_wipe_command = args.map_wipe_command

    if args.log_file_location:
        if os.path.exists(args.log_file_location):
            log_file_location = args.log_file_location
        else:
            raise FileNotFoundError("log_file_location '{0}' does not exist!".format(args.log_file_location))

    if args.log_level:
        log_level = args.log_level

    if args.time_zone:
        try:
            time_zone=pytz.timezone(args.time_zone)
        except Exception:
            log("Invalid timezone: '{0}'! Using local timezone '{1}' instead.".format(args.time_zone, LOCAL_TIMEZONE), LogLevel.WARN)
            time_zone=LOCAL_TIMEZONE
    else:
        time_zone=LOCAL_TIMEZONE


    if args.retries:
        if args.retries:
            wipe_command_retries_on_fail = args.retries

def print_current_vars():

    log("", LogLevel.TRACE)
    log("# CURRENT VARS #", LogLevel.TRACE)

    log("VERSION_STRING: '{0}'".format(VERSION_STRING), LogLevel.TRACE)
    log("SCRIPT_DIR: '{0}'".format(SCRIPT_DIR), LogLevel.TRACE)


    log("wipe_check_interval_seconds: '{0}'".format(wipe_check_interval_seconds), LogLevel.TRACE)
    log("time_zone: '{0}'".format(time_zone), LogLevel.TRACE)
    log("date_parse_format: '{0}'".format(date_parse_format), LogLevel.TRACE)
    log("date_parse_format_repstring: '{0}'".format(date_parse_format_repstring), LogLevel.TRACE)
    log("bp_wipe_command: '{0}'".format(bp_wipe_command), LogLevel.TRACE)
    log("map_wipe_command: '{0}'".format(map_wipe_command), LogLevel.TRACE)
    log("log_file_location: '{0}'".format(log_file_location), LogLevel.TRACE)
    log("bp_wipe_days: '{0}'".format(bp_wipe_days), LogLevel.TRACE)
    log("map_wipe_days: '{0}'".format(map_wipe_days), LogLevel.TRACE)
    log("bp_wipe_time: '{0}'".format(bp_wipe_time), LogLevel.TRACE)
    log("map_wipe_time: '{0}'".format(map_wipe_time), LogLevel.TRACE)
    log("bp_wipe_types: '{0}'".format(bp_wipe_types), LogLevel.TRACE)
    log("map_wipe_types: '{0}'".format(map_wipe_types), LogLevel.TRACE)
    log("first_bp_wipe_date: '{0}'".format(first_bp_wipe_date), LogLevel.TRACE)
    log("first_map_wipe_date: '{0}'".format(first_map_wipe_date), LogLevel.TRACE)
    log("log_level: '{0}'".format(log_level), LogLevel.TRACE)

    log("##", LogLevel.TRACE)
    log("", LogLevel.TRACE)

def _get_n_weekday(year, month, day_of_week, n): 
    count = 0 
    for i in range(1, 32): 
        try: 
            d = date(year, month, i) 
        except ValueError: 
            break 
        if d.isoweekday() == day_of_week: 
            count += 1 
        if count == n:
            return d
    return None

def _get_week_number(date):
    return ((date - dt(date.year, 1, 1).date()).days // 7) + 1

def check_wipe_by_type(wipe_type, wipe_days, wipe_time, first_wipe_date, last_wipe_date, time_zone, current_date=None, current_time=None):
    log("check_wipe_by_type()", LogLevel.TRACE)

    if current_date is None:
        current_date = dt.now(time_zone).date()
    if current_time is None:
        current_time = dt.now(time_zone).strftime("%H%M")
    first_date_of_month=dt(current_date.year, current_date.month, 1).date()

    log("current_date: {0}".format(current_date), log_level=LogLevel.TRACE)
    log("current_time: {0}".format(current_time), log_level=LogLevel.TRACE)
    log("first_wipe_date: {0}".format(first_wipe_date), log_level=LogLevel.TRACE)
    log("last_wipe_date: {0}".format(last_wipe_date), log_level=LogLevel.TRACE)
    log("first_date_of_month: {0}".format(first_date_of_month), log_level=LogLevel.TRACE)

    # first check if we already wiped today!
    if current_date == last_wipe_date:
        log("HIT current_date == last_wipe_date", LogLevel.TRACE)
        return False
    # next check if first wipe day is in future!
    if first_wipe_date > current_date:
        log("HIT first_wipe_date > current_date", LogLevel.TRACE)
        return False
    # check if its the right time to wipe!
    if wipe_time > current_time:
        log("HIT wipe_time > current_time", LogLevel.TRACE)
        return False
    # check if current date is first wipe day
    if current_date == first_wipe_date:
        log("HIT current_date == first_wipe_date", LogLevel.TRACE)
        return True
    else:
        # 1 -> WEEKLY
        if wipe_type == 1:
            # we calculate +1 here so we have some day number structure as in params.. 1 = Monday 7 = Sunday. By default weekday() returns in shema 0 = Monday, 6 = Sunday
            current_day_of_week = current_date.weekday() + 1
            for day in wipe_days:
                for i in range(1, 6):
                    next_date=_get_n_weekday(current_date.year, current_date.month, day, i)
                    if next_date is not None and next_date == current_date:
                        log("HIT Type 1 wipe_type: {0} next_wipe_date: {1} current_date: {2} wipe_day: {3}".format(wipe_type, next_date, current_date, day), LogLevel.TRACE)
                        return True
        elif wipe_type == 2:            
            for day in wipe_days:
                for i in range(1, 6):
                    next_date=_get_n_weekday(current_date.year, current_date.month, day, i)
                    if next_date is None:
                        continue
                    next_date_week=_get_week_number(next_date)
                    if last_wipe_date is not None:
                        last_wipe_week=_get_week_number(last_wipe_date)
                    else:
                        last_wipe_week=_get_week_number(first_wipe_date)

                    if (next_date_week - last_wipe_week) == 2:
                        if next_date is not None and next_date == current_date:
                            log("HIT Type 2 wipe_type: {0} next_wipe_date: {1} current_date: {2} wipe_day: {3} next_wipe_date_week: {4} last_wipe_week: {5}".format(wipe_type, next_date, current_date, day, next_date_week, last_wipe_week), LogLevel.TRACE)
                            return True
        # 3-7 .. 1st - 5th Weekday of Month
        elif wipe_type >= 3 and wipe_type <= 7:
            for day in wipe_days:
                
                if wipe_type == 3:
                    nth_day = 1
                elif wipe_type == 4:
                    nth_day = 2
                elif wipe_type == 5:
                    nth_day = 3
                elif wipe_type == 6:
                    nth_day = 4
                elif wipe_type == 7:
                    nth_day = 5
                else:
                    raise Exception("This should never ever happen! Wipe Type unkown!")

                next_wipe_date = _get_n_weekday(current_date.year, current_date.month, day, nth_day)
                if next_wipe_date is not None and next_wipe_date == current_date:
                    return True


    return False

def check_if_wipe(bp_wipe_types, map_wipe_types, bp_wipe_days, map_wipe_days, bp_wipe_time, map_wipe_time, first_bp_wipe_date, first_map_wipe_date, last_bp_wipe_date, last_map_wipe_date, time_zone):
    '''
        Returns WipeAction Enum Value.
    '''
    log("check_if_wipe()", LogLevel.TRACE)

    #check for bp wipe first!
    log("Checking for Blueprint Wipes...")
    for wipe_type in bp_wipe_types:
        wipe_confirmed = check_wipe_by_type(wipe_type, bp_wipe_days, bp_wipe_time, first_bp_wipe_date, last_bp_wipe_date, time_zone)
        if (wipe_confirmed):
            return WipeAction.BP_WIPE

    #check for map wipe first!
    log("Checking for Map Wipes...")
    for wipe_type in map_wipe_types:
        wipe_confirmed = check_wipe_by_type(wipe_type, map_wipe_days, map_wipe_time, first_map_wipe_date, last_map_wipe_date, time_zone)
        if (wipe_confirmed):
            return WipeAction.MAP_WIPE

    return WipeAction.NONE

def run_wipe_process(wipe_command):
    import subprocess

    log("~", LogLevel.INFO)
    log("=====================", LogLevel.INFO)
    log("Starting Wipe Process..", LogLevel.INFO)

    log("Executing Command: '{0}'".format(wipe_command), LogLevel.INFO)

    splitted_command = wipe_command.split(' ')

    try:
        with subprocess.Popen(splitted_command, stdout=subprocess.PIPE) as process:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                log(line.decode(), LogLevel.INFO)
        log("ReturnCode: '{0}'".format(process.returncode))

        if process.returncode != 0:
            raise Exception("Command returncode does not equal 0!")
    except Exception as ex:
        log("Failed while executing Wipe Command '{0}'! Error Message: '{1}'".format(wipe_command, ex), LogLevel.ERROR)
        return None

    log("Wipe Process ended!", LogLevel.INFO)
    log("=====================", LogLevel.INFO)
    log("~", LogLevel.INFO)

    return True

def do_run():
    global last_bp_wipe_date
    global last_map_wipe_date
    global current_bp_wipe_retries
    global current_map_wipe_retries

    log("do_run()", LogLevel.TRACE)

    while True:
        wipe_action_to_trigger = check_if_wipe(bp_wipe_types, map_wipe_types, bp_wipe_days, map_wipe_days, bp_wipe_time, map_wipe_time, first_bp_wipe_date, first_map_wipe_date, last_bp_wipe_date, last_map_wipe_date, time_zone)

        if wipe_action_to_trigger == WipeAction.BP_WIPE:
            if current_bp_wipe_retries > 0:
                log("Execuing Blueprint Wipe! Retry: {0}".format(current_bp_wipe_retries), LogLevel.INFO)
            else:
                log("Execuing Blueprint Wipe!", LogLevel.INFO)
            if run_wipe_process(bp_wipe_command) is True:
                current_bp_wipe_retries=0
                last_bp_wipe_date=dt.now(time_zone).date()
            else:
                log("Blueprint Wipe Failed!", LogLevel.WARN)
                current_bp_wipe_retries+=1
                if wipe_command_retries_on_fail == -1 or wipe_command_retries_on_fail >= current_bp_wipe_retries:
                    log("Continue..", LogLevel.INFO)
                    continue
                else:
                    log("Autowipe failed due to wipe command failure!", LogLevel.ERROR)
                    exit(rc.EXIT_WIPE_FAILED)


        elif wipe_action_to_trigger == WipeAction.MAP_WIPE:
            if current_map_wipe_retries > 0:
                log("Execuing Map Wipe! Retry: {0}".format(current_map_wipe_retries), LogLevel.INFO)
            else:
                log("Execuing Map Wipe!", LogLevel.INFO)
            if run_wipe_process(map_wipe_command) is True:
                current_map_wipe_retries=0
                last_map_wipe_date=dt.now(time_zone).date()
            else:
                log("Map Wipe Failed!", LogLevel.WARN)
                current_map_wipe_retries+=1
                if wipe_command_retries_on_fail == -1 or wipe_command_retries_on_fail >= current_map_wipe_retries:
                    log("Continue..", LogLevel.INFO)
                    continue
                else:
                    log("Autowipe failed due to wipe command failure!", LogLevel.ERROR)
                    exit(rc.EXIT_WIPE_FAILED)
        else:
            log("Any wipes executed!", LogLevel.DEBUG)

        sleep(wipe_check_interval_seconds)

def log(message, log_level=LogLevel.DEBUG):
    if logger_obj is not None:
        logger_obj.log(message, log_level)
    else:
        print(message)


def get_logger(logger_name="AutoWipe", log_file_location=None, log_level=LogLevel.INFO):
    logger_obj = SimpleLogger(logger_name, log_file_location, log_level, append_date_to_logfile_name)
    log("created logger!", log_level=LogLevel.TRACE)
    return logger_obj

def main():
    global logger_obj

    try:
        __parse_args()
    except Exception as ex:
        if hasattr(ex, 'message'):
            log("Failed to parse arguments! Error Message: '{0}'",format(ex.message), LogLevel.ERROR)
        else:
            log("Failed to parse arguments! Error: '{0}'".format(ex), LogLevel.ERROR)
        exit(rc.EXIT_PARSE_ARGS_FAILED)


    logger_obj = get_logger(log_file_location=log_file_location, log_level=log_level)
    
    log("Started AutoWipe Version '{0}' by '{1}'".format(VERSION_STRING, AUTHOR), LogLevel.INFO)

    do_run()

if __name__ == '__main__':
    main()


