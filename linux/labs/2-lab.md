---
layout: default
title: Linux DevOps Practical Labs
---

# Linux DevOps Practical Labs

## Lab Set 1: Basic Skills

### Lab 1.1: Wildcards and File Management

1. Create 10 files named `test1.txt` through `test10.txt` in a new directory called `lab1`
2. Create 5 files named `report_jan.log`, `report_feb.log`, `report_mar.log`, `report_apr.log`, `report_may.log`
3. List only files that start with "test" and have a single digit
4. List only files that end with `.log` extension
5. Copy all `.txt` files to a new directory called `backup`
6. Delete all files that start with "test" and end with numbers 6-9
7. Create files named `data_A.csv`, `data_B.csv`, `data_C.csv`
8. List only files that contain uppercase letters in their names
9. Rename all `.log` files to have a `.backup` extension instead
10. Find and list all `.csv` files in the current directory using the find command

### Lab 1.2: Aliases and Productivity

1. Create a temporary alias called `ll` that shows detailed file listings with human-readable sizes
2. Create an alias called `..` to go up one directory
3. List all currently active aliases in your session
4. Create an alias called `ports` to show all listening network ports
5. Remove the `ll` alias you created
6. Make your aliases permanent by adding them to the appropriate configuration file
7. Reload your configuration file to apply the changes without logging out

### Lab 1.3: Environment Variables and PATH

1. Create a temporary environment variable called `DB_HOST` with value `localhost`
2. Create and export an environment variable called `APP_ENV` with value `development`
3. Display the value of your `HOME` environment variable
4. Display your current `PATH` variable in a readable format (one directory per line)
5. Create a directory called `~/mybin` and add it to your PATH temporarily

## Lab Set 2

### Lab 2.1: File Permissions and Security

1. Create a file called `secret.txt` and set permissions so only you can read and write it (no access for group or others)

### Lab 2.2: Number Systems and Permissions

1. Convert the permission `rwxr-xr-x` to its octal (numeric) representation
2. Convert the octal permission `644` to its symbolic representation
3. Convert the binary number `111101101` to octal format (for permissions)
4. If a file has permissions `rw-r-----`, calculate its numeric value
5. Convert the decimal number 255 to hexadecimal
6. Convert the hexadecimal number `FF` to binary
7. Convert the binary number `11111111` to decimal
8. Create a file with permissions `rwxrwx---` using numeric notation
9. What would be the binary representation of the permission `rwx------`?
10. Calculate what permission `chmod 777` represents in symbolic and binary format

### Lab 2.3: Bashrc Configuration and Source

1. Open your `.bashrc` file and add a comment section for "Custom Aliases"
2. Add an alias for `gs='git status'` in your `.bashrc`
3. Add an alias for `dc='docker-compose'` in your `.bashrc`
4. Add a custom function called `mkcd` that creates a directory and changes into it in one command
5. Create a separate file called `.bash_aliases` for all your aliases
6. Modify your `.bashrc` to source (load) the `.bash_aliases` file if it exists
7. Create a file called `.env` with database connection variables
8. Source the `.env` file and verify the variables are loaded
9. Add a custom PS1 prompt configuration to your `.bashrc`
10. Reload your entire `.bashrc` without logging out to test all changes

### Lab 2.4: Advanced Wildcards and Find

1. Create a complex directory structure: `project/{src,tests,docs}/{js,py}` with multiple files
2. Find all `.js` files in the entire project directory tree
3. Find all files that were modified in the last 24 hours
4. Find all files larger than 1MB in your home directory
5. Use wildcards to list only files that start with a vowel (a, e, i, o, u)
6. Find all executable files in `/usr/bin` that start with 'git'
7. Delete all `.tmp` files recursively in your project directory (be careful!)
8. Find all empty files in the current directory and its subdirectories
9. Copy all `.conf` files from `/etc` that contain the word "network" in their name to a backup directory
10. Use character classes to find all files that start with a digit followed by exactly two letters

---

## Lab Set 1 - Expected Outcomes

After completing Lab Set 1, you should be able to:

- ✅ Confidently use wildcards to match file patterns
- ✅ Create and manage aliases for common commands
- ✅ Work with environment variables and PATH
- ✅ Customize your bash prompt with colors and information
- ✅ Understand basic file operations and navigation

---

## Lab Set 2 - Expected Outcomes

After completing Lab Set 2, you should be able to:

- ✅ Master file permissions in both numeric and symbolic formats
- ✅ Convert between different number systems (binary, octal, hexadecimal)
- ✅ Configure and customize your `.bashrc` effectively
- ✅ Use advanced find commands and wildcards
- ✅ Implement security best practices with file permissions

---

## Hints and Tips

### For Wildcards:

- Remember `*` matches zero or more characters
- Remember `?` matches exactly one character
- Use `[0-9]` for digits, `[a-z]` for lowercase letters
- Character classes like `[[:alpha:]]` are very powerful

### For Permissions:

- Read = 4, Write = 2, Execute = 1
- Add them together: rwx = 4+2+1 = 7
- Common patterns: 644 (files), 755 (executables), 700 (private)

### For Environment Variables:

- Use `export` to make variables available to child processes
- Variables are case-sensitive
- Access with `$VARIABLE_NAME` or `${VARIABLE_NAME}`

### For .bashrc:

- Always test changes before making them permanent
- Keep backups of your configuration files
- Use `source ~/.bashrc` to reload without logging out
- Comment your customizations for future reference

---

## Validation Commands

### To verify your work:

```
# Check file permissions
ls -l filename

# Verify aliases
alias

# Check environment variables
printenv | grep VARIABLE_NAME

# View your prompt
echo $PS1

# Test command in PATH
which command_name

# Verify sourced variables
echo $VARIABLE_NAME
```

---

## Additional Challenges (Optional)

### Challenge 1: Create a Development Environment Setup Script

Write a script that:

- Sets up all necessary environment variables for a project
- Creates project directory structure
- Sets appropriate permissions on all directories
- Adds project bin directory to PATH
- Creates useful aliases for the project

### Challenge 2: Permission Audit Script

Write a script that:

- Finds all world-writable files
- Finds all SUID/SGID files
- Checks for files with overly permissive settings
- Generates a security report

### Challenge 3: Custom Bash Profile

Create a comprehensive `.bashrc` that includes:

- Organized sections with clear comments
- Useful aliases for your workflow
- Custom functions for common tasks
- A beautiful, informative prompt
- Smart PATH management
- Conditional configurations based on hostname or OS

---

## Troubleshooting Guide

### If aliases don't work:

1. Check if you exported them (not needed for aliases, but needed for variables)
2. Ensure you sourced the file: `source ~/.bashrc`
3. Check for syntax errors in your alias definition

### If PATH changes don't work:

1. Make sure you used `export`
2. Verify the directory exists
3. Check for typos in the path
4. Ensure you reloaded your configuration

### If permissions seem wrong:

1. Use `ls -l` to verify what was actually set
2. Remember: directories need `x` permission to be entered
3. Check both numeric and symbolic representations
4. Verify you have permission to change the file

### If variables disappear:

1. Remember to `export` them
2. Add them to `.bashrc` for persistence
3. Check if you're in the same shell session
4. Verify the syntax is correct

---
