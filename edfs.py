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

    Firebase:   firebase URL: https://blombach-dsci-551-hw2-default-rtdb.firebaseio.com/

                Structure for empty root:
                INodeSection
                    7000
                        name: "/"
                        type: root
                INodeDirectorySection
                    7000
                        7000:parent

    Notes:  Permitted python libraries are - base64, json, requests, sys, uuid, fileinput



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
report = ""

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
    #print("results ", results.text, start)
    if results.text != "{\"" + str(start) + "\"" + ":\"parent\"}":
        json_data = json.loads(results.text)
        keys = list(json_data.keys())
        inode = ""
        #print(keys)
        for key in keys:
            results = requests.get(firebase_url + 'INodeSection/' + key + '/.json')
            temp = json.loads(results.text)
            name = temp['name']
            nodeType = temp['type']
            #print("start", start, "key ", key, "type", nodeType)
            if path == name and object_type == nodeType and key != start:
                status = True
                inode = key
                #print(key, path, name, nodeType)
    if status:
        return True, inode
    else:
        return False, 9

def getChildren(start, level):
    global report

    results = requests.get(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')
    if results.text != "{\"" + str(start) + "\"" + ":\"parent\"}":
        json_data = json.loads(results.text)
        keys = list(json_data.keys())

        #print(keys)
        for key in keys:
            #print(key)
            results = requests.get(firebase_url + 'INodeSection/' + key + '/.json')
            temp = json.loads(results.text)
            #print(temp)
            name = temp['name']
            nodeType = temp['type']
            #print("start", start, "key ", key, "type", nodeType)
            if key != start:
                if nodeType == "file":
                    report += "\t" * level + "<" + name + "/>\r\n"
                    #print("\t" * level + "<" + name + "/>")
                if nodeType == "directory":
                    report += "\t" * level + "<" + name + ">\r\n"
                    #print("\t" * level + "<" + name + ">")
                    #recursive call for iterating subdirectories
                    getChildren(key, level + 1)
                if nodeType == "directory":
                    report += "\t" * level + "</" + name + ">\r\n"
                    #print("\t" * level + "</" + name + ">")

    return report


def create(option, options, start, success, x):
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
        if not check:
            # get next inode
            newInode = getNextInode()
            requests.put(firebase_url + 'INodeSection/' + str(newInode) + '.json', data='{"name": "' + file
                                                                                        + '","type":"file"}')
            requests.patch(firebase_url + 'INodeDirectorySection/' + str(start) + '.json', data='{"'
                                                                                                + str(
                newInode) + '":"child"}')
            print("The file " + option + " was created successfully.")
        else:
            print("The file " + option + " already exists.")
    else:
        print("Error. Invalid path")

def export(option, start):
    global report
    report += "<root>\r\n"
    report = getChildren(start, 1)
    report += "</root>"
    print(report)
    file = open(option, 'w+', newline='')
    file.write(report)
    file.close


def ls(option, options, start, success):
    if option[0] == "/" and len(option) > 1:
        for path in options:
            if path != "/":
                check, child = doesItExist(start, path, "directory")
                #print(x, start, child, path)
                #x += 1
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
        #print("at root")
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


def mkdir(option, options, start, success):
    for path in options:
        if path != "/":
            check, nextStart = doesItExist(start, path, "directory")
            # print(path, check, nextStart)
            if check:
                start = nextStart
            else:
                # create the directory inode and add to inode directory
                newInode = getNextInode()
                # print(newInode)
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


def rm(option, options, start, success, x):
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
            # print(child, start)
            requests.delete(firebase_url + 'INodeSection/' + str(child) + '.json')
            requests.delete(firebase_url + 'INodeDirectorySection/' + str(start) + "/" + str(child)
                            + '.json')
            print("The file " + option + " was deleted successfully.")
        else:
            print("The file " + option + " does not exist.")
    else:
        print("Error. Invalid path")


def rmdir(option, options, start, success):
    for path in options:
        if path != "/":
            check, child = doesItExist(start, path, "directory")
            # print("del check", start, path, check, child)
            if check:
                parent = start
                start = child
                success = True
            else:
                success = False
                break  # quit processing because path is invalid

    if success:
        # check if directory is empty
        results = requests.get(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')
        # print(results.text)
        if results.text == "{\"" + str(start) + "\"" + ":\"parent\"}":
            requests.delete(firebase_url + 'INodeDirectorySection/' + str(parent) + "/" + str(start)
                            + '.json')
            requests.delete(firebase_url + 'INodeDirectorySection/' + str(start) + '.json')

            requests.delete(firebase_url + 'INodeSection/' + str(start) + '.json')
            print("The directory " + option + " was deleted successfully.")
        else:
            print("The directory " + option + " is not empty and was not deleted.")
    elif option[0] == "/" and len(option) == 1:
        print("You cannot remove the root / directory .")
    else:
        print("The path " + option + " does not exist.")


def main():
    if len(sys.argv) == 3:
        command = sys.argv[1]
        option = sys.argv[2]
        start = 7000  # always start at root
        if (option[0] == "/" and len(option) >= 1) or command == "-export":
            options = option.split("/")
            options[0] = "/"  # set root

            # -CREATE
            if command == "-create":
                create(option, options, start, True, 0)

            # -EXPORT
            elif command == "-export":
                global report
                export(option, start)

            # -LS
            elif command == "-ls":
                ls(option, options, start, False)

            # -MKDIR
            elif command == "-mkdir":
                mkdir(option, options, start, False)

            # -RM
            elif command == "-rm":
                rm(option, options, start, True, 0)

            # -RMDIR
            elif command == "-rmdir":
                rmdir(option, options, start, False)

            else:
                print(system_message)

        else:
            print("Path must include / but cannot be only root directory .")
            print(system_message)
    else:
        print(system_message)


if __name__ == "__main__":
    main()
