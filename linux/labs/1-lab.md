---
layout: default
title: Linux Fundamentals Lab
---

# Linux Fundamentals Lab Exercises

## Lab Overview

This lab provides hands-on exercises to practice Linux basic commands and concepts. Each exercise describes what you need to accomplish without providing the exact commands. Use the manual pages, help flags, and your knowledge to complete each task.

## Prerequisites

You should have a working Linux environment such as Ubuntu installed in VirtualBox. You need access to a terminal window where you can execute commands. Review your course materials on basic Linux commands before starting.

## How to Use This Lab

Each exercise set contains tasks you must complete. Read each task carefully and determine which commands you need to use. If you get stuck, use the man command or the help flag to learn about command options. Try to solve each problem before looking at reference materials.

## Exercise Set One: System Information and Prompt Understanding

**Task 1.1**
Display your current username and verify it matches what appears in your terminal prompt.

**Task 1.2**
Find out the hostname of your machine and compare it with what appears in your prompt after the @ symbol.

**Task 1.3**
Display comprehensive system information including kernel name, version, hostname, and hardware architecture.

**Task 1.4**
Display only the kernel release version.

**Task 1.5**
Display only the machine hardware architecture.

**Task 1.6**
Attempt to read the /etc/shadow file as a regular user. Observe what happens.

**Task 1.7**
Read the /etc/shadow file using elevated privileges [super user]. What password do you need to enter?

**Task 1.8**
Switch to the root user account. Observe how your prompt changes. What symbol appears at the end now?

**Task 1.9**
While as root, verify your current username and current directory location.

**Task 1.10**
Exit from the root shell and return to your regular user account. Verify your prompt returns to normal.

## Exercise Set Two: Filesystem Navigation and Exploration

**Task 2.1**
Display your current directory location. You should be in your home directory.

**Task 2.2**
List the files and directories in your current location.

**Task 2.3**
List the same contents but with detailed information including permissions, owner, size, and modification date.

**Task 2.4**
List all files including hidden ones that start with a dot.

**Task 2.5**
List all files with detailed information and include hidden files in a single command.

**Task 2.6**
Navigate to the root directory of the filesystem.

**Task 2.7**
From the root directory, list all the top-level directories. You should see directories like bin, etc, home, var, and usr.

**Task 2.8**
Navigate to the /etc directory and verify your location.

**Task 2.9**
Return to your home directory using the tilde shortcut.

**Task 2.10**
Navigate to /var/log and verify your location.

**Task 2.11**
Move up one directory level to /var.

**Task 2.12**
Move up two directory levels from /var to reach the root directory.

**Task 2.13**
Navigate to the /tmp directory, then return to your previous directory location using the dash argument.

**Task 2.14**
Create a new directory called lab_workspace in your home directory.

**Task 2.15**
Navigate into the lab_workspace directory and verify you are there.

## Exercise Set Three: File and Directory Manipulation

**Task 3.1**
Create three empty files named file1.txt, file2.txt, and file3.txt.

**Task 3.2**
Verify the files were created by listing them with detailed information.

**Task 3.3**
Create a file named document.txt containing the text "This is the first line" using output redirection.

**Task 3.4**
Display the contents of document.txt to verify it contains the text.

**Task 3.5**
Append the text "This is the second line" to document.txt without overwriting the existing content.

**Task 3.6**
Verify that document.txt now contains both lines.

**Task 3.7**
Create a copy of document.txt named document_backup.txt.

**Task 3.8**
Rename file1.txt to renamed_file.txt.

**Task 3.9**
Create a subdirectory named documents.

**Task 3.10**
Move renamed_file.txt into the documents directory.

**Task 3.11**
Verify that renamed_file.txt is now inside the documents directory and no longer in the current directory.

**Task 3.12**
Create a nested directory structure projects/web/frontend in a single command.

**Task 3.13**
Verify the nested structure was created by listing the projects directory recursively.

**Task 3.14**
Create a copy of the documents directory named documents_backup including all its contents.

**Task 3.15**
Create three directories named dir1, dir2, and dir3 in a single command.

**Task 3.16**
Remove the empty directory dir1.

**Task 3.17**
Try to remove the non-empty documents directory using the command for empty directories. Observe what happens.

**Task 3.18**
Remove dir2 along with any contents it might have.

**Task 3.19**
Create a file named protected.txt and make it read-only. Try to delete it normally and observe the prompt.

**Task 3.20**
Force delete protected.txt without any prompts.

**Task 3.21**
Create five files with different extensions: report.pdf, notes.doc, script.sh, image.png, and data.csv.

**Task 3.22**
Delete all .txt files in the current directory using a wildcard pattern.

## Exercise Set Four: Working with File Contents

**Task 4.1**
Create a file named multiline.txt containing ten lines of text using a here-document with EOF as the delimiter.

**Task 4.2**
Display the entire contents of multiline.txt.

**Task 4.3**
Display only the first ten lines of multiline.txt.

**Task 4.4**
Display only the first three lines of multiline.txt.

**Task 4.5**
Display only the last ten lines of multiline.txt.

**Task 4.6**
Display only the last two lines of multiline.txt.

**Task 4.7**
View multiline.txt using a paginated viewer that allows you to scroll up and down. Navigate through the file and then exit.

**Task 4.8**
Count the total number of lines, words, and characters in multiline.txt.

**Task 4.9**
Count only the number of lines in multiline.txt.

**Task 4.10**
Create a file named unsorted.txt containing five fruit names in random order.

**Task 4.11**
Display the contents of unsorted.txt sorted alphabetically without modifying the original file.

**Task 4.12**
Save the sorted output to a new file named sorted.txt.

**Task 4.13**
Sort the contents of unsorted.txt in reverse alphabetical order.

**Task 4.14**
Create a file named numbers.txt containing five numbers: 100, 20, 5, 50, and 3.

**Task 4.15**
Sort numbers.txt alphabetically and observe the result.

**Task 4.16**
Sort numbers.txt numerically to get the correct numerical order.

## Exercise Set Six: Standard Streams and Redirection

**Task 6.1**
Display the text "This goes to stdout" on your terminal.

**Task 6.2**
Redirect the text "This goes to a file" into a file named output.txt, overwriting any existing content.

**Task 6.3**
Display the contents of output.txt to verify it contains the text.

**Task 6.4**
Append the text "This is appended" to output.txt without overwriting the existing content.

**Task 6.5**
Verify that output.txt now contains both lines.

**Task 6.6**
Try to list a directory that does not exist, such as /nonexistent, and observe the error message.

**Task 6.7**
Redirect only the error message from the previous command into a file named errors.txt.

**Task 6.8**
Display the contents of errors.txt to verify it captured the error.

**Task 6.9**
List both an existing directory like /etc and a non-existing directory like /nonexistent. Redirect both the normal output and error messages to a file named all_output.txt.

**Task 6.10**
Verify that all_output.txt contains both successful output and error messages.

**Task 6.11**
Create a file named input.txt containing three lines: "line three", "line one", and "line two".

**Task 6.12**
Sort the contents of input.txt by using it as standard input rather than as a command argument. "<"

**Task 6.13**
Combine input and output redirection to sort input.txt and save the result to sorted_output.txt.

## GOODLUCK
