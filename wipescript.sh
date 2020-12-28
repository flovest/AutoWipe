#!/bin/bash

# Original Author: Florian Oertel
# Email: florian.oertel@outlook.com
# Version: 0.1

SERVER_START_CMD="<SERVERDIR>/rustserver start"
SERVER_STOP_CMD="<SERVERDIR>/rustserver stop"
BP_WIPE_CMD="<SERVERDIR>/rustserver full-wipe"
MAP_WIPE_CMD="<SERVERDIR>/rustserver wipe"

# 1=Mon;2=Tue;3=Wed;4=Thu;5=Fri;6=Sat;0=Sun
BP_WIPE_DAY=1
MAP_WIPE_DAY=4

# 24h format HHMM
BP_WIPE_TIME=0400
MAP_WIPE_TIME=0400

# needs to be a zone out of here.. /usr/share/zoneinfo/ (!case sensitive!)
TIME_ZONE=CET

# WEEK STARTS WITH MONDAY
# WIPE_TYPES:
# 1 .. WEEKLY
# 2 .. EVERY 2nd WEEK
# 3 .. First Week of Month
# 4 .. Second Week of Month
# 5 .. Third Week of Month
# 6 .. Fourth Week of Month
# 7 .. Fith Week of Month
# example: MAP_WIPE_TYPES=( 2 3 )
# with example it mapwipes every 2nd week begining at $FIRST_MAP_WIPE and every first week of month
BP_WIPE_TYPES=( 3 )
MAP_WIPE_TYPES=( 1 )

# YYYY-MM-DD Format! so 1 needs to be 01 and so on 
FIRST_BP_WIPE="2021-01-07"
FIRST_MAP_WIPE="2020-12-31"

# time in secs how often it checks for wipe | should not be changed
WIPE_CHECK_INTERVAL_SECS=10

# DO NOT CHANGE BELOW HERE
DATE_COMPARE_FORMAT="+'%Y-%m-%d'"

LOG_FILE="/var/log/wipescript.log"

# LOGLEVELS:
# 1 .. FATAL
# 2 .. WARN
# 3 .. INFO
# 4 .. DEBUG
# 5 .. TRACE
LOG_LEVEL=5

function log {
    log_message=$1
    current_log_level=$2

    log_time=$(date +'%Y-%m-%d %H:%M:%S.%3N')

    if [ -z "$current_log_level" ]; then
        current_log_level=5
    fi

    if [[ "$current_log_level" > "$LOG_LEVEL" ]]; then
        return
    fi

    if [[ "$current_log_level" == 1 ]]; then
        current_log_level="FATAL"
    elif [[ "$current_log_level" == 2 ]]; then
        current_log_level="WARN"
    elif [[ "$current_log_level" == 3 ]]; then
        current_log_level="INFO"
    elif [[ "$current_log_level" == 4 ]]; then
        current_log_level="DEBUG"
    elif [[ "$current_log_level" == 5 ]]; then
        current_log_level="TRACE"
    fi

    logmessage="[$log_time][$current_log_level]: $log_message"

    echo $logmessage >> $LOG_FILE
    echo $logmessage
}

# Return Values:
# 0 .. wipe declined
# 1 .. wipe confirmed
function check_wipe_by_type {
    # 1 .. wipe type ()
    # 2 .. wipe day of week (1=Mon;2=Tue;...;0=Sun)
    # 3 .. time of wipe (24h format)
    # 4 .. first day of wipe where we start going to count from!
    # 5 .. last day of wipe we did (can be empty!)
    wipe_type=$1
    wipe_day_of_week=$2
    wipe_time=$3
    first_wipe_day=$4
    last_wipe_date=$5

    current_date=$(TZ=":$TIME_ZONE" date $DATE_COMPARE_FORMAT)
    current_time=$(TZ=":$TIME_ZONE" date +%H%M)
    current_day_of_week=$(TZ=":$TIME_ZONE" date +%a)
    first_wipe_date_compare_format=$(TZ=":$TIME_ZONE" date -d $first_wipe_day $DATE_COMPARE_FORMAT)

    log "~~~~ check_wipe_by_type ~~~~" 4
    log "current_date: $current_date" 4
    log "current_time: $current_time" 4
    log "current_day_of_week: $current_day_of_week" 4
    log "wipe_type: $wipe_type" 4
    log "wipe_day_of_week: $wipe_day_of_week" 4
    log "wipe_time: $wipe_time" 4
    log "first_wipe_day: $first_wipe_day" 4
    log "first_wipe_date_compare_format: $first_wipe_date_compare_format" 4

    # first check if we already wiped today!
    if [[ "$current_date" == "$last_wipe_date" ]]; then
        return_value=0
    # next check if first wipe day is in future!
    elif [[ "$first_wipe_date_compare_format" > "$current_date" ]]; then
        return_value=0
    # check if its the right time to wipe!
    elif [ $wipe_time -gt $current_time ]; then 
        return_value=0
    # check if current date is first wipe day
    elif [[ "$first_wipe_date_compare_format" == "$current_date" ]]; then
        return_value=1
    else
        case $wipe_type in
            1|2) # 1|2 .. WEEKLY | Every 2nd WEEK
                if [ -z "$last_wipe_date" ]; then
                    next_wipe_date=$(TZ=":$TIME_ZONE" date -d "$first_wipe_day + $wipe_type weeks" $DATE_COMPARE_FORMAT)
                else
                    next_wipe_date=$(TZ=":$TIME_ZONE" date -d "$last_wipe_date + $wipe_type weeks" $DATE_COMPARE_FORMAT)
                fi
                if [[ "$next_wipe_date" == "$current_date" ]]; then
                    return_value=1
                fi
                ;;    
            3|4|5|6|7) # 3-7 .. First-Fith Week of Month
                d=$(TZ=":$TIME_ZONE" date -d "today" '+%Y-%m-01')
                di=$(TZ=":$TIME_ZONE" date -d $d '+%w')
                wanted_week=$(TZ=":$TIME_ZONE" date -d "$d $(( di - 1 )) day ago +$((wipe_type-3)) weeks")
                if [[ "$wipe_day_of_week" -eq "0" ]]; then
                    next_wipe_date=$(TZ=":$TIME_ZONE" date -d "$wanted_week +6 days" $DATE_COMPARE_FORMAT)
                else
                    next_wipe_date=$(TZ=":$TIME_ZONE" date -d "$wanted_week +$((wipe_day_of_week - 1)) days")
                fi

                if [[ $(date -d "$next_wipe_date" +'%m') == $(date -d "today" +'%m') ]]; then 
                    next_wipe_date=$(date -d $(( $d + $i )) $DATE_COMPARE_FORMAT);
                    if [[ "$next_wipe_date" == "$current_date" ]]; then
                        return_value=1
                    fi
                fi
                ;;
            *)
                log "unknown wipe_type!" 2
                ;;
        esac
    fi
    return $return_value
}

