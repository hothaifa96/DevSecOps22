---
layout: default
title: Linux for DevOps - Lesson 3
---

# Linux for DevOps - Lesson 3

## Table of Contents

1. [Wildcards and Pattern Matching](#wildcards-and-pattern-matching)
2. [Aliases](#aliases)
3. [Environment Variables](#environment-variables)
4. [PATH Variable](#path-variable)
5. [PS1 Prompt Customization](#ps1-prompt-customization)
6. [Bashrc Configuration](#bashrc-configuration)
7. [Source Command](#source-command)
8. [Number Systems](#number-systems)
9. [File Permissions](#file-permissions)
10. [Summary Cheat Sheets](#summary-cheat-sheets)

---

## 1. Wildcards and Pattern Matching

### Overview

Wildcards are special characters used to match patterns in filenames and paths.

### Basic Wildcards

#### `*` (Asterisk) - Matches Zero or More Characters

```bash
# List all .txt files
ls *.txt

# List all files starting with "log"
ls log*

# Delete all .tmp files
rm *.tmp

# Copy all .conf files
cp *.conf /etc/

# Examples
file* matches: file, file1, file.txt, file_backup.tar.gz
*.log matches: error.log, system.log, access.log
```

#### `?` (Question Mark) - Matches Exactly One Character

```bash
# Match file1.txt, file2.txt
ls file?.txt

# Match dates like 2024-01-01
ls 2024-??-??

# Examples
file?.txt matches: file1.txt, fileA.txt (NOT file10.txt)
log? matches: log1, logX (NOT log or log12)
```

#### `[]` (Square Brackets) - Match Single Character in Set

```bash
# Match file1.txt, file2.txt, file3.txt
ls file[123].txt

# Match ranges
ls file[a-z].txt
ls log[0-9].txt

# Examples
file[123].txt matches: file1.txt, file2.txt, file3.txt
[a-c]* matches: apple, boy, cat
```

#### `[!]` (Negation) - Match NOT in Set

```bash
# Match files NOT ending with numbers
ls file[!0-9].txt

# Exclude vowels
ls [!aeiou]*.txt

# Examples
file[!0-9].txt matches: fileA.txt (NOT file1.txt)
[!a-z]* matches files NOT starting with lowercase
```

#### `[[:class:]]` (Character Classes)

| Class         | Description      |
| ------------- | ---------------- |
| `[[:alpha:]]` | Letters (a-zA-Z) |
| `[[:digit:]]` | Digits (0-9)     |
| `[[:alnum:]]` | Alphanumeric     |
| `[[:lower:]]` | Lowercase        |
| `[[:upper:]]` | Uppercase        |
| `[[:space:]]` | Whitespace       |

```bash
# Match files starting with letters
ls [[:alpha:]]*

# Match files with digits
ls [[:digit:]]*.log

# Uppercase files
ls [[:upper:]]*.conf
```

### Best Commands with Wildcards

```bash
# ls - List files
ls *.conf
ls -l file[0-9].txt

# find - Search files
find . -name "*.log"
find . -name "*.py" -o -name "*.sh"

# cp - Copy files
cp *.txt /backup/

# mv - Move files
mv *.log /archive/

# rm - Remove files
rm *.tmp
rm -i *.bak  # Interactive

# grep - Search text
grep "ERROR" *.log

# chmod - Permissions
chmod +x *.sh

# tar - Archive
tar -czf backup.tar.gz *.conf
```

---

## 2. Aliases

### Overview

Aliases are shortcuts for commands.

### Creating Aliases

```bash
# Temporary (current session)
alias ll='ls -la'
alias ..='cd ..'

# View aliases
alias

# Remove alias
unalias ll
```

### Practical Examples

#### File Operations

```bash
alias rm='rm -i'        # Interactive delete
alias cp='cp -i'        # Interactive copy
alias mv='mv -i'        # Interactive move
alias mkdir='mkdir -p'  # Create parent dirs
alias df='df -h'        # Human-readable
alias du='du -h'
```

#### Navigation

```bash
alias ..='cd ..'
alias ...='cd ../..'
alias home='cd ~'
alias docs='cd ~/Documents'
```

#### System Info

```bash
alias ports='netstat -tulanp'
alias meminfo='free -m -l -t'
alias myip='curl ifconfig.me'
alias openports='ss -tuln'
```

---

## 3. Environment Variables

### Overview

Environment variables store system configuration.

### Types

```bash
# Shell variable (local)
MY_VAR="value"

# Environment variable (exported)
export MY_VAR="value"
```

### Common Variables

| Variable  | Description         |
| --------- | ------------------- |
| `$HOME`   | Home directory      |
| `$USER`   | Username            |
| `$PATH`   | Command search path |
| `$PWD`    | Current directory   |
| `$SHELL`  | Current shell       |
| `$EDITOR` | Default editor      |

### Working with Variables

```bash
# View variable
echo $HOME
printenv PATH

# View all
printenv
env

# Set variable
export DATABASE_URL="postgresql://localhost/db"
export API_KEY="secret-key"

# Unset
unset MY_VAR

# Default value if empty
echo ${MY_VAR:-"default"}
```

### Practical Examples

```bash
# Database config
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="myapp"

# Development
export JAVA_HOME="/usr/lib/jvm/java-11"
export GOPATH="$HOME/go"
export NODE_ENV="development"

# Proxy
export HTTP_PROXY="http://proxy:8080"
export HTTPS_PROXY="http://proxy:8080"
```

---

## 4. PATH Variable

### Overview

PATH tells the shell where to find commands.

```bash
# View PATH
echo $PATH
# Output: /usr/local/bin:/usr/bin:/bin

# Which command is used
which ls
type python
```

### Modifying PATH

```bash
# Add to end
export PATH=$PATH:/new/directory

# Add to beginning (priority)
export PATH=/new/directory:$PATH

# Permanent (in .bashrc)
export PATH="$PATH:$HOME/bin"
```

### Common Additions

```bash
# User bin
export PATH="$PATH:$HOME/bin"

# Python
export PATH="$PATH:$HOME/.local/bin"

# Node.js
export PATH="$PATH:$HOME/.npm-global/bin"

# Go
export PATH="$PATH:$GOPATH/bin"

# Rust
export PATH="$PATH:$HOME/.cargo/bin"
```

---

## 5. PS1 Prompt Customization

### Special Characters

| Code | Description            |
| ---- | ---------------------- |
| `\u` | Username               |
| `\h` | Hostname               |
| `\w` | Full directory         |
| `\W` | Directory basename     |
| `\t` | Time (HH:MM:SS)        |
| `\d` | Date                   |
| `\$` | # if root, $ otherwise |

### Colors

```bash
# Basic colors
Black:   \[\033[0;30m\]
Red:     \[\033[0;31m\]
Green:   \[\033[0;32m\]
Yellow:  \[\033[0;33m\]
Blue:    \[\033[0;34m\]
Purple:  \[\033[0;35m\]
Cyan:    \[\033[0;36m\]
White:   \[\033[0;37m\]
Reset:   \[\033[0m\]
```

### Examples

```bash
# Simple
export PS1='\u@\h:\w\$ '

# Colored
export PS1='\[\033[0;32m\]\u\[\033[0m\]@\[\033[0;34m\]\h\[\033[0m\]:\w\$ '

# Two-line
export PS1='┌─[\u@\h]─[\w]\n└─\$ '
```

---

## 6. Bashrc Configuration

### Structure

```bash
# ~/.bashrc

# ============================================
# 1. NON-INTERACTIVE CHECK
# ============================================
case $- in
    *i*) ;;
      *) return;;
esac

# ============================================
# 2. SHELL OPTIONS
# ============================================
HISTSIZE=10000
HISTFILESIZE=20000
shopt -s histappend
shopt -s checkwinsize

# ============================================
# 3. ENVIRONMENT VARIABLES
# ============================================
export EDITOR=vim
export PATH="$HOME/bin:$PATH"

# ============================================
# 4. PROMPT
# ============================================
export PS1='\u@\h:\w\$ '

# ============================================
# 5. ALIASES
# ============================================
alias ll='ls -la'
alias ..='cd ..'

# ============================================
# 6. FUNCTIONS
# ============================================
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# ============================================
# 7. COMPLETIONS
# ============================================
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# ============================================
# 8. LOAD ADDITIONAL FILES
# ============================================
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
```

---

## 7. Source Command

### Overview

Source runs commands in current shell.

```bash
# Source a file
source filename
. filename

# Common uses
source ~/.bashrc
source venv/bin/activate
source .env
```

### Source vs Execute

```bash
# Execute (new subprocess)
./script.sh
# Variables don't persist

# Source (current shell)
source script.sh
# Variables persist
```

### Practical Examples

```bash
# Reload config
source ~/.bashrc

# Load environment
# .env file:
export DATABASE_URL="postgresql://localhost/db"
export API_KEY="secret"

# Load it:
source .env
echo $DATABASE_URL  # Works!

# Python virtualenv
source venv/bin/activate

# Project setup
# setup.sh:
export PROJECT_ROOT="$(pwd)"
export PATH="$PROJECT_ROOT/bin:$PATH"
alias run='python main.py'

# Load:
source setup.sh
```

---

## 8. Number Systems

### Decimal (Base 10)

Uses digits 0-9

```
Example: 2547
2×1000 + 5×100 + 4×10 + 7×1 = 2547
```

### Binary (Base 2)

Uses digits 0-1

```
Position: 2⁷ 2⁶ 2⁵ 2⁴ 2³ 2² 2¹ 2⁰
Example:  1  0  1  0  1  1  0  1 = 173

Calculation:
128 + 32 + 8 + 4 + 1 = 173
```

### Hexadecimal (Base 16)

Uses 0-9 and A-F

```
0-9 = 0-9
A=10, B=11, C=12, D=13, E=14, F=15

Example: 2FA
2×256 + 15×16 + 10×1 = 762
```

### Quick Reference

| Dec | Bin      | Hex |
| --- | -------- | --- |
| 0   | 0000     | 0   |
| 1   | 0001     | 1   |
| 2   | 0010     | 2   |
| 4   | 0100     | 4   |
| 8   | 1000     | 8   |
| 15  | 1111     | F   |
| 16  | 10000    | 10  |
| 255 | 11111111 | FF  |

---

## 9. File Permissions

### Permission Types

| Symbol | Permission | Value |
| ------ | ---------- | ----- |
| r      | Read       | 4     |
| w      | Write      | 2     |
| x      | Execute    | 1     |
| -      | None       | 0     |

### Viewing Permissions

```bash
ls -l file

# Output:
-rwxr-xr-x 1 user group 4096 Jan 15 10:30 file
 │││││││││
 │││││││└└─ Others (r-x = 5)
 │││││└└└── Group (r-x = 5)
 │││└└└──── Owner (rwx = 7)
 ││└─────── Links
 │└──────── File type
 └───────── - = file, d = directory
```

### Numeric Permissions

```
rwx = 4+2+1 = 7
rw- = 4+2+0 = 6
r-x = 4+0+1 = 5
r-- = 4+0+0 = 4
```

### Common Permissions

| Octal | Symbolic   | Use           |
| ----- | ---------- | ------------- |
| 644   | -rw-r--r-- | Regular files |
| 755   | -rwxr-xr-x | Executables   |
| 700   | -rwx------ | Private files |
| 600   | -rw------- | Config files  |

### chmod - Change Permissions

```bash
# Numeric
chmod 644 file.txt
chmod 755 script.sh
chmod 700 private/

# Symbolic
chmod u+x script.sh      # Add execute for owner
chmod g+r file.txt       # Add read for group
chmod o-w file.txt       # Remove write for others
chmod a+x script.sh      # Add execute for all

# Recursive
chmod -R 755 directory/
```

### chown - Change Owner

```bash
# Change owner
chown john file.txt

# Change owner and group
chown john:developers file.txt

# Change group only
chown :developers file.txt

# Recursive
chown -R www-data:www-data /var/www
```

### Binary Format

```
Permission: rwxr-xr--
Binary:     111 101 100
Octal:      7   5   4

Breakdown:
Owner:  111 = rwx = 7
Group:  101 = r-x = 5
Others: 100 = r-- = 4

Result: 754
```

### Symbolic Examples

```bash
# u = user, g = group, o = others, a = all

chmod u+x file        # User: add execute
chmod g-w file        # Group: remove write
chmod o+r file        # Others: add read
chmod a+x file        # All: add execute

# Combined
chmod u=rwx,g=rx,o=r file    # Set exact permissions
chmod u+rw,g+r,o+r file      # Add permissions
chmod a-w file               # Remove write for all
```

---

## 10. Summary Cheat Sheets

### Wildcards Quick Reference

```bash
*           # Match any characters
?           # Match one character
[abc]       # Match a, b, or c
[a-z]       # Match range a to z
[!abc]      # NOT a, b, or c
[[:alpha:]] # Letters
[[:digit:]] # Digits
```

### Aliases

```bash
alias name='command'  # Create
unalias name          # Remove
alias                 # List all
```

### Environment Variables

```bash
VAR="value"           # Set local
export VAR="value"    # Set global
echo $VAR             # View
printenv              # List all
unset VAR             # Remove
```

### PATH

```bash
echo $PATH                        # View
export PATH="$PATH:/new/dir"      # Add
which command                     # Find command
```

### Permissions

```bash
chmod 644 file        # rw-r--r--
chmod 755 file        # rwxr-xr-x
chmod u+x file        # Add execute
chown user:group file # Change owner
```

### Number Conversions

```bash
# Decimal to Binary
echo "obase=2; 10" | bc        # 1010

# Binary to Decimal
echo "ibase=2; 1010" | bc      # 10

# Decimal to Hex
echo "obase=16; 255" | bc      # FF

# Bash arithmetic
echo $((0xFF))                 # 255
echo $((2#1010))               # 10
```

### Common Commands

```bash
ls -la                # List all with details
cd directory          # Change directory
pwd                   # Print working directory
cp source dest        # Copy
mv source dest        # Move/rename
rm file               # Remove
mkdir dir             # Make directory
rmdir dir             # Remove empty directory
cat file              # View file
less file             # Page through file
head file             # First 10 lines
tail file             # Last 10 lines
grep pattern file     # Search in file
find . -name "*.txt"  # Find files
```

---

## Practice Exercises

### Wildcard Exercises

```bash
# 1. List all .sh files
ls *.sh

# 2. Find files starting with "test" and ending with numbers
ls test*[0-9]

# 3. Delete all .tmp and .bak files
rm *.tmp *.bak

# 4. Copy all .conf files to /backup
cp *.conf /backup/

# 5. Find Python files recursively
find . -name "*.py"
```

### Permission Exercises

```bash
# 1. What is -rw-r--r-- in octal?
# Answer: 644

# 2. Convert 755 to symbolic
# Answer: -rwxr-xr-x

# 3. Make script executable
chmod +x script.sh
chmod 755 script.sh

# 4. Set file to owner-only read/write
chmod 600 secret.txt

# 5. Recursive permission on directory
chmod -R 755 /var/www
```

### Number System Exercises

```bash
# 1. Convert 10 to binary
echo "obase=2; 10" | bc  # Answer: 1010

# 2. Convert FF to decimal
echo "ibase=16; FF" | bc  # Answer: 255

# 3. What is rwx in binary?
# Answer: 111 (7)

# 4. Convert 11111111 to decimal
# Answer: 255

# 5. What is 777 in binary?
# Answer: 111111111
```

---

## Additional Resources

### Shell Options (shopt)

```bash
shopt -s histappend      # Append to history
shopt -s checkwinsize    # Check window size
shopt -s cdspell         # Correct cd typos
shopt -s globstar        # Enable **
```

### Special Permissions

```bash
chmod u+s file           # Setuid (4000)
chmod g+s directory      # Setgid (2000)
chmod +t directory       # Sticky bit (1000)

# Example
chmod 4755 program       # Setuid + 755
chmod 2775 shared/       # Setgid + 775
chmod 1777 /tmp          # Sticky + 777
```

### Finding Files

```bash
find / -perm 777         # World writable
find / -perm /4000       # SUID files
find / -user john        # By owner
find / -size +100M       # Large files
find / -mtime -7         # Modified in 7 days
```

---
