---
layout: default
title: Linux Basic Commands
---

# Linux 1

## Linux and Unix History

Unix was developed at AT&T Bell Labs in the late 1960s by Ken Thompson, Dennis Ritchie, and others. It started as a small operating system written in assembly language and was later rewritten in C, making it portable across different hardware platforms. This portability became one of Unix's defining characteristics.

Throughout the 1970s and 1980s, Unix evolved into various commercial versions including System V from AT&T and BSD from the University of California, Berkeley. These different Unix variants shared core concepts but diverged in implementation details, leading to what became known as the Unix wars.

In 1991, Linus Torvalds, a Finnish computer science student, created Linux as a free and open-source alternative to Unix. He released the Linux kernel under the GNU General Public License, allowing anyone to use, modify, and distribute it. This decision fundamentally changed the trajectory of operating systems.

Linux combined with the GNU project's utilities, which Richard Stallman had been developing since 1983, to create a complete free operating system. The GNU project provided essential tools like compilers, shells, and core utilities that worked with the Linux kernel.

Today, Linux powers everything from smartphones running Android to supercomputers, web servers, embedded devices, and cloud infrastructure. Its open-source nature has created an ecosystem of distributions like Ubuntu, Debian, Red Hat, CentOS, Fedora, and Arch Linux, each tailored for different use cases.

The Unix philosophy of small, modular tools that do one thing well and can be combined together remains central to Linux. This design philosophy emphasizes simplicity, clarity, and composability.

## Linux Terminal: Shell vs Bash

The terminal is your interface to the Linux operating system. When you open a terminal, you're actually running a shell program that interprets your commands and communicates with the kernel.

A shell is a command-line interpreter that provides a user interface for Unix-like operating systems. The shell takes commands you type and translates them into actions the operating system can perform. Think of it as the bridge between you and the kernel.

There are many different shells available on Linux systems. The original Unix shell was the Thompson shell, followed by the Bourne shell. Other popular shells include the C shell, Korn shell, and Z shell.

Bash stands for Bourne Again Shell and is the most widely used shell on Linux systems. It was written as a free software replacement for the Bourne shell and includes features from the Korn shell and C shell. Bash is the default shell on most Linux distributions.

When you see references to shell scripts, they can be written for any shell. Bash scripts are shell scripts specifically written for the Bash interpreter. Bash provides features like command history, tab completion, job control, and scripting capabilities that make it powerful for both interactive use and automation.

The relationship is hierarchical: Bash is a specific implementation of a shell. When someone says they're using the shell, they're often using Bash specifically, though they might be using zsh, fish, or another shell alternative.

## Understanding the Prompt: user@machine

When you open a terminal, you see a prompt that typically looks something like this:

```
hodi@ubuntu:~$
```

This prompt contains important information about your current session. The first part before the @ symbol is your username. In this example, the user logged in is john.

The part after the @ symbol and before the colon is the hostname or machine name. This is particularly useful when you're managing multiple servers or when you're connected to remote systems via SSH. In the example, the machine name is webserver.

The part after the colon shows your current directory. The tilde symbol represents your home directory. If you navigate to other directories, this will change to show your current location in the filesystem.

The final character is the prompt symbol. A dollar sign indicates you're running as a regular user, while a hash or pound symbol indicates you're running as the root user with administrative privileges.

Some systems customize this prompt extensively, adding colors, git branch information, timestamps, or other useful context. The prompt is controlled by the PS1 environment variable, which you can customize to suit your preferences.

## sudo and su: Privilege Escalation

Linux is a multi-user system with built-in security mechanisms. Not all users have permission to perform all actions. Administrative tasks require elevated privileges.

The su command stands for substitute user or switch user. When you run su without any arguments, it attempts to switch you to the root user account. You'll be prompted for the root password. Once authenticated, you become root until you exit that shell session.

You can also use su to switch to other users by specifying their username:

```
su - username
```

The dash after su starts a login shell, meaning you get that user's environment variables and start in their home directory.

The sudo command stands for superuser do. Instead of switching to another user entirely, sudo lets you run a single command with elevated privileges. The advantage is that you don't need to know the root password; you use your own password.

To run a command with sudo, simply prefix it:

```
sudo apt update
```

After entering your password, that specific command runs with root privileges, but you remain your regular user for subsequent commands. This is more secure than staying logged in as root.