# returns codes:
# 0 .. do nothing
# 1 .. bpwipe
# 2 .. mapwipe
function check_if_wipe {

    return_value=0

    log "checking bp wipes..." 4
    # check for bp wipe first!!
    all_types_confirmed=false
    for i in "${BP_WIPE_TYPES[@]}"; do
        check_wipe_by_type $i $BP_WIPE_DAY $BP_WIPE_TIME $FIRST_BP_WIPE $last_bp_wipe_date
        wipe_confirmed=$?

        if [ $wipe_confirmed == 1 ]; then 
            return_value=1
        else 
            return_value=0
            break
        fi
    done
    if [ $return_value != 0 ]; then
        return $return_value
    fi


    log "checking map wipes..." 4
    # check for map wipe
    all_types_confirmed=false
    for i in "${MAP_WIPE_TYPES[@]}"; do
        check_wipe_by_type $i $MAP_WIPE_DAY $MAP_WIPE_TIME $FIRST_MAP_WIPE $last_map_wipe_date
        wipe_confirmed=$?

        if [ $wipe_confirmed == 1 ]; then 
            return_value=2
        else 
            return_value=0
            break
        fi

    done

    return $return_value

    log "end of check if wipe"
    return $return_value
}

function do_work {

    while true; do

        check_if_wipe
        return_value=$?

        # check return value (check "check_if_wipe" functions for declaration)
        case $return_value in
            0)
                log "... NOT doing any wipe!" 3
                ;;
            1) # BP WIPE
                log "++++ DOING BLUEPRINT WIPE ++++" 3
                
                log "STOPPING SERVER..." 3
                log "bash -c "$SERVER_STOP_CMD"" 4
                bash -c "$SERVER_STOP_CMD"
                if [[ "$?" != "0" ]]; then
                    log "Failed to bp wipe server" 1
                    continue
                fi

                log "EXECUTING BP WIPE CMD..." 3
                log "bash -c "$BP_WIPE_CMD""
                bash -c "$BP_WIPE_CMD"
                if [[ "$?" != "0" ]]; then
                    log "Failed to bp wipe server" 1
                    continue
                fi

                log "STARTING SERVER..." 3
                log "bash -c "$SERVER_START_CMD"" 4
                bash -c "$SERVER_START_CMD"
                if [[ "$?" != "0" ]]; then
                    log "Failed to start server" 1
                    continue
                fi


                # when successfull set last_bp_wipe_date variable
                last_bp_wipe_date=$(TZ=":$TIME_ZONE" date $DATE_COMPARE_FORMAT)
                log "++++ WIPE DONE ++++" 3
                ;;
            2) # MAP WIPE
                log "++++ DOING MAP WIPE ++++" 3

                log "STOPPING SERVER..." 3
                log "bash -c "$SERVER_STOP_CMD"" 4
                bash -c "$SERVER_STOP_CMD"
                if [[ "$?" != "0" ]]; then
                    log "Failed to bp wipe server" 1
                    continue
                fi

                log "EXECUTING MAP WIPE CMD..." 3
                log "bash -c "$MAP_WIPE_CMD"" 4
                bash -c "$MAP_WIPE_CMD"
                if [[ "$?" != "0" ]]; then
                    log "Failed to map wipe server" 1
                    continue
                fi

                log "STARTING SERVER..." 3
                log "bash -c "$SERVER_START_CMD"" 4
                bash -c "$SERVER_START_CMD"
                if [[ "$?" != "0" ]]; then
                    log "Failed to start server" 1
                    continue
                fi

                # when successfull set last_map_wipe_date variable
                last_map_wipe_date=$(TZ=":$TIME_ZONE" date $DATE_COMPARE_FORMAT)
                log "++++ WIPE DONE ++++" 3
                ;;
            *)
                log "unknown return value!"    
                ;;
        esac

        # sleepppp
        log "### SLEEPING FOR $WIPE_CHECK_INTERVAL_SECS ###"
        log ""
        sleep $WIPE_CHECK_INTERVAL_SECS
    done
}

do_work