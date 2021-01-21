#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SERVER_DIR="/home/rustuser/myrustserver"
SERVER_START_CMD="$SERVER_DIR/rustserver start"
SERVER_STOP_CMD="$SERVER_DIR/rustserver stop"
BP_WIPE_CMD="$SERVER_DIR/rustserver full-wipe"
MAP_WIPE_CMD="$SERVER_DIR/rustserver wipe"
SERVER_UPDATE_CMD="$SERVER_DIR/rustserver update"
SERVER_UPDATE_LGSM_CMD="$SERVER_DIR/rustserver update-lgsm"
SERVER_UPDATE_MODS_CMD="$SERVER_DIR/rustserver mods-update"

# wipe methods: 'bpwipe' or 'mapwipe'
WIPE_METHODS=("mapwipe", "bpwipe")

print_wipe_meths() {
    for I in "${WIPE_METHODS[@]}"
    do    
        joined_str=${joined_str:+$joined_str }$I
    done
    echo "Choose one of these: $joined_str"
}

join() {
    # $1 is sep
    # $2... are the elements to join
    # return is in global variable join_ret
    local sep=$1 IFS=
    join_ret=$2
    shift 2 || shift $(($#))
    join_ret+="${*/#/$sep}"
}

wipe_method=$1
if [ -z "$wipe_method" ]
then
    echo "Wipe method not set!"
    print_wipe_meths
    exit 1
fi

if [[ ! " ${WIPE_METHODS[*]} " == *"$wipe_method"* ]]; then
    echo "Invalid wipe method: '$wipe_method'"
    print_wipe_meths
    exit 1
fi

echo "Stopping server..."
echo "bash -c "$SERVER_STOP_CMD""
bash -c "$SERVER_STOP_CMD"

echo "Updating Server..."
echo "bash -c "$SERVER_UPDATE_CMD""
bash -c "$SERVER_UPDATE_CMD"
if [[ ! $? -eq 0 ]]; then
    echo "Failed to update server"
    exit 1
fi
echo "Finished Update Task successfully!"

echo "Updating LGSM..."
echo "bash -c "$SERVER_UPDATE_LGSM_CMD""
bash -c "$SERVER_UPDATE_LGSM_CMD"
if [[ ! $? -eq 0 ]]; then
    echo "Failed to update LGSM"
    exit 1
fi
echo "Finished Update LGSM Task successfully!"

echo "Updating Mods..."
echo "bash -c "$SERVER_UPDATE_MODS_CMD""
bash -c "$SERVER_UPDATE_MODS_CMD"
if [[ ! $? -eq 0 ]]; then
    echo "Failed to update mods"
    exit 1
fi
echo "Finished Update-Mods Task successfully!"


wipe_cmd=""
if [[ $wipe_method = "bpwipe" ]]; then
    wipe_cmd=$BP_WIPE_CMD
    echo "Doing BP Wipe..."
elif [[ $wipe_method = "mapwipe" ]]; then
    wipe_cmd=$MAP_WIPE_CMD
    echo "Doing Map Wipe..."
else
    "Not supported wipe method!"
    exit 2
fi

echo "bash -c "$wipe_cmd""
bash -c "$wipe_cmd"
if [[ ! $? -eq 0 ]]; then
    echo "Failed executing '$wipe_cmd'"
    exit 1
fi
echo "Finishhed Wipe Task successfully!"

echo "Starting server..."
echo "bash -c "$SERVER_START_CMD""
bash -c "$SERVER_START_CMD"
if [[ ! $? -eq 0 ]]; then
    echo "Failed to start server"
    exit 1
fi

echo "Server started successfully!"