Most modern Linux distributions prefer sudo over su because it provides better auditing and control. Administrators can configure which users can use sudo and which commands they can run through the sudoers file.

## The Prompt Symbols: Hash and Dollar

The symbols at the end of your command prompt serve as important visual indicators of your privilege level.

The dollar sign means you're operating as a regular user with limited privileges. When you see this symbol, you can run commands that affect your own files and processes, but you cannot make system-wide changes or access files belonging to other users.

The hash symbol indicates you're operating with root privileges. This is sometimes called the superuser or administrator account. When you see the hash symbol, you have unrestricted access to the entire system. You can install software, modify system files, access any user's data, and perform any operation.

This visual distinction is crucial for safety. The hash symbol should make you pause and think carefully about what you're doing, as mistakes made as root can damage your system or compromise security.

When you use su to become root, your prompt changes from dollar to hash. When you use sudo, you temporarily gain root privileges for that one command, but your prompt remains a dollar sign because your shell session itself hasn't changed privilege levels.

## VirtualBox , Ubuntu ISO

VirtualBox is a free and open-source virtualization platform that allows you to run multiple operating systems on a single physical machine. It's particularly useful for learning Linux without affecting your main operating system.

To get started, download VirtualBox from the official website and install it on your host operating system, whether that's Windows, macOS, or another Linux distribution.

Next, download an Ubuntu ISO file from Ubuntu's official website. An ISO file is a disk image containing the entire operating system. Ubuntu offers different versions including Desktop for personal use and Server for headless installations.

Creating a virtual machine in VirtualBox involves allocating resources from your physical machine. You specify how much RAM the virtual machine can use, how much disk space to allocate, and how many CPU cores it can access.

When creating the VM, select Linux as the type and Ubuntu as the version. Allocate at least 2GB of RAM for desktop installations, though 4GB or more is recommended for comfortable use. For storage, a dynamically allocated virtual hard disk of 25GB or more works well.

After creating the VM, mount the Ubuntu ISO file as a virtual optical drive. Start the VM, and it will boot from the ISO just like a physical computer would boot from a DVD. Follow the Ubuntu installation wizard to install the operating system on your virtual hard disk.

Once installed, VirtualBox Guest Additions can be installed to improve performance and enable features like shared folders, better video support, and seamless mouse integration between host and guest.

Virtual machines are perfect for experimentation because you can take snapshots before making major changes. If something goes wrong, you can restore to a previous snapshot without losing everything.

## Filesystem Structure

The Linux filesystem follows a hierarchical tree structure with the root directory at the top, represented by a forward slash. Everything in Linux is organized under this root directory.

The '/home' directory contains personal directories for each user on the system. When you log in as a user named john, your files live in /home/john. This is your home directory where you have full control.

The '/root' directory is the home directory for the root user, kept separate from regular user home directories as an additional security measure.

The '/bin' directory contains essential binary executables needed for system operation and recovery. Commands like ls, cp, and mv live here.

The '/sbin' directory holds system binaries used for system administration tasks, typically run by root. Commands like fdisk and ifconfig are found here.

The '/etc' directory stores system-wide configuration files. When you need to configure a service or change system settings, you often edit files in /etc.

The '/var' directory contains variable data that changes during system operation, including log files in /var/log, mail spools, and temporary files.

The '/tmp' directory provides temporary storage that's typically cleared on reboot. Applications and users can create temporary files here.

The '/usr' directory holds user programs and data. Despite its name, it's not for user personal files but for software installed system-wide. The /usr/bin subdirectory contains most user commands.

The '/opt' directory is used for optional software packages, particularly third-party applications that don't follow the standard Linux filesystem conventions.

The '/dev' directory contains device files representing hardware components. In Linux, hardware is accessed through special files. For example, /dev/sda might represent your first hard drive.

The '/proc' directory is a virtual filesystem providing information about running processes and kernel parameters. Files here don't exist on disk but are generated by the kernel on demand.

The '/sys' directory is another virtual filesystem exposing kernel and device information in a structured format.

Understanding this structure helps you navigate the system and know where to find configurations, logs, and executables.

## Filesystem Navigation and Information Commands

The uname command displays system information. Running it alone shows the kernel name, but adding flags reveals more:

```
uname -a
```

This shows everything including kernel version, hostname, processor architecture, and operating system.

The pwd command stands for print working directory. It shows your current location in the filesystem. When you open a terminal, you typically start in your home directory, and pwd confirms this.

The cd command changes your current directory. Without arguments, cd takes you to your home directory. You can specify absolute paths starting from root:

```
cd /var/log
```

Or relative paths based on your current location:

```
cd documents
```

The ls command lists directory contents. By itself, it shows files and directories in your current location. Adding options modifies the output.

The -l flag provides a long listing with detailed information including permissions, owner, size, and modification time:

```
ls -l
```

The -a flag shows all files including hidden ones, which start with a dot:

```
ls -a
```

Combining flags gives you comprehensive output:

```
ls -al
```

This shows all files in long format, revealing everything about directory contents including hidden configuration files.

The man command displays manual pages for other commands. It's your built-in documentation:

```
man ls
```

This shows the complete manual for the ls command, including all options and usage examples. Navigate with arrow keys, search with forward slash, and quit with q.

Most commands also support a --help flag for quick reference:

```
ls --help
```

This displays a brief summary of available options without opening the full manual page.

## File and Directory Manipulation Commands

The echo command prints text to the terminal. It seems simple but is powerful in scripts:

```
echo Hello World
```

The mv command moves or renames files. To move a file to another directory:

```
mv file.txt /home/user/documents/
```

To rename a file in the current directory:

```
mv oldname.txt newname.txt
```

The mv command can do both simultaneously:

```
mv file.txt /home/user/documents/newname.txt
```

The cp command copies files. Like mv, it takes source and destination:

```
cp source.txt destination.txt
```

To copy entire directories with their contents, use the -r flag for recursive:

```
cp -r directory1 directory2
```

For renaming, mv is the standard tool. Some distributions include a rename command for batch renaming using patterns, but mv handles basic renaming needs.

The mkdir command creates directories:

```
mkdir new_directory
```

Create nested directories with the -p flag, which creates parent directories as needed:

```
mkdir -p parent/child/grandchild
```

The rmdir command removes empty directories:

```
rmdir empty_directory
```

If the directory contains files, rmdir fails. For removing directories with contents, use rm with flags.

The rm command deletes files:

```
rm file.txt
```

To remove directories and their contents, combine the -r flag for recursive with -f for force:

```
rm -rf directory
```

This is powerful and dangerous. It permanently deletes without confirmation. There's no recycle bin in the command line, so deleted files are gone. Use with extreme caution, especially as root.

The -i flag adds interactive prompting for confirmation:

```
rm -i file.txt
```

The touch command creates empty files or updates timestamps:

```
touch newfile.txt
```

The cat command displays file contents:

```
cat file.txt
```

For large files, less provides scrollable viewing:

```
less largefile.txt
```

The head command shows the first lines of a file:

```
head file.txt
```

The tail command shows the last lines, useful for log files:

```
tail file.txt
```

The -f flag makes tail follow the file, showing new lines as they're added:

```
tail -f /var/log/syslog
```

## Special Directory Symbols

The single dot represents the current directory. When you run:

```
ls .
```

You're explicitly telling ls to list the current directory. This is usually implicit, but the dot becomes useful in other contexts.

When copying files, the dot serves as shorthand for the current directory:

```
cp /home/user/file.txt .
```

This copies file.txt from the specified location to wherever you currently are.

The double dot represents the parent directory, one level up in the hierarchy:

```
cd ..
```

This moves you up one directory level. You can chain these:

```
cd ../..
```

This moves up two levels. You can combine them with other path elements:

```
cd ../sibling_directory
```

This goes up one level then into a sibling directory.

The tilde represents your home directory:

```
cd ~
```

This takes you home from anywhere in the filesystem. The tilde expands to /home/username, so:

```
cd ~/documents
```

Takes you to your documents directory regardless of where you currently are.

You can reference other users' home directories:

```
cd ~otheruser
```

These symbols make navigation more efficient and scripts more portable, since they work regardless of absolute paths.

## Command Input, Output, and Error Streams

Every Linux process has three standard data streams that handle communication with the user and system.

Standard input, called stdin, is stream zero. It's where a command receives input, typically from your keyboard or from another command in a pipeline.

