# Linux Basic Commands Cheatsheet

## System Information

**uname -a**
Display all system information including kernel version, hostname, and architecture

**uname -r**
Show kernel release version

**uname -m**
Display machine hardware architecture

**hostname**
Show or set system hostname

**hostnamectl**
Query and change system hostname and related settings

**uptime**
Show how long system has been running and load average

**whoami**
Display current username

**id**
Show user ID and group ID information

**w**
Display who is logged in and what they are doing

**who**
Show who is logged in

**last**
Show listing of last logged in users

**date**
Display or set system date and time

**cal**
Display calendar

**df -h**
Show disk space usage in human-readable format

**df -i**
Show inode usage

**du -sh**
Show disk usage summary in human-readable format

**du -sh ***
Show disk usage for all items in current directory

**free -h**
Display memory usage in human-readable format

**top**
Display real-time system resource usage and processes

**htop**
Interactive process viewer with better interface than top

**ps aux**
Show all running processes with detailed information

**ps -ef**
Display all processes in full format

**pstree**
Show processes in tree format

## Navigation and Directory Operations

**pwd**
Print working directory path

**cd**
Change to home directory

**cd ..**
Move up one directory level

**cd ../..**
Move up two directory levels

**cd -**
Change to previous directory

**cd ~**
Change to home directory

**cd /path/to/directory**
Change to specific directory

**ls**
List directory contents

**ls -l**
List with detailed information in long format

**ls -a**
List all files including hidden files

**ls -la**
List all files with detailed information

**ls -lh**
List with human-readable file sizes

**ls -lt**
List sorted by modification time newest first

**ls -ltr**
List sorted by modification time oldest first

**ls -R**
List recursively including subdirectories

