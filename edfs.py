"""
###############################
    George Blombach
    USC ID 2416-0961-99
    DSCI 551 - Spring 2023
    Homework #2
    February 24, 2023

    File:   edfs.py

    Desc:   In this homework, you are asked to emulate the file system structure of HDFS using Firebase and allow
            the export of its structure in the XML format. The emulated HDFS (or EDFS) should support ls, create,
            mkdir, rmdir, rm, and export commands as detailed below.

    Syntax: python edfs.py -create <path-to-file>
            python edfs.py -export output.xml
            python edfs.py -ls <dir>
            python edfs.py -mkdir <path>
            python edfs.py -rm <path-to-file>
            python edfs.py -rmdir <path>

    Notes:  Permitted python libraries are - base64, json, requests, sys, uuid, fileinput
            firebase URL: https://blombach-dsci-551-hw2-default-rtdb.firebaseio.com/

###############################
"""
import sys
import requests
import json

firebase_url = "https://blombach-dsci-551-hw2-default-rtdb.firebaseio.com/"
system_message = "Something is missing or incorrect. The syntax for this command is:\r\n\t python3 edfs.py [OPTION] [FILE OR /PATH] \r\n\t\t\t" \
                 "-create <path-to-file>\r\n\t\t\t-export output.xml \r\n\t\t\t-ls <dir> \r\n\t\t\t-mkdir <path>" \
                 "\r\n\t\t\t-rm <path-to-file> \r\n\t\t\t-rmdir <path>"
success_message = " was created successfully."
error_message = " Error creating "


def getNextInode():
    results = requests.get(firebase_url + 'INodeSection/.json?orderBy="$key"&limitToLast=1')
    json_data = json.loads(results.text)
    key = list(json_data.keys())
    currentInode = int(key[0])
    nextInode = currentInode + 1
    return nextInode