Standard output, called stdout, is stream one. It's where a command sends its normal output, typically displayed on your terminal screen.

Standard error, called stderr, is stream two. It's where a command sends error messages and diagnostics, also typically displayed on your terminal but through a separate channel.

The separation of stdout and stderr lets you handle normal output and error messages differently, which is crucial for automation and scripting.

The greater-than symbol redirects stdout to a file, overwriting any existing content:

```
ls -l > filelist.txt
```

This runs ls and instead of displaying output on screen, writes it to filelist.txt.

The double greater-than symbol appends stdout to a file without overwriting:

```
echo "new line" >> logfile.txt
```

This adds the text to the end of logfile.txt, preserving existing content.

The less-than symbol redirects stdin from a file:

```
sort < unsorted.txt
```

This feeds unsorted.txt as input to the sort command.

The here-document syntax uses double less-than followed by a delimiter, often EOF:

```
cat <<EOF
This is line one
This is line two
EOF
```

Everything between the delimiters becomes input to the command. This is useful in scripts for providing multi-line input.

You can redirect specific streams by number:

```
command 2> errors.txt
```

This redirects only stderr to errors.txt while stdout still goes to the terminal.

To redirect both stdout and stderr to the same file:

```
command > output.txt 2>&1
```

The 2>&1 means "redirect stderr to wherever stdout is going," which in this case is output.txt.

To discard output entirely, redirect to /dev/null, a special file that discards everything:

```
command > /dev/null 2>&1
```

This runs the command silently, hiding both normal output and errors.

## Sorting and Text Processing

The sort command arranges lines of text in order. By default, it sorts alphabetically:

```
sort names.txt
```

Numeric sorting requires the -n flag:

```
sort -n numbers.txt
```

Reverse sorting uses the -r flag:

```
sort -r file.txt
```

You can sort by specific fields or columns using delimiters. The -t flag sets the delimiter and -k specifies the field:

```
sort -t: -k3 -n /etc/passwd
```

This sorts the password file numerically by the third field, which is the user ID.

Sort can take input from stdin:

```
cat file.txt | sort
```

Or using redirection:

```
sort < file.txt
```

To remove duplicate lines while sorting, use the -u flag for unique:

```
sort -u file.txt
```

The echo command combined with redirection builds files quickly:

```
echo "first line" > newfile.txt
echo "second line" >> newfile.txt
```

Echo interprets special characters when used with the -e flag:

```
echo -e "line one\nline two"
```

This interprets \n as a newline, printing two lines.

## Piping: Connecting Commands

The pipe symbol connects the output of one command to the input of another, creating powerful command chains.

Basic piping takes stdout from the left command and feeds it as stdin to the right command:

```
ls -l | less
```

This lists directory contents and pipes the output to less for scrollable viewing.

You can chain multiple commands:

```
cat file.txt | sort | uniq
```

This displays file contents, sorts the lines, and removes duplicates.

Piping enables text processing workflows:

```
ls -l | grep "\.txt$" | wc -l
```

This counts how many text files are in a directory by listing all files, filtering for those ending in .txt, and counting the lines.

The grep command searches for patterns:

```
cat logfile.txt | grep "ERROR"
```

This shows only lines containing ERROR.

The wc command counts words, lines, and characters:

```
cat file.txt | wc -l
```

The -l flag counts lines specifically.

Pipes work with redirection:

```
cat file1.txt file2.txt | sort | uniq > combined_sorted.txt
```

This combines two files, sorts them, removes duplicates, and writes the result to a new file.

You can use tee to write to a file while still passing output along the pipe:

```
command | tee output.txt | another_command
```

This saves output to output.txt and also sends it to another_command.

Complex pipelines solve real problems:

```
cat /var/log/apache2/access.log | cut -d' ' -f1 | sort | uniq -c | sort -rn | head -10
```

This analyzes a web server log to find the top ten IP addresses by request count. It extracts IP addresses, sorts them, counts occurrences, sorts by count in reverse numeric order, and shows the top ten.

The power of pipes comes from combining simple tools that do one thing well. Instead of one complex program, you compose a solution from small, focused commands that work together through standard streams.

Understanding stdin, stdout, stderr, redirection, and piping transforms how you work with Linux. These concepts enable automation, data processing, and system administration tasks that would be tedious or impossible with graphical tools alone.