**ls -d */**
List only directories in current location

**tree**
Display directory tree structure

**tree -L 2**
Display directory tree limited to two levels deep

**dirs**
Show directory stack

**pushd /path**
Push directory onto stack and change to it

**popd**
Pop directory from stack and change to it

## File Operations

**touch filename**
Create empty file or update timestamp

**cat filename**
Display file contents

**cat file1 file2**
Concatenate and display multiple files

**tac filename**
Display file contents in reverse order

**more filename**
View file contents one screen at a time

**less filename**
View file contents with backward navigation capability

**head filename**
Display first ten lines of file

**head -n 20 filename**
Display first twenty lines of file

**tail filename**
Display last ten lines of file

**tail -n 20 filename**
Display last twenty lines of file

**tail -f filename**
Follow file and display new lines as they are added

**cp source destination**
Copy file to destination

**cp -r source_dir dest_dir**
Copy directory recursively

**cp -i source destination**
Copy with interactive prompt before overwrite

**cp -u source destination**
Copy only when source is newer than destination

**cp -v source destination**
Copy with verbose output

**mv source destination**
Move or rename file

**mv -i source destination**
Move with interactive prompt before overwrite

**mv -u source destination**
Move only when source is newer than destination

**rm filename**
Remove file

**rm -i filename**
Remove with interactive confirmation

**rm -f filename**
Force remove without confirmation

**rm -r directory**
Remove directory and contents recursively

**rm -rf directory**
Force remove directory and contents without confirmation

**mkdir dirname**
Create directory

**mkdir -p path/to/nested/directory**
Create nested directories including parents

**rmdir dirname**
Remove empty directory

**ln -s source linkname**
Create symbolic link

**ln source linkname**
Create hard link

**stat filename**
Display detailed file information and statistics

**file filename**
Determine file type

**basename /path/to/file**
Extract filename from path

**dirname /path/to/file**
Extract directory path from full path

## File Viewing and Editing

**nano filename**
Edit file with nano text editor

**vi filename**
Edit file with vi editor

**vim filename**
Edit file with vim editor

**gedit filename**
Edit file with gedit graphical editor

**code filename**
Open file in Visual Studio Code

**diff file1 file2**
Compare two files line by line

**diff -u file1 file2**
Compare files with unified format output

**sdiff file1 file2**
Compare files side by side

**cmp file1 file2**
Compare two files byte by byte

**comm file1 file2**
Compare sorted files line by line

## File Permissions and Ownership

**chmod 755 filename**
Change file permissions using numeric notation

**chmod u+x filename**
Add execute permission for user owner

**chmod g-w filename**
Remove write permission for group

**chmod o+r filename**
Add read permission for others

**chmod -R 755 directory**
Change permissions recursively for directory

**chown user:group filename**
Change file owner and group

**chown user filename**
Change file owner only

**chown -R user:group directory**
Change ownership recursively for directory

**chgrp group filename**
Change group ownership of file

**umask**
Display default permission mask

**umask 022**
Set default permission mask

## Searching and Finding

**find /path -name filename**
Find files by name

**find /path -iname filename**
Find files by name case-insensitive

**find /path -type f**
Find only files

**find /path -type d**
Find only directories

**find /path -size +100M**
Find files larger than one hundred megabytes

**find /path -mtime -7**
Find files modified in last seven days

**find /path -user username**
Find files owned by specific user

**find /path -name "*.txt" -delete**
Find and delete files matching pattern

**find /path -perm 777**
Find files with specific permissions

**locate filename**
Find files by name using database

**updatedb**
Update locate database

**which command**
Show full path of command

**whereis command**
Show binary, source, and manual page locations

**type command**
Display information about command type

## Text Processing and Manipulation

**grep pattern filename**
Search for pattern in file

**grep -i pattern filename**
Search case-insensitive

**grep -r pattern directory**
Search recursively in directory

**grep -n pattern filename**
Show line numbers with matches

**grep -v pattern filename**
Show lines not matching pattern

**grep -c pattern filename**
Count matching lines

**grep -l pattern files***
List files containing pattern

**grep -w pattern filename**
Match whole words only

**grep -A 3 pattern filename**
Show three lines after match

**grep -B 3 pattern filename**
Show three lines before match

**grep -C 3 pattern filename**
Show three lines before and after match

**egrep pattern filename**
Extended grep with regular expressions

**fgrep pattern filename**
Fixed string grep without regex interpretation

**sort filename**
Sort lines alphabetically

**sort -r filename**
Sort in reverse order

**sort -n filename**
Sort numerically

**sort -u filename**
Sort and remove duplicates

**sort -k 2 filename**
Sort by second column

**sort -t: -k3 -n filename**
Sort by third field using colon delimiter numerically

**uniq filename**
Remove adjacent duplicate lines

**uniq -c filename**
Count occurrences of duplicate lines

**uniq -d filename**
Show only duplicate lines

**uniq -u filename**
Show only unique lines

**wc filename**
Count lines, words, and characters

**wc -l filename**
Count lines only

**wc -w filename**
Count words only

**wc -c filename**
Count bytes only

**cut -d: -f1 filename**
Extract first field using colon delimiter

**cut -c1-10 filename**
Extract characters one through ten

**paste file1 file2**
Merge lines of files side by side

**join file1 file2**
Join lines of files on common field

**tr 'a-z' 'A-Z' < filename**
Translate lowercase to uppercase

**tr -d '0-9' < filename**
Delete all digits

**tr -s ' ' < filename**
Squeeze repeated spaces to single space

**sed 's/old/new/' filename**
Replace first occurrence of old with new on each line

**sed 's/old/new/g' filename**
Replace all occurrences of old with new

**sed -i 's/old/new/g' filename**
Replace in file and save changes

**sed -n '10,20p' filename**
Print lines ten through twenty

**sed '5d' filename**
Delete line five

**awk '{print $1}' filename**
Print first field of each line

**awk -F: '{print $1}' filename**
Print first field using colon delimiter

**awk '/pattern/ {print $0}' filename**
Print lines matching pattern

**awk 'NR==10' filename**
Print line ten

**awk '{sum+=$1} END {print sum}' filename**
Sum values in first column

## Archiving and Compression

**tar -cvf archive.tar directory**
Create tar archive

**tar -xvf archive.tar**
Extract tar archive

**tar -tvf archive.tar**
List contents of tar archive

**tar -czvf archive.tar.gz directory**
Create compressed tar gzip archive

**tar -xzvf archive.tar.gz**
Extract tar gzip archive

**tar -cjvf archive.tar.bz2 directory**
Create compressed tar bzip2 archive

**tar -xjvf archive.tar.bz2**
Extract tar bzip2 archive

**gzip filename**
Compress file with gzip

**gzip -d filename.gz**
Decompress gzip file

**gunzip filename.gz**
Decompress gzip file

**bzip2 filename**
Compress file with bzip2

**bzip2 -d filename.bz2**
Decompress bzip2 file

**bunzip2 filename.bz2**
Decompress bzip2 file

**zip archive.zip files**
Create zip archive

**zip -r archive.zip directory**
Create zip archive recursively

**unzip archive.zip**
Extract zip archive

**unzip -l archive.zip**
List contents of zip archive

**7z a archive.7z files**
Create 7z archive

**7z x archive.7z**
Extract 7z archive

## Network Operations

**ping hostname**
Send ICMP echo requests to test connectivity

**ping -c 4 hostname**
Ping four times then stop

**ifconfig**
Display or configure network interfaces

**ip addr**
Show IP addresses and network interfaces

**ip link**
Show network interface status

**ip route**
Show routing table

**netstat -tuln**
Show listening ports

**netstat -ant**
Show all network connections

**ss -tuln**
Show listening sockets

**ss -ant**
Show all sockets

**curl url**
Transfer data from URL

**curl -O url**
Download file from URL

**curl -I url**
Fetch HTTP headers only

**wget url**
Download file from URL

**wget -c url**
Continue interrupted download

**scp file user@host:/path**
Securely copy file to remote host

**scp user@host:/path/file .**
Securely copy file from remote host

**rsync -avz source destination**
Synchronize files and directories

**rsync -avz source user@host:/path**
Synchronize to remote host

**ssh user@host**
Connect to remote host via SSH

**ssh -p port user@host**
Connect using specific port

**nslookup domain**
Query DNS for domain information

**dig domain**
DNS lookup utility

**host domain**
DNS lookup simple output

**traceroute hostname**
Show path packets take to destination

**route -n**
Display routing table

**arp -a**
Show ARP cache

## Process Management

**ps**
Show processes for current shell

**ps aux**
Show all processes with details

**ps -ef**
Show all processes in full format

**ps -u username**
Show processes for specific user

**pgrep process_name**
Find process ID by name

**pidof process_name**
Find process ID of running program

**kill pid**
Terminate process by ID

**kill -9 pid**
Force kill process

**killall process_name**
Kill all processes by name

**pkill process_name**
Kill processes matching pattern

**bg**
Resume suspended job in background

**fg**
Bring background job to foreground

**jobs**
List background jobs

**nohup command &**
Run command immune to hangups in background

**nice -n 10 command**
Run command with modified priority

**renice -n 5 -p pid**
Change priority of running process

**watch command**
Execute command repeatedly and display results

**watch -n 5 command**
Execute command every five seconds

**screen**
Start screen session for persistent terminal

**tmux**
Start tmux session for terminal multiplexing

## Package Management for Debian and Ubuntu

**apt update**
Update package index

**apt upgrade**
Upgrade all packages

**apt full-upgrade**
Upgrade with package removal if needed

**apt install package**
Install package

**apt remove package**
Remove package keeping configuration

**apt purge package**
Remove package including configuration

**apt autoremove**
Remove unused dependencies

**apt search keyword**
Search for packages

**apt show package**
Show package details

**apt list --installed**
List installed packages

**apt list --upgradable**
List upgradable packages

**dpkg -i package.deb**
Install deb package file

**dpkg -r package**
Remove package

**dpkg -l**
List installed packages

**dpkg -L package**
List files installed by package

**dpkg -S filename**
Find package owning file

## Package Management for Red Hat and CentOS

**yum update**
Update all packages

**yum install package**
Install package

**yum remove package**
Remove package

**yum search keyword**
Search for packages

**yum info package**
Show package information

**yum list installed**
List installed packages

**dnf update**
Update all packages with dnf

**dnf install package**
Install package with dnf

**dnf remove package**
Remove package with dnf

**rpm -i package.rpm**
Install rpm package

**rpm -e package**
Remove rpm package

**rpm -qa**
List all installed rpm packages

**rpm -ql package**
List files in package

**rpm -qf filename**
Find package owning file

## User and Group Management

**useradd username**
Create new user

**useradd -m username**
Create user with home directory

**useradd -s /bin/bash username**
Create user with specific shell

**userdel username**
Delete user

**userdel -r username**
Delete user including home directory

**usermod -aG group username**
Add user to group

**usermod -s /bin/zsh username**
Change user shell

**passwd**
Change current user password

**passwd username**
Change password for specific user

**groupadd groupname**
Create new group

**groupdel groupname**
Delete group

**groups**
Show groups current user belongs to

**groups username**
Show groups for specific user

**id username**
Show user ID and group memberships

**su**
Switch to root user

**su - username**
Switch to user with login shell

**sudo command**
Execute command as root

**sudo -u user command**
Execute command as specific user

**sudo -i**
Start interactive root shell

**visudo**
Edit sudoers file safely

## System Control and Services

**systemctl start service**
Start systemd service

**systemctl stop service**
Stop systemd service

**systemctl restart service**
Restart systemd service

**systemctl reload service**
Reload service configuration

**systemctl status service**
Show service status

**systemctl enable service**
Enable service to start at boot

**systemctl disable service**
Disable service from starting at boot

**systemctl list-units**
List all active units

**systemctl list-unit-files**
List all unit files

**journalctl**
View systemd journal logs

**journalctl -u service**
View logs for specific service

**journalctl -f**
Follow journal logs in real-time

**journalctl -b**
Show logs from current boot

**service service_name start**
Start service using init script

**service service_name stop**
Stop service using init script

**service service_name status**
Check service status

**reboot**
Reboot system

**shutdown -h now**
Shutdown system immediately

**shutdown -r now**
Restart system immediately

**shutdown -h +10**
Shutdown in ten minutes

**poweroff**
Power off system

**halt**
Halt system

**init 0**
Shutdown system using runlevel

**init 6**
Restart system using runlevel

## Disk and Filesystem Management

**fdisk -l**
List all disk partitions

**fdisk /dev/sda**
Partition disk interactively

**parted /dev/sda**
Partition disk with parted

**mkfs.ext4 /dev/sda1**
Create ext4 filesystem

**mkfs.xfs /dev/sda1**
Create xfs filesystem

**mount /dev/sda1 /mnt**
Mount filesystem

**mount -t nfs server:/path /mnt**
Mount NFS share

**umount /mnt**
Unmount filesystem

**blkid**
Show block device attributes

**lsblk**
List block devices in tree format

**fsck /dev/sda1**
Check and repair filesystem

**e2fsck /dev/sda1**
Check ext filesystem

**tune2fs -l /dev/sda1**
Show ext filesystem parameters

**resize2fs /dev/sda1**
Resize ext filesystem

**dd if=/dev/sda of=/dev/sdb**
Copy disk to disk

**dd if=/dev/zero of=file bs=1M count=100**
Create file filled with zeros

## Environment Variables

**echo $PATH**
Display PATH variable

**echo $HOME**
Display home directory variable

**echo $USER**
Display current username variable

**env**
Display all environment variables

**printenv**
Display all environment variables

**export VAR=value**
Set environment variable

**export PATH=$PATH:/new/path**
Add to PATH variable

**unset VAR**
Remove environment variable

**source filename**
Execute commands from file in current shell

**. filename**
Execute commands from file in current shell

## Input Output Redirection

**command > file**
Redirect stdout to file overwriting

**command >> file**
Redirect stdout to file appending

**command 2> file**
Redirect stderr to file

**command &> file**
Redirect both stdout and stderr to file

**command > file 2>&1**
Redirect stdout and stderr to same file

**command < file**
Redirect file as stdin

**command << EOF**
Here document for multi-line input

**command 2>&1 | tee file**
Redirect to file and stdout simultaneously

**command | command2**
Pipe stdout of first command to stdin of second

**command 2>&1 | command2**
Pipe both stdout and stderr to next command

**command > /dev/null**
Discard stdout

**command 2> /dev/null**
Discard stderr

**command &> /dev/null**
Discard all output

## Wildcards and Pattern Matching

***filename***
Match any characters

**file?.txt**
Match single character

**file[abc].txt**
Match any one character in brackets

**file[a-z].txt**
Match any character in range

**file[!abc].txt**
Match any character not in brackets

**{file1,file2}.txt**
Brace expansion for multiple patterns

**file{1..10}.txt**
Brace expansion with sequence

## Command History and Shortcuts

**history**
Display command history

**history 20**
Display last twenty commands

**!number**
Execute command by history number

**!!**
Execute previous command

**!string**
Execute most recent command starting with string

**!$**
Reference last argument of previous command

**!***
Reference all arguments of previous command

**ctrl-r**
Search command history interactively

**ctrl-c**
Cancel current command

**ctrl-z**
Suspend current process

**ctrl-d**
Logout or end input

**ctrl-l**
Clear screen

**tab**
Autocomplete commands and filenames

## Miscellaneous Useful Commands

**clear**
Clear terminal screen

**reset**
Reset terminal to default state

**tty**
Print terminal device name

**alias name='command'**
Create command alias

**unalias name**
Remove alias

**history -c**
Clear command history

**script filename**
Record terminal session to file

**bc**
Command-line calculator

**expr 5 + 3**
Evaluate arithmetic expression

**factor number**
Display prime factors

**yes string**
Output string repeatedly

**seq start end**
Generate sequence of numbers

**shuf filename**
Shuffle lines randomly

**rev filename**
Reverse characters in each line

**column -t filename**
Format output into columns

**split -l 100 filename**
Split file into pieces of one hundred lines each

**csplit file pattern**
Split file at pattern matches

**xargs**
Build and execute commands from stdin

**xargs -I {} command {}**
Execute command for each input line

**parallel command ::: args**
Execute commands in parallel

**time command**
Measure command execution time

**timeout 10 command**
Run command with time limit

**sleep 5**
Delay for five seconds

**wait**
Wait for background processes to complete

**cron**
Schedule recurring tasks

**crontab -e**
Edit cron jobs for current user

**crontab -l**
List cron jobs

**at now + 5 minutes**
Schedule one-time task

**batch**
Execute commands when load permits