def doesItExist(start, path, object_type):
    status = False
    results = requests.get(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')
    #print("results ", results.text)
    if results.text != "{\"" + str(start) + "\"" + ":\"parent\"}":
        json_data = json.loads(results.text)
        keys = list(json_data.keys())
        inode = ""
        for key in keys:
            results = requests.get(firebase_url + 'INodeSection/' + key + '/.json')
            temp = json.loads(results.text)
            name = temp['name']
            nodeType = temp['type']

            if path == name and object_type == nodeType:
                status = True
                inode = key
            # print(key, path, name)
    if status:
        return True, inode
    else:
        return False, 9


def main():
    if len(sys.argv) == 3:
        command = sys.argv[1]
        option = sys.argv[2]

        # -CREATE
        if command == "-create":
            if option[0] == "/" and len(option) > 1:
                options = option.split("/")
                options[0] = "/"  # set root
                start = 7000  # always start at root
                success = True
                x = 0
                while x < len(options)-1:
                    path = options[x]
                    if path != "/":
                        check, child = doesItExist(start, path, "directory")
                        #print("create check", start, path, check, child)
                        if check:
                            parent = start
                            start = child
                            success = True
                        else:
                            success = False
                            break  # quit processing because path is invalid
                    x += 1
                if success:
                    # check if file exists
                    file = options[x]
                    check, child = doesItExist(start, file, "file")
                    #print(check, file, child)
                    if not check:
                        #get next inode
                        newInode = getNextInode()
                        requests.put(firebase_url + 'INodeSection/' + str(newInode) + '.json', data='{"name": "' + file
                                                    + '","type":"file"}')
                        requests.patch(firebase_url + 'INodeDirectorySection/' + str(start) + '.json', data='{"'
                                                    + str(newInode) + '":"child"}')
                        print("The file " + option + " was created successfully.")
                    else:
                        print("The file " + option + " already exists.")
                else:
                    print("Error. Invalid path")
            else:
                print("Path must include / but cannot be only root directory .")
                print(system_message)

        # -EXPORT
        elif command == "-export":
            test = 1

        # -LS
        elif command == "-ls":
            if option[0] == "/" and len(option) > 1:
                options = option.split("/")
                options[0] = "/"  # set root
                start = 7000  # always start at root
                success = False
                for path in options:
                    if path != "/":
                        check, child = doesItExist(start, path, "directory")
                        #print("ls check", start, path, check, child)
                        if check:
                           parent = start
                           start = child
                           success = True
                        else:
                           success = False
                           break  # quit processing because path is invalid
                if success:
                    #get contents of folder
                    results = requests.get(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')
                    #print(results.text)
                    if results.text != "{\"" + str(start) + "\"" + ":\"parent\"}":
                        json_data = json.loads(results.text)
                        keys = list(json_data.keys())
                        inode = ""
                        for key in keys:
                            if key != start:
                                results = requests.get(firebase_url + 'INodeSection/' + key + '/.json')
                                temp = json.loads(results.text)
                                name = temp['name']
                                nodeType = temp['type']
                                print(name)

                else:
                    print("The path " + option + " does not exist.")
            elif option[0] == "/" and len(option) == 1:
                results = requests.get(firebase_url + 'INodeDirectorySection/7000.json')
                if results.text != "{\"7000\":\"parent\"}":
                    json_data = json.loads(results.text)
                    keys = list(json_data.keys())
                    inode = ""
                    for key in keys:
                        if key != "7000":
                            results = requests.get(firebase_url + 'INodeSection/' + key + '/.json')
                            temp = json.loads(results.text)
                            name = temp['name']
                            nodeType = temp['type']
                            print(name)
            else:
                print("Path must include / but cannot be only root directory .")
                print(system_message)

        # -MKDIR
        elif command == "-mkdir":
            if option[0] == "/" and len(option) > 1:
                options = option.split("/")
                options[0] = "/"  # set root
                start = 7000  # always start at root
                success = False
                for path in options:
                    if path != "/":
                        check, nextStart = doesItExist(start, path, "directory")
                        #print(path, check, nextStart)
                        if check:
                            start = nextStart
                        else:
                            # create the directory inode and add to inode directory
                            newInode = getNextInode()
                            #print(newInode)
                            requests.put(firebase_url + 'INodeSection/' + str(newInode) + '.json', data='{"name": "'
                                                        + path + '","type":"directory"}')
                            requests.patch(firebase_url + 'INodeDirectorySection/.json', data='{"'
                                                        + str(newInode) + '":""}')
                            requests.patch(firebase_url + 'INodeDirectorySection/' + str(newInode) + '.json', data='{"'
                                                        + str(newInode) + '":"parent"}')
                            requests.patch(firebase_url + 'INodeDirectorySection/' + str(start) + '.json', data='{"'
                                                        + str(newInode) + '":"child"}')
                            start = newInode
                            success = True
                if success:
                    print(option + " was created successfully.")
                else:
                    print(option + " already exists.")
            else:
                print("Path must include / but cannot be only root directory .")
                print(system_message)

        # -RM
        elif command == "-rm":
            if option[0] == "/" and len(option) > 1:
                options = option.split("/")
                options[0] = "/"  # set root
                start = 7000  # always start at root
                success = True
                x = 0
                while x < len(options) - 1:
                    path = options[x]
                    if path != "/":
                        check, child = doesItExist(start, path, "directory")
                        # print("create check", start, path, check, child)
                        if check:
                            parent = start
                            start = child
                            success = True
                        else:
                            success = False
                            break  # quit processing because path is invalid
                    x += 1
                if success:
                    # check if file exists
                    file = options[x]
                    check, child = doesItExist(start, file, "file")
                    # print(check, file, child)
                    if check:
                        #print(child, start)
                        requests.delete(firebase_url + 'INodeSection/' + str(child) + '.json')
                        requests.delete(firebase_url + 'INodeDirectorySection/' + str(start) + "/" + str(child)
                                        + '.json')
                        print("The file " + option + " was deleted successfully.")
                    else:
                        print("The file " + option + " does not exist.")
                else:
                    print("Error. Invalid path")
            else:
                print("Path must include / but cannot be only root directory .")
                print(system_message)

        # -RMDIR
        elif command == "-rmdir":
            if option[0] == "/" and len(option) > 1:
                options = option.split("/")
                options[0] = "/"  # set root
                start = 7000  # always start at root
                success = False
                for path in options:
                    if path != "/":
                        check, child = doesItExist(start, path, "directory")
                        print("del check", start, path, check, child)
                        if check:
                            parent = start
                            start = child
                            success = True
                        else:
                            success = False
                            break #quit processing because path is invalid
                if success:
                    #check if directory is empty
                    results = requests.get(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')
                    #print(results.text)
                    if results.text == "{\"" + str(start) + "\"" + ":\"parent\"}":
                        requests.delete(firebase_url + 'INodeDirectorySection/' + str(parent) + "/" + str(start)
                                        + '.json')
                        requests.delete(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')

                        requests.delete(firebase_url + 'INodeSection/' + str(start) + '.json')
                        print(option + " was deleted successfully.")
                    else:
                        print(option + " is not empty and was not deleted.")
            else:
                print("Path must include / but cannot be only root directory .")
                print(system_message)
        else:
            print(system_message)
    else:
        print(system_message)


if __name__ == "__main__":
    main()
