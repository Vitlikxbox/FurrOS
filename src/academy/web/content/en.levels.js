/* Lapa's School, levels 2 and 3: Pixie (a confident user) and Danyok (the system inside out). 14 chapters each. */
Object.assign(window.CONTENT.en.ui, {
  levelsTitle: "Levels", level: "Level",
  levelsIntro: "Three teachers, each one harder. Lapa teaches you to live in FurrOS, Pixie to command the system with confidence, Danyok to take it apart down to the last screw.",
  lvl_lapa: "Lapa", lvl_pixie: "Pixie", lvl_danyok: "Danyok",
  diff_lapa: "beginner", diff_pixie: "confident user", diff_danyok: "system master",
  lvlIntro_lapa: "The desktop, files, terminal, apps, games and first aid.",
  lvlIntro_pixie: "Pipes, processes, services, disks, network, SSH, the AUR and your own scripts.",
  lvlIntro_danyok: "Boot, the kernel, Btrfs, your own services, containers, VMs, encryption and hardcore repairs.",
  lvlHello_lapa: "Lapa's level 🐾", lvlHello_pixie: "Yo, I'm Pixie. I'm teaching now 🖤", lvlHello_danyok: "Hey. I'm Danyok, and I have a lemon 🍋",
  lvlText_lapa: "The basics: how to live in FurrOS without fear. Start here if Linux is new to you.",
  lvlText_pixie: "Lapa taught you not to fear the terminal. I'll teach you to command it: chain commands, find anything, manage processes and services, hop to other computers over SSH and write your own scripts. It gets a bit harder, but afterwards you'll do in a minute what used to take an hour.",
  lvlText_danyok: "The last level. We're going inside: how the system boots, what the kernel does, how Btrfs and systemd work, how to build your own package, run a container and a VM, encrypt a disk and raise the system from the dead. Take your time, and try things in a VM or with a fresh snapshot.",
  lvlFirst: "We suggest finishing the “{0}” level first. But if you feel confident, go right ahead.",
  says_pixie: "Pixie says", says_danyok: "Danyok says",
  nextLevel: "Next: {0}",
  diplomaTitle_pixie: "Pixie's diploma 🎓", diplomaText_pixie: "You've finished the confident user level: pipes, processes, services, disks, network, SSH, the AUR and scripts. The terminal works for you now, not the other way round. Pixie approves 🖤",
  diplomaTitle_danyok: "Danyok's diploma 🎓🍋", diplomaText_danyok: "You've finished all three levels of Lapa's School. Boot, the kernel, Btrfs, systemd, packages, containers, encryption and repairs are all yours now. You're officially a FurrOS master. Have a lemon 🍋",
});

window.CONTENT.en.levels = {
  pixie: { chapters: [
    {
      id: "p-shell", mood: "wave", badge: "⚡ Bash buff", title: "Deeper into bash",
      intro: "Paths, wildcards, variables, aliases and your ~/.bashrc.",
      lessons: [
        { title: "Paths and wildcards", blocks: [
          { p: "A path is either <b>absolute</b> (from the root: <code>/home/furry/Documents</code>) or <b>relative</b> (from the current folder: <code>Documents/notes.txt</code>). <code>.</code> is the current folder, <code>..</code> the one above, <code>~</code> your home, and <code>-</code> in <code>cd -</code> the previous one." },
          { p: "Wildcards match many files at once: <code>*</code> is any characters, <code>?</code> a single character, <code>{a,b}</code> alternatives." },
          { cmd: "ls ~/Pictures/*.png", note: "Every PNG in your Pictures folder." },
          { cmd: "mkdir -p project/{src,docs,tests}", note: "Three folders in one command. -p also creates the parent." },
          { say: "Bash expands the wildcard itself, not the program. So before <code>rm *</code>, run <code>ls *</code> first and see what's about to get hit 🖤" },
        ] },
        { title: "Variables and aliases", blocks: [
          { p: "The shell has <b>environment variables</b>. Every program started from it can see them:" },
          { table: { head: ["Variable", "What it holds"], rows: [
            ["<code>$HOME</code>", "Your home folder"], ["<code>$USER</code>", "Your user name"],
            ["<code>$PATH</code>", "Where to look for commands (folders separated by colons)"], ["<code>$EDITOR</code>", "Default editor"],
          ] } },
          { cmd: "echo $PATH" },
          { p: "An <b>alias</b> is a short name for a long command. To keep it forever, add it to <code>~/.bashrc</code>:" },
          { cmd: "echo \"alias update='sudo pacman -Syu'\" >> ~/.bashrc && source ~/.bashrc", note: "source re-reads the file without restarting the terminal." },
          { tip: "Keep your own scripts in <code>~/.local/bin</code>: FurrOS already has it in $PATH, so scripts there run by name from any folder." },
        ] },
      ],
      quiz: [
        { q: "What does cd - do?", a: ["Goes back to the previous folder", "Deletes the folder", "Goes to the root"], ok: 0 },
        { q: "What does the wildcard *.txt match?", a: ["Every file ending in .txt", "Only a file literally named *.txt", "Every hidden file"], ok: 0 },
        { q: "Which variable lists the folders where bash looks for commands?", a: ["$HOME", "$PATH", "$USER"], ok: 1 },
      ],
    },
    {
      id: "p-pipes", mood: "wave", badge: "⚡ Plumber", title: "Redirection and pipes",
      intro: "Chaining commands: >, >>, 2>, | and the filters grep, sort, wc.",
      lessons: [
        { title: "Where the output goes", blocks: [
          { p: "Every command has three streams: input (stdin), output (stdout) and errors (stderr). You can redirect them:" },
          { table: { head: ["Syntax", "What it does"], rows: [
            ["<code>command > file</code>", "Write the output to a file (old contents are wiped)"],
            ["<code>command >> file</code>", "Append to the end of the file"],
            ["<code>command 2> file</code>", "Write only the errors"],
            ["<code>command &> file</code>", "Output and errors together"],
            ["<code>command > /dev/null</code>", "Throw the output away (a “black hole”)"],
            ["<code>command &lt; file</code>", "Take the input from a file"],
          ] } },
          { cmd: "pacman -Qe > ~/my-packages.txt", note: "A list of explicitly installed packages. Handy when reinstalling." },
        ] },
        { title: "The pipe |", blocks: [
          { p: "The pipe <code>|</code> feeds one command's output into the next one's input. Big commands are built from small ones this way:" },
          { table: { head: ["Filter", "What it does"], rows: [
            ["<code>grep word</code>", "Keep lines containing the word (<code>-i</code> ignore case, <code>-v</code> the opposite)"],
            ["<code>sort</code>", "Sort (<code>-n</code> numerically, <code>-r</code> reversed)"],
            ["<code>uniq -c</code>", "Collapse identical neighbouring lines and count them"],
            ["<code>wc -l</code>", "Count lines"],
            ["<code>head -n 5</code> / <code>tail -n 5</code>", "First / last lines"],
            ["<code>less</code>", "Page through long output (quit: q, search: /)"],
          ] } },
          { cmd: "pacman -Q | wc -l", note: "How many packages are installed." },
          { cmd: "pacman -Q | grep -i nvidia", note: "Which NVIDIA packages are installed." },
          { cmd: "du -sh ~/* 2>/dev/null | sort -h | tail -n 5", note: "The five heaviest folders in your home." },
          { say: "Pipes are Linux's superpower. Each command does one thing well, and the pipe glues them into anything. Like Lego, but for grown-ups 🖤" },
        ] },
      ],
      quiz: [
        { q: "How is > different from >>?", a: ["> overwrites the file, >> appends to it", "No difference", ">> deletes the file"], ok: 0 },
        { q: "What does the command to the right of | get?", a: ["The left command's output as its input", "It runs separately and independently", "It cancels the left one"], ok: 0 },
        { q: "How do you throw away a command's errors?", a: ["2>/dev/null", "| grep", ">> errors"], ok: 0 },
      ],
    },
    {
      id: "p-find", mood: "hoodie", badge: "⚡ Sniffer", title: "Finding anything",
      intro: "find, grep -r, plocate, which: find a file, some text or a program.",
      lessons: [
        { title: "Find a file", blocks: [
          { cmd: "find ~ -name \"*.pdf\"", note: "Every PDF in your home. -iname ignores case." },
          { cmd: "find ~/Downloads -type f -size +500M", note: "Files over 500 MB in Downloads." },
          { cmd: "find ~ -type f -mtime -1", note: "Files changed in the last 24 hours." },
          { p: "find walks through every folder for real, so it can be slow. Searching a ready-made database is faster: <b>plocate</b>." },
          { cmd: "sudo pacman -S plocate && sudo updatedb", note: "Install it and build the database. After that it updates itself daily." },
          { cmd: "locate hyprland.lua" },
        ] },
        { title: "Find text and programs", blocks: [
          { cmd: "grep -rn \"monitor\" ~/.config/hypr/", note: "In every file of the folder: -r recursive, -n with line numbers." },
          { cmd: "which firefox", note: "Where the program behind a command lives." },
          { cmd: "pacman -F libGL.so.1", note: "Which package contains a file, even if it isn't installed. sudo pacman -Fy updates the file database." },
          { say: "The “error while loading shared libraries: libsomething.so” error is fixed exactly like this: pacman -F finds the package you need to install 🖤" },
        ] },
      ],
      quiz: [
        { q: "How do you find every .jpg in your home?", a: ["find ~ -name \"*.jpg\"", "grep jpg ~", "ls -jpg"], ok: 0 },
        { q: "What's the fastest way to find a file by name across the system?", a: ["locate (plocate)", "cat", "wc"], ok: 0 },
        { q: "How do you find which package has libGL.so.1?", a: ["pacman -F libGL.so.1", "which libGL.so.1", "pacman -Syu"], ok: 0 },
      ],
    },
    {
      id: "p-text", mood: "hoodie", badge: "⚡ Editor", title: "Editors and text",
      intro: "nano like a pro, surviving vim, diff and quick edits with sed.",
      lessons: [
        { title: "nano and vim", blocks: [
          { p: "<b>nano</b>: hints at the bottom, <code>^</code> means Ctrl. Useful: <kbd>Ctrl</kbd>+<kbd>W</kbd> search, <kbd>Ctrl</kbd>+<kbd>K</kbd> cut a line, <kbd>Ctrl</kbd>+<kbd>U</kbd> paste, <kbd>Alt</kbd>+<kbd>U</kbd> undo, <kbd>Ctrl</kbd>+<kbd>O</kbd> save, <kbd>Ctrl</kbd>+<kbd>X</kbd> quit." },
          { p: "Sooner or later <b>vim</b> will open by itself (in git, for example). Five things are enough to survive:" },
          { table: { head: ["Keys", "What it does"], rows: [
            ["<kbd>i</kbd>", "Insert mode: now you can type"], ["<kbd>Esc</kbd>", "Back to command mode"],
            ["<code>:w</code> + Enter", "Save"], ["<code>:q!</code> + Enter", "Quit without saving"], ["<code>:wq</code> + Enter", "Save and quit"],
          ] } },
          { cmd: "export EDITOR=nano", note: "So programs open nano instead of vim. Add it to ~/.bashrc to make it permanent." },
        ] },
        { title: "Compare and replace", blocks: [
          { cmd: "diff -u old.conf new.conf", note: "How two files differ: - removed, + added." },
          { cmd: "sed -i 's/old/new/g' file.txt", noRun: true, note: "Replace everywhere in the file. Without -i it only shows the result and leaves the file alone." },
          { warn: "sed -i edits the file immediately. Before touching system configs, make a copy: <code>sudo cp file file.bak</code>." },
          { say: "Pixie hack: <code>sed</code> without <code>-i</code> is a preview. I look first, then add -i. Not one broken config, purr 🖤" },
        ] },
      ],
      quiz: [
        { q: "How do you quit vim without saving?", a: [":q! and Enter", "Ctrl+C", "Alt+F4"], ok: 0 },
        { q: "What does diff -u a b show?", a: ["The differences between the files", "The file sizes", "It deletes b"], ok: 0 },
        { q: "What does sed's -i flag do?", a: ["Edits the file in place", "Ignores case", "Shows help"], ok: 0 },
      ],
    },
    {
      id: "p-proc", mood: "timer", badge: "⚡ Process tamer", title: "Processes",
      intro: "What's running right now, how to stop it and how to run things in the background.",
      lessons: [
        { title: "Look and stop", blocks: [
          { p: "Every running program is a <b>process</b> with its own number (PID)." },
          { cmd: "htop", note: "A live list of processes: F6 sort, F9 kill, q quit. If missing: sudo pacman -S htop" },
          { cmd: "ps aux | grep firefox", note: "Find a process and its PID." },
          { table: { head: ["Command", "What it does"], rows: [
            ["<code>kill PID</code>", "Politely ask it to quit (TERM signal)"],
            ["<code>kill -9 PID</code>", "Kill it, no questions asked (KILL), if it's frozen solid"],
            ["<code>pkill firefox</code>", "Quit by name"],
            ["<code>xkill</code> / <code>kill</code> in KRunner", "Click on the frozen window (X11 and KDE)"],
          ] } },
          { say: "Plain kill first, and only if the process doesn't react, -9. Kill -9 doesn't let the program save, so unsaved work can be lost 🖤" },
        ] },
        { title: "Background and foreground", blocks: [
          { ul: [
            "<code>command &</code> — run it in the background and keep using the terminal.",
            "<kbd>Ctrl</kbd>+<kbd>Z</kbd> — pause the current command.",
            "<code>jobs</code> — list background jobs, <code>bg</code> — continue in the background, <code>fg</code> — bring it back to the front.",
            "<code>nohup command &</code> — survives even if you close the terminal.",
          ] },
          { cmd: "free -h", note: "How much memory is used. The available column is what's really free." },
          { cmd: "uptime", note: "How long the computer has been on, and the average load." },
        ] },
      ],
      quiz: [
        { q: "What is a PID?", a: ["A process number", "The admin password", "A file type"], ok: 0 },
        { q: "When should you use kill -9?", a: ["When a process is frozen and ignores a normal kill", "Always, instead of kill", "To reboot the PC"], ok: 0 },
        { q: "What does Ctrl+Z do in the terminal?", a: ["Pauses the command", "Undoes the last action", "Closes the terminal"], ok: 0 },
      ],
    },
    {
      id: "p-systemd", mood: "timer", badge: "⚡ Service manager", title: "systemd services",
      intro: "systemctl, autostart, one service's logs and timers.",
      lessons: [
        { title: "systemctl", blocks: [
          { p: "<b>systemd</b> boots the system and looks after <b>services</b>: the network, sound, Bluetooth, the login screen. You manage them with <code>systemctl</code>:" },
          { table: { head: ["Command", "What it does"], rows: [
            ["<code>systemctl status name</code>", "Is the service running, plus its latest log lines"],
            ["<code>sudo systemctl start / stop name</code>", "Start / stop it now"],
            ["<code>sudo systemctl restart name</code>", "Restart it"],
            ["<code>sudo systemctl enable name</code>", "Start it at boot (<code>--now</code> — and right now too)"],
            ["<code>sudo systemctl disable name</code>", "Remove it from autostart"],
            ["<code>systemctl list-units --type=service</code>", "All running services"],
          ] } },
          { cmd: "sudo systemctl enable --now bluetooth" },
          { p: "There are also <b>user</b> services that run as you: <code>systemctl --user status pipewire</code>." },
        ] },
        { title: "Logs and timers", blocks: [
          { cmd: "journalctl -u NetworkManager -b", note: "One service's log since this boot." },
          { cmd: "journalctl -f", note: "Watch the log live (quit: Ctrl+C)." },
          { p: "systemd <b>timers</b> replace cron: they start services on a schedule. FurrOS uses one to clean the pacman cache, for example:" },
          { cmd: "systemctl list-timers" },
          { say: "If something “doesn't start by itself after a reboot”, someone almost always forgot <code>enable</code>. start is for now, enable is forever 🖤" },
        ] },
      ],
      quiz: [
        { q: "How do you enable a service at boot and start it right away?", a: ["sudo systemctl enable --now name", "sudo systemctl start name", "systemctl status name"], ok: 0 },
        { q: "How do you see one service's log?", a: ["journalctl -u name", "cat name", "pacman -Qi name"], ok: 0 },
        { q: "What are systemd timers?", a: ["Starting services on a schedule", "The clock on the panel", "A stopwatch in the terminal"], ok: 0 },
      ],
    },
    {
      id: "p-disks", mood: "hoodie", badge: "⚡ Disk keeper", title: "Disks and space",
      intro: "lsblk, df, du, mounting, UUIDs and /etc/fstab.",
      lessons: [
        { title: "Which disks, and where's the space", blocks: [
          { cmd: "lsblk -f", note: "All disks and partitions: file system, label, UUID, where they're mounted." },
          { cmd: "df -h", note: "Free space on each partition." },
          { cmd: "du -sh ~/.cache", note: "How big a folder is." },
          { cmd: "sudo pacman -S ncdu && ncdu ~", note: "Interactive: walk the folders with the arrows and see what ate your space." },
          { warn: "On Btrfs, <code>df</code> sometimes lies because of snapshots and compression. The exact picture: <code>sudo btrfs filesystem usage /</code>." },
        ] },
        { title: "Mount a disk for good", blocks: [
          { p: "USB sticks mount by themselves. A second internal disk can be mounted at every boot: you add it to <code>/etc/fstab</code> by its <b>UUID</b> (names like sdb can change, a UUID never does)." },
          { cmd: "sudo mkdir -p /mnt/data && sudo mount /dev/sdb1 /mnt/data", noRun: true, note: "Mount it by hand once. Unmount: sudo umount /mnt/data" },
          { p: "The fstab line (take the UUID from <code>lsblk -f</code>):" },
          { cmd: "UUID=xxxx-xxxx  /mnt/data  ext4  defaults,nofail  0 2", noRun: true, note: "nofail — the system still boots if the disk is missing." },
          { cmd: "sudo mount -a", note: "Test fstab without rebooting: no errors means everything mounts." },
          { say: "A mistake in fstab can stop the system from booting. So always <code>nofail</code> for extra disks, and always <code>sudo mount -a</code> before rebooting 🖤" },
        ] },
      ],
      quiz: [
        { q: "Which command shows free space on the partitions?", a: ["df -h", "ls -l", "free -h"], ok: 0 },
        { q: "Why use the UUID in fstab instead of /dev/sdb1?", a: ["sdX names can change, the UUID doesn't", "The UUID is shorter", "It's faster"], ok: 0 },
        { q: "What does the nofail option do?", a: ["The system boots even if the disk is missing", "The disk will never break", "Turns off disk checks forever"], ok: 0 },
      ],
    },
    {
      id: "p-users", mood: "grr", badge: "⚡ Gatekeeper", title: "Users, groups, permissions",
      intro: "New users, groups, chmod with numbers and chown.",
      lessons: [
        { title: "Users and groups", blocks: [
          { cmd: "sudo useradd -m -G wheel -s /bin/bash sister && sudo passwd sister", noRun: true, note: "A new user with a home folder and sudo rights (the wheel group)." },
          { cmd: "groups", note: "Which groups you're in." },
          { cmd: "sudo usermod -aG docker $USER", noRun: true, note: "Add yourself to a group. -a is a must, or you'll be dropped from all your other groups! Takes effect after you log in again." },
          { p: "Groups give access to devices and features: <code>wheel</code> — sudo, <code>libvirt</code> — virtual machines, <code>docker</code> — Docker." },
        ] },
        { title: "chmod with numbers, and chown", blocks: [
          { p: "Permissions can be written as numbers: r=4, w=2, x=1, added up for the owner, the group and everyone else." },
          { table: { head: ["Number", "Permissions", "For"], rows: [
            ["<code>755</code>", "rwxr-xr-x", "Scripts and folders"], ["<code>644</code>", "rw-r--r--", "Regular files"],
            ["<code>600</code>", "rw-------", "Secrets: SSH keys, passwords"], ["<code>700</code>", "rwx------", "A private folder"],
          ] } },
          { cmd: "chmod 600 ~/.ssh/id_ed25519" },
          { cmd: "sudo chown -R $USER:$USER ~/Games", note: "Take back a folder you accidentally created with sudo." },
          { say: "A classic: you created files with sudo, and now it's “Permission denied” in your own folder. One chown fixes it. Don't chmod 777 — that's leaving the door wide open 😤" },
        ] },
      ],
      quiz: [
        { q: "What do 644 permissions mean?", a: ["The owner reads and writes, everyone else only reads", "Everyone can do everything", "Nobody can do anything"], ok: 0 },
        { q: "Why does usermod need -a together with -G?", a: ["Without -a you're removed from your other groups", "It makes the command faster", "Without -a the user is deleted"], ok: 0 },
        { q: "Which group gives sudo rights on Arch and FurrOS?", a: ["wheel", "users", "audio"], ok: 0 },
      ],
    },
    {
      id: "p-net", mood: "wave", badge: "⚡ Networker", title: "Deeper into networking",
      intro: "IP addresses, ping, who's listening on which port, curl and downloads.",
      lessons: [
        { title: "Diagnostics", blocks: [
          { cmd: "ip -br a", note: "Network interfaces and their IP addresses, in short." },
          { cmd: "ping -c 4 archlinux.org", note: "Is there a connection? If an IP pings (ping 1.1.1.1) but a name doesn't, the problem is DNS." },
          { cmd: "ip route", note: "Which router the internet goes through (the default line)." },
          { cmd: "sudo ss -tulpn", note: "Which programs listen on ports on your computer." },
          { cmd: "resolvectl status", note: "Which DNS servers are used." },
        ] },
        { title: "Downloading from the terminal", blocks: [
          { cmd: "curl -LO https://example.com/file.iso", noRun: true, note: "-L follows redirects, -O saves under the original name." },
          { cmd: "curl -s ifconfig.me", note: "Your public IP address." },
          { cmd: "sha256sum file.iso", noRun: true, note: "The checksum: compare it with the one on the website. If they match, the file is intact." },
          { say: "Downloaded an ISO? Check the sum. It takes ten seconds and saves an hour of fighting a broken image 🖤" },
        ] },
      ],
      quiz: [
        { q: "ping 1.1.1.1 works but ping archlinux.org doesn't. What's wrong?", a: ["DNS", "The network card burned out", "You need to reinstall the system"], ok: 0 },
        { q: "How do you see which programs listen on ports?", a: ["sudo ss -tulpn", "ls /ports", "pacman -Q"], ok: 0 },
        { q: "Why run sha256sum after a download?", a: ["To check the file isn't broken or tampered with", "To speed up the download", "To unpack the file"], ok: 0 },
      ],
    },
    {
      id: "p-ssh", mood: "hoodie", badge: "⚡ Teleporter", title: "SSH: other computers",
      intro: "Connect to a server, keys instead of passwords, copying files.",
      lessons: [
        { title: "Connecting and keys", blocks: [
          { p: "<b>SSH</b> is a secure terminal on another computer: a server, a Raspberry Pi, your second PC." },
          { cmd: "ssh user@192.168.1.50", noRun: true },
          { p: "Typing a password every time is tedious and less secure. Make a key pair: the private key stays with you, the public one goes to the server." },
          { cmd: "ssh-keygen -t ed25519", note: "You can press Enter at the questions. A passphrase on the key is a good idea." },
          { cmd: "ssh-copy-id user@192.168.1.50", noRun: true, note: "Send the public key to the server. From then on, no password needed." },
          { warn: "The file <code>~/.ssh/id_ed25519</code> without .pub is your private key. Never send it to anyone, just like a password." },
        ] },
        { title: "Files and comfort", blocks: [
          { cmd: "scp photo.png user@192.168.1.50:~/", noRun: true, note: "Copy a file to the server." },
          { cmd: "rsync -avP ~/Music/ user@192.168.1.50:~/Music/", noRun: true, note: "Sync a folder: next time only the changes are sent." },
          { p: "To stop typing addresses, create <code>~/.ssh/config</code>:" },
          { cmd: "Host pi\n    HostName 192.168.1.50\n    User furry", noRun: true, note: "Now ssh pi is enough." },
          { say: "For others to connect to you, you need a server: <code>sudo pacman -S openssh && sudo systemctl enable --now sshd</code>, plus port 22 in the firewall. Don't turn it on if you don't need it — fewer doors, fewer problems 🖤" },
        ] },
      ],
      quiz: [
        { q: "Which key can you give to the server?", a: ["The public one (.pub)", "The private one (no .pub)", "Both"], ok: 0 },
        { q: "What copies a file to another computer over SSH?", a: ["scp", "cp", "mv"], ok: 0 },
        { q: "What is ~/.ssh/config for?", a: ["Short names and settings for servers", "Storing passwords in plain text", "Turning on the SSH server"], ok: 0 },
      ],
    },
    {
      id: "p-pacman", mood: "timer", badge: "⚡ pacman lord", title: "Grown-up pacman",
      intro: "Package details, rolling a version back, IgnorePkg and .pacnew.",
      lessons: [
        { title: "Learn everything about packages", blocks: [
          { table: { head: ["Command", "What it does"], rows: [
            ["<code>pacman -Qi name</code>", "Details of an installed package (version, size, dependencies)"],
            ["<code>pacman -Ql name</code>", "Which files the package installed"],
            ["<code>pacman -Qe</code>", "What you installed yourself, without dependencies"],
            ["<code>pacman -Qdt</code>", "Orphans: dependencies nothing needs any more"],
            ["<code>pactree name</code>", "Dependency tree (pacman-contrib package)"],
            ["<code>expac -H M '%m\\t%n' | sort -h | tail</code>", "The heaviest packages (expac package)"],
          ] } },
        ] },
        { title: "Roll back and hold", blocks: [
          { p: "A new version broke something? The old one is in the cache, and you can install it back:" },
          { cmd: "ls /var/cache/pacman/pkg/ | grep firefox" },
          { cmd: "sudo pacman -U /var/cache/pacman/pkg/firefox-VERSION-x86_64.pkg.tar.zst", noRun: true },
          { p: "To stop pacman from updating that package for now, add it to <code>/etc/pacman.conf</code> with the line <code>IgnorePkg = firefox</code>. Remember to remove it later: holding old versions for long is risky on Arch." },
          { cmd: "sudo pacdiff", note: "Sort out .pacnew files: compare the new sample config with yours and decide what to keep." },
          { say: "A rollback is a plaster, not a cure. Roll back, file a bug report, update again in a couple of days. That's how pros do it 🖤" },
        ] },
      ],
      quiz: [
        { q: "How do you see the files a package installed?", a: ["pacman -Ql name", "pacman -Ss name", "pacman -R name"], ok: 0 },
        { q: "Where are old package versions kept for rollbacks?", a: ["/var/cache/pacman/pkg", "/tmp", "~/Downloads"], ok: 0 },
        { q: "What does pacdiff do?", a: ["Helps you sort out .pacnew files", "Removes pacman", "Compares two systems"], ok: 0 },
      ],
    },
    {
      id: "p-aur", mood: "grr", badge: "⚡ Builder", title: "The AUR by hand",
      intro: "What's inside a PKGBUILD, makepkg, and how not to catch a nasty package.",
      lessons: [
        { title: "Building without a helper", blocks: [
          { p: "yay does this for you, but it's worth knowing what happens. An AUR package isn't a program, it's a <b>recipe</b>: a PKGBUILD file used to build the program on your machine." },
          { cmd: "sudo pacman -S --needed base-devel git" },
          { cmd: "git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin" },
          { cmd: "less PKGBUILD", note: "Read the recipe first! Look at source (where it downloads from) and at the commands in package()." },
          { cmd: "makepkg -si", note: "Build and install (with dependencies). Never run makepkg with sudo." },
        ] },
        { title: "How not to get caught", blocks: [
          { ul: [
            "Look at the votes and popularity on aur.archlinux.org.",
            "Check the last update date and the comments: problems get reported there.",
            "Anything in a PKGBUILD that downloads from odd websites or runs <code>curl … | sh</code> is suspicious.",
            "When updating, yay shows a diff of the recipe. Read it, especially for little-known packages.",
          ] },
          { cmd: "yay -Sua", note: "Update only the AUR packages." },
          { say: "The AUR is a market: great stuff and shady stuff. A package with five votes and a recipe that pulls something from a file-sharing site? Pass 😤" },
        ] },
      ],
      quiz: [
        { q: "What is a PKGBUILD?", a: ["A recipe for building a package", "A ready-made program", "pacman's logs"], ok: 0 },
        { q: "Can you run makepkg with sudo?", a: ["No, makepkg runs as a normal user", "Yes, that's how it's done", "Only on Fridays"], ok: 0 },
        { q: "What's suspicious in a PKGBUILD?", a: ["Downloads from odd websites and curl | sh", "Comments", "The pkgver field"], ok: 0 },
      ],
    },
    {
      id: "p-archive", mood: "hoodie", badge: "⚡ Packer", title: "Archives and compression",
      intro: "tar, zip, zstd and 7z: pack, unpack, peek inside.",
      lessons: [
        { title: "tar and friends", blocks: [
          { p: "<b>tar</b> glues many files into one, and gzip, xz or zstd compress it. Remember the letters: <b>c</b> create, <b>x</b> extract, <b>t</b> list, <b>f</b> file, <b>v</b> verbose." },
          { cmd: "tar -czf backup.tar.gz ~/Documents", note: "Pack with gzip." },
          { cmd: "tar --zstd -cf backup.tar.zst ~/Documents", note: "zstd: faster and usually smaller. Arch packages are compressed with it too." },
          { cmd: "tar -xf backup.tar.gz -C ~/restore", note: "Unpack into a folder (tar detects the compression itself)." },
          { cmd: "tar -tf backup.tar.gz | head", note: "See what's inside without unpacking." },
        ] },
        { title: "zip, 7z and rar", blocks: [
          { cmd: "zip -r photos.zip ~/Pictures", note: "Every system understands zip — handy for friends on Windows." },
          { cmd: "unzip photos.zip -d photos" },
          { cmd: "sudo pacman -S 7zip && 7z x archive.7z", note: "7z unpacks almost anything, including .rar." },
          { say: "File managers handle archives too: right-click → “Compress” or “Extract”. The terminal is for when you need lots, fast 🖤" },
        ] },
      ],
      quiz: [
        { q: "Which tar letter means “extract”?", a: ["x", "c", "z"], ok: 0 },
        { q: "How do you see an archive's contents without unpacking it?", a: ["tar -tf archive", "tar -xf archive", "cat archive"], ok: 0 },
        { q: "Which format is easiest to send to a friend on Windows?", a: ["zip", "tar.zst", "pkg.tar.zst"], ok: 0 },
      ],
    },
    {
      id: "p-script", mood: "wave", badge: "⚡ Scripter", title: "Your own scripts",
      intro: "shebang, variables, conditions, loops, arguments and Pixie's graduation.",
      lessons: [
        { title: "Your first script", blocks: [
          { p: "A script is a text file full of commands. The first line (the <b>shebang</b>) says what runs it:" },
          { cmd: "#!/bin/bash\nset -euo pipefail\nname=${1:-friend}\necho \"Hi, $name! Today is $(date +%A)\"", noRun: true, note: "set -euo pipefail: stop at the first error. $1 is the first argument, :-friend a default value. $(…) inserts a command's output." },
          { cmd: "nano ~/.local/bin/hello && chmod +x ~/.local/bin/hello", note: "Create the script and make it executable. Then simply: hello Pixie" },
        ] },
        { title: "Conditions and loops", blocks: [
          { cmd: "if [ -f ~/.bashrc ]; then\n  echo \"bashrc is there\"\nelse\n  echo \"no bashrc\"\nfi", noRun: true, note: "-f file exists, -d folder, -z empty string. The spaces inside [ ] are required!" },
          { cmd: "for f in ~/Pictures/*.png; do\n  echo \"Found: $f\"\ndone", noRun: true },
          { p: "A real-life example: rename every screenshot, adding the date:" },
          { cmd: "for f in Screenshot*.png; do mv -- \"$f\" \"$(date +%F)-$f\"; done", noRun: true },
          { tip: "Check your scripts with <b>shellcheck</b> (<code>sudo pacman -S shellcheck</code>): it finds mistakes that would otherwise pop up at the worst moment." },
          { say: "That's it, you've finished my level! You chain commands, manage services, hop over SSH and write scripts. Danyok is next, and I think he has a lemon 🍋🖤", mood: "lying" },
        ] },
      ],
      quiz: [
        { q: "What is a shebang?", a: ["The #! first line that says what runs the script", "A bash error", "A comment at the end"], ok: 0 },
        { q: "What does $1 hold?", a: ["The script's first argument", "The script's price", "The line number"], ok: 0 },
        { q: "What does set -e do?", a: ["Stops the script at the first error", "Turns on emoji", "Deletes the variables"], ok: 0 },
      ],
    },
  ] },

  danyok: { chapters: [
    {
      id: "d-boot", mood: "wave", badge: "🍋 Bootloader", title: "How Linux boots",
      intro: "UEFI, the FurrBoot boot menu, the kernel, initramfs and systemd: what happens after the power button.",
      lessons: [
        { title: "The boot chain", blocks: [
          { ol: [
            "<b>UEFI</b> (the board's firmware) finds the EFI partition and starts the boot loader from it.",
            "<b>FurrBoot</b> shows the FurrOS menu and loads the <b>kernel</b> (vmlinuz) and the <b>initramfs</b> into memory. Old PCs without UEFI get Limine instead, and the spare GRUB is always in the board's boot menu (F11/F12/F8).",
            "The <b>initramfs</b> is a tiny temporary system: it holds the drivers to find and mount the real root partition (Btrfs, encryption, NVMe).",
            "The kernel starts <b>systemd</b> (PID 1), and systemd starts every service and the login screen.",
          ] },
          { cmd: "systemd-analyze", note: "How long each boot stage took." },
          { cmd: "systemd-analyze blame | head", note: "Which services take the longest to start." },
        ] },
        { title: "Kernel parameters and the initramfs", blocks: [
          { p: "Kernel parameters live in <code>/etc/kernel/cmdline</code>. After editing, update the boot menu:" },
          { cmd: "sudo furrboot-update" },
          { p: "The spare GRUB has its own settings: <code>/etc/default/grub</code>, then <code>sudo grub-mkconfig -o /boot/grub/grub.cfg</code>." },
          { cmd: "cat /proc/cmdline", note: "Which parameters the kernel was booted with right now." },
          { p: "What goes into the initramfs is set in <code>/etc/mkinitcpio.conf</code> (the MODULES and HOOKS lines). After editing, rebuild it:" },
          { cmd: "sudo mkinitcpio -P" },
          { say: "Press <kbd>E</kbd> in the FurrBoot menu once — you'll see the boot line and can add a parameter just for this boot. It saves the day when the system won't boot with new settings. And if a new kernel fails to boot three times in a row, FurrBoot starts the spare one by itself. The lemon approves 🍋" },
        ] },
      ],
      quiz: [
        { q: "What is the initramfs?", a: ["A tiny temporary system that mounts the real root", "A swap file", "The boot menu"], ok: 0 },
        { q: "What starts as the first process (PID 1)?", a: ["systemd", "GRUB", "bash"], ok: 0 },
        { q: "What do you do after editing /etc/kernel/cmdline?", a: ["sudo furrboot-update", "Nothing", "sudo pacman -Syu"], ok: 0 },
      ],
    },
    {
      id: "d-kernel", mood: "hoodie", badge: "🍋 Kernel hacker", title: "The kernel and modules",
      intro: "Kernel flavours, modules, blacklists, DKMS and sysctl.",
      lessons: [
        { title: "Kernels and modules", blocks: [
          { cmd: "uname -r", note: "The running kernel's version." },
          { p: "Arch has several kernels: <code>linux</code> (latest), <code>linux-lts</code> (long-term support, a spare), <code>linux-zen</code> (tuned for responsiveness). FurrOS has its own too, <code>linux-furros</code>. You can keep two: the boot menu updates itself and the second one shows up under «Other kernel»." },
          { cmd: "sudo pacman -S linux-lts linux-lts-headers", noRun: true, note: "A spare kernel: if a new one breaks something, boot the LTS one." },
          { cmd: "lsmod | head", note: "Loaded modules (drivers)." },
          { cmd: "modinfo btusb", note: "What a module is and which parameters it takes." },
        ] },
        { title: "Blacklists, DKMS, sysctl", blocks: [
          { p: "A module gets in the way (a buggy webcam driver, say)? Block it:" },
          { cmd: "echo 'blacklist uvcvideo' | sudo tee /etc/modprobe.d/no-webcam.conf", noRun: true },
          { p: "<b>DKMS</b> rebuilds third-party modules (nvidia-580xx, for example) for every new kernel. That needs headers: <code>linux-headers</code> for each installed kernel." },
          { cmd: "dkms status" },
          { p: "<b>sysctl</b> changes kernel parameters on the fly. Permanent ones go in <code>/etc/sysctl.d/*.conf</code>:" },
          { cmd: "sysctl vm.swappiness" },
          { say: "Advice worth a million lemons: keep <code>linux-lts</code> as a spare kernel. It costs next to no space, and on a bad day it saves the whole system 🍋" },
        ] },
      ],
      quiz: [
        { q: "Why keep linux-lts next to linux?", a: ["A spare kernel if the new one breaks something", "To make games faster", "Wi-Fi requires it"], ok: 0 },
        { q: "What does DKMS do?", a: ["Rebuilds third-party modules for a new kernel", "Removes old kernels", "Updates the BIOS"], ok: 0 },
        { q: "Where do permanent sysctl settings go?", a: ["/etc/sysctl.d/*.conf", "~/.bashrc", "/boot/grub"], ok: 0 },
      ],
    },
    {
      id: "d-btrfs", mood: "timer", badge: "🍋 Btrfs master", title: "Grown-up Btrfs",
      intro: "Subvolumes, snapshots, compression, scrub and how much space is really used.",
      lessons: [
        { title: "Subvolumes and snapshots", blocks: [
          { p: "FurrOS on Btrfs creates <b>subvolumes</b>: <code>@</code> (the system), <code>@home</code>, <code>@log</code>, <code>@pkg</code>. A snapshot is taken per subvolume, so rolling the system back doesn't touch your files in home." },
          { cmd: "sudo btrfs subvolume list /" },
          { cmd: "sudo snapper -c root list", note: "System snapshots. They're copy-on-write: they take almost no space until files change." },
          { cmd: "sudo snapper -c root create -d \"before the experiment\"", note: "A manual snapshot before risky changes." },
          { cmd: "sudo snapper -c root status 41..42", noRun: true, note: "What changed between two snapshots." },
        ] },
        { title: "Compression and health", blocks: [
          { p: "FurrOS mounts Btrfs with zstd compression: files take less space on disk and often even read faster." },
          { cmd: "sudo pacman -S compsize && sudo compsize /usr", note: "How much compression really saves." },
          { cmd: "sudo btrfs filesystem usage /", note: "The exact space picture (df lies on Btrfs)." },
          { cmd: "sudo btrfs scrub start / && sudo btrfs scrub status /", note: "Check all data against its checksums. Worth doing monthly." },
          { warn: "<code>btrfs check --repair</code> is a last resort, only on advice from people who know, and with a backup. It can make things worse." },
          { say: "A snapshot isn't a backup. It sits on the same disk. Disk dies — snapshots die with it. Backups go on another disk, lemons go in the fridge 🍋" },
        ] },
      ],
      quiz: [
        { q: "Why doesn't a system rollback touch your files in home?", a: ["home is a separate subvolume, @home", "Snapper can't roll back", "Files in home are read-only"], ok: 0 },
        { q: "What checks Btrfs data against its checksums?", a: ["btrfs scrub", "fsck.vfat", "rm -rf"], ok: 0 },
        { q: "Do snapshots replace backups?", a: ["No, snapshots are on the same disk", "Yes, completely", "Only on SSDs"], ok: 0 },
      ],
    },
    {
      id: "d-units", mood: "hoodie", badge: "🍋 On duty", title: "Your own services and timers",
      intro: "Writing unit files, drop-in edits and timers instead of cron.",
      lessons: [
        { title: "Your own service", blocks: [
          { p: "A service is described by a <b>unit</b> file. Your own system units go in <code>/etc/systemd/system/</code>, user ones in <code>~/.config/systemd/user/</code>." },
          { cmd: "[Unit]\nDescription=My bot\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nExecStart=/home/furry/bot/run.sh\nRestart=on-failure\n\n[Install]\nWantedBy=default.target", noRun: true, note: "~/.config/systemd/user/bot.service — a bot that restarts if it crashes." },
          { cmd: "systemctl --user daemon-reload && systemctl --user enable --now bot", noRun: true },
          { cmd: "loginctl enable-linger $USER", noRun: true, note: "So user services run even when you're not logged in." },
        ] },
        { title: "Edits and timers", blocks: [
          { p: "System unit files aren't edited directly (an update would overwrite them). Use a <b>drop-in</b> instead:" },
          { cmd: "sudo systemctl edit sddm", noRun: true, note: "Opens an editor for an override file. Whatever you write there survives updates." },
          { p: "A timer is a .timer and a .service with the same name:" },
          { cmd: "[Timer]\nOnCalendar=daily\nPersistent=true\n\n[Install]\nWantedBy=timers.target", noRun: true, note: "backup.timer: starts backup.service once a day. Persistent — catch up a missed run if the PC was off." },
          { cmd: "systemd-analyze calendar \"Mon *-*-* 10:00\"", note: "Check a schedule: when it fires next." },
          { say: "Timers beat cron: everything's visible in <code>systemctl list-timers</code>, logs are in journalctl, and missed runs catch up. Sour advice, but true 🍋" },
        ] },
      ],
      quiz: [
        { q: "Where do your own user services go?", a: ["~/.config/systemd/user/", "/boot", "/tmp"], ok: 0 },
        { q: "What's the right way to change a system service?", a: ["sudo systemctl edit name (a drop-in)", "Edit the file in /usr/lib/systemd directly", "There isn't one"], ok: 0 },
        { q: "What does Persistent=true do in a timer?", a: ["Catches up a missed run", "Prevents stopping", "Runs every second"], ok: 0 },
      ],
    },
    {
      id: "d-net", mood: "wave", badge: "🍋 Network admin", title: "Networking inside out",
      intro: "NetworkManager from the terminal, DNS, /etc/hosts, ufw rules and a VPN that works even where VPNs are blocked.",
      lessons: [
        { title: "Connections and DNS", blocks: [
          { cmd: "nmcli connection show" },
          { cmd: "nmcli connection modify \"My network\" ipv4.dns \"1.1.1.1 9.9.9.9\" ipv4.ignore-auto-dns yes", noRun: true, note: "Your own DNS for one network. Apply: nmcli connection up \"My network\"." },
          { p: "<code>/etc/hosts</code> is a local “phone book”: name → IP. Handy for home servers:" },
          { cmd: "192.168.1.50  pi.home", noRun: true, note: "A line in /etc/hosts. Now ssh furry@pi.home." },
        ] },
        { title: "Firewall and VPN", blocks: [
          { cmd: "sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp", noRun: true, note: "SSH from the home network only." },
          { cmd: "sudo ufw status numbered", note: "Rules with numbers; delete one: sudo ufw delete N." },
          { p: "<b>VPN, honestly:</b> plain <b>WireGuard</b> is built into the kernel and very fast, but in Russia it (like OpenVPN) is often cut off: the blocking recognises the protocol itself. It works where it isn't blocked, for example to reach your own home server. The config goes in <code>/etc/wireguard/wg0.conf</code>:" },
          { cmd: "sudo pacman -S wireguard-tools && sudo wg-quick up wg0", noRun: true, note: "Disconnect: sudo wg-quick down wg0." },
          { p: "If WireGuard won't connect, you need a disguised protocol. <b>AmneziaWG</b> is a WireGuard fork that hides the recognisable packets. The easiest way is the <b>AmneziaVPN</b> app from the AUR: paste the key or config from your VPN provider (or your own Amnezia server) and press Connect:" },
          { cmd: "yay -S amneziavpn-bin", noRun: true, note: "For the terminal there is amneziawg-tools + amneziawg-dkms (AUR): config in /etc/amnezia/amneziawg/awg0.conf, start with sudo awg-quick up awg0." },
          { p: "If your provider gives you a <b>VLESS / Reality subscription</b> (a vless://… link or a subscription URL), you need a client for it: <b>Throne</b> (formerly NekoRay) or <b>Hiddify</b>. Both are in the AUR: paste the link and you're done:" },
          { cmd: "yay -S throne-bin", noRun: true, note: "Or yay -S hiddify. AUR packages are made by people, not by Arch: check what you install, and take keys only from your own provider." },
          { say: "A firewall rule is a lock: write the narrowest one that works. “Open everything to everyone” isn't a setting, it's lemonade instead of a lemon 🍋" },
        ] },
      ],
      quiz: [
        { q: "What is /etc/hosts for?", a: ["Mapping names to IP addresses locally", "Storing Wi-Fi passwords", "A list of packages"], ok: 0 },
        { q: "How do you allow SSH only from the home network?", a: ["ufw allow from 192.168.1.0/24 to any port 22", "ufw disable", "ufw allow 22 from everyone"], ok: 0 },
        { q: "WireGuard won't connect because of blocking. What should you try?", a: ["AmneziaWG (the AmneziaVPN app) or a VLESS/Reality client", "Reinstall the kernel", "Turn off the firewall"], ok: 0 },
      ],
    },
    {
      id: "d-sshd", mood: "grr", badge: "🍋 Server owner", title: "Your own SSH server",
      intro: "Keys only, no root, and tunnels.",
      lessons: [
        { title: "Tightening the screws", blocks: [
          { cmd: "sudo pacman -S openssh && sudo systemctl enable --now sshd", noRun: true },
          { p: "Settings go in <code>/etc/ssh/sshd_config.d/</code> (your own file, e.g. <code>10-furros.conf</code>):" },
          { cmd: "PermitRootLogin no\nPasswordAuthentication no\nKbdInteractiveAuthentication no", noRun: true, note: "Keys only, no root. Make sure key login works first!" },
          { cmd: "sudo sshd -t && sudo systemctl reload sshd", noRun: true, note: "sshd -t checks the config. A mistake there can lock you out." },
          { warn: "Editing SSH on a remote server? Keep a second session open until you've tested the new login. Otherwise you can lock yourself out." },
        ] },
        { title: "Tunnels", blocks: [
          { cmd: "ssh -L 8080:localhost:80 user@server", noRun: true, note: "The server's web panel (port 80) opens on your localhost:8080. Nothing needs to be exposed to the internet." },
          { cmd: "ssh -D 1080 user@server", noRun: true, note: "A SOCKS proxy through the server." },
          { cmd: "sudo journalctl -u sshd | grep -i failed | tail", note: "Who tried to guess a password." },
          { say: "A server with a password and an open port 22 gets attacked within minutes of going up. Use keys, and the bots can go sit in the corner. With a lemon 🍋" },
        ] },
      ],
      quiz: [
        { q: "What must you do before PasswordAuthentication no?", a: ["Make sure key login works", "Delete the keys", "Turn off the firewall"], ok: 0 },
        { q: "How do you check the sshd config for errors?", a: ["sudo sshd -t", "ssh -v", "cat sshd"], ok: 0 },
        { q: "What does ssh -L 8080:localhost:80 do?", a: ["Forwards the server's port to you", "Opens the port to the internet", "Deletes port 80"], ok: 0 },
      ],
    },
    {
      id: "d-perf", mood: "timer", badge: "🍋 Overclocker", title: "Performance",
      intro: "Where it's slow: CPU, memory, disk. zram, governors and temperatures.",
      lessons: [
        { title: "Find the bottleneck", blocks: [
          { table: { head: ["Tool", "What it shows"], rows: [
            ["<code>btop</code>", "Everything at once, nicely: CPU, memory, disks, network, processes"],
            ["<code>sudo iotop</code>", "Who's hammering the disk"], ["<code>free -h</code>", "Memory and swap"],
            ["<code>sensors</code>", "Temperatures (lm_sensors package)"], ["<code>nvtop</code>", "GPU load"],
            ["<code>journalctl -k -p 4</code>", "Kernel warnings: overheating, disk errors"],
          ] } },
          { cmd: "sudo pacman -S btop lm_sensors nvtop iotop" },
        ] },
        { title: "Memory and CPU", blocks: [
          { p: "<b>zram</b> is compressed swap right in memory: when RAM runs low, the system slows down far less than with swap on disk." },
          { cmd: "zramctl", note: "Is zram there? To set it up: the zram-generator package and /etc/systemd/zram-generator.conf." },
          { p: "The <b>governor</b> decides how quickly the CPU raises its clock:" },
          { cmd: "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" },
          { cmd: "powerprofilesctl set performance", noRun: true, note: "The performance profile (or balanced / power-saver). Handy before gaming; on a laptop it costs battery." },
          { say: "Measure first, then tweak. An “internet tweak” without measuring is fortune-telling with lemon pips 🍋" },
        ] },
      ],
      quiz: [
        { q: "What is zram?", a: ["Compressed swap in RAM", "A new kind of SSD", "A GPU driver"], ok: 0 },
        { q: "What shows who's loading the disk?", a: ["iotop", "ping", "ls"], ok: 0 },
        { q: "What should you do before performance tweaks?", a: ["Measure where the bottleneck is", "Change everything at once", "Reinstall the system"], ok: 0 },
      ],
    },
    {
      id: "d-gpu", mood: "wave", badge: "🍋 Pixel wizard", title: "Graphics: Wayland, X11, drivers",
      intro: "Mesa and NVIDIA, Wayland versus X11, hybrid graphics and checking Vulkan.",
      lessons: [
        { title: "Who draws the picture", blocks: [
          { p: "<b>Mesa</b> is the open driver stack for AMD and Intel; it's in the kernel and works out of the box. For NVIDIA: <code>nvidia-open</code> (RTX and GTX 16xx) or <code>nvidia-580xx</code> from [furros] (GTX 750–10xx). See what's installed: <code>furros-drivers</code>." },
          { cmd: "echo $XDG_SESSION_TYPE", note: "wayland or x11: what your session runs on." },
          { cmd: "sudo pacman -S vulkan-tools mesa-utils && vulkaninfo --summary && glxinfo -B", noRun: true, note: "Which GPU and driver Vulkan and OpenGL use." },
          { p: "<b>Wayland</b> is the new display protocol: smoother, safer, better with mixed refresh rates. <b>X11</b> is the old one, but some programs still live only there. They run on Wayland through <b>Xwayland</b>." },
        ] },
        { title: "Hybrid graphics and NVIDIA", blocks: [
          { p: "A laptop with two GPUs: the integrated one runs by default (saving battery), and heavy stuff runs on the dedicated one:" },
          { cmd: "prime-run steam", noRun: true, note: "The nvidia-prime package. For AMD+AMD: DRI_PRIME=1 program." },
          { cmd: "cat /sys/module/nvidia_drm/parameters/modeset", note: "Y — the mode Wayland needs with NVIDIA is on." },
          { say: "Black screen on NVIDIA after an update? Almost always the driver doesn't match the kernel. Console (Ctrl+Alt+F3), <code>sudo pacman -Syu</code>, reboot. Or the spare LTS kernel 🍋" },
        ] },
      ],
      quiz: [
        { q: "How do you know if you're on Wayland or X11?", a: ["echo $XDG_SESSION_TYPE", "uname -r", "ls /wayland"], ok: 0 },
        { q: "What is Xwayland?", a: ["A way to run X11 programs inside Wayland", "A new desktop", "An NVIDIA driver"], ok: 0 },
        { q: "How do you run a program on a laptop's dedicated NVIDIA GPU?", a: ["prime-run program", "sudo program", "nvidia program --fast"], ok: 0 },
      ],
    },
    {
      id: "d-pkg", mood: "hoodie", badge: "🍋 Packager", title: "Your own package and repository",
      intro: "Writing a PKGBUILD, checking it with namcap and building your own repository.",
      lessons: [
        { title: "A PKGBUILD from scratch", blocks: [
          { p: "Your own script or program is best installed as a package: pacman knows its files, updates it and removes it cleanly." },
          { cmd: "pkgname=lemon-timer\npkgver=1.0\npkgrel=1\npkgdesc=\"A timer with a lemon\"\narch=(any)\nlicense=(MIT)\ndepends=(bash libnotify)\nsource=(lemon-timer)\nsha256sums=(SKIP)\n\npackage() {\n  install -Dm755 lemon-timer \"$pkgdir/usr/bin/lemon-timer\"\n}", noRun: true, note: "A PKGBUILD next to the lemon-timer script." },
          { cmd: "makepkg -si", noRun: true },
          { cmd: "namcap PKGBUILD *.pkg.tar.zst", noRun: true, note: "Checks for common mistakes: dependencies, permissions, paths." },
          { tip: "Instead of SKIP, put real checksums: <code>updpkgsums</code> (pacman-contrib package) calculates them for you." },
        ] },
        { title: "Your own repository", blocks: [
          { p: "Several of your own packages for several computers are easiest to keep in a repository, just like FurrOS does with its [furros]:" },
          { cmd: "repo-add ~/repo/lemon.db.tar.zst ~/repo/*.pkg.tar.zst", noRun: true },
          { cmd: "[lemon]\nSigLevel = Optional TrustAll\nServer = file:///home/furry/repo", noRun: true, note: "A section in /etc/pacman.conf. For other people, packages get signed (gpg + makepkg --sign) and SigLevel = Required." },
          { say: "That's exactly how FurrOS delivers your wallpapers, Lapa's School and drivers: signed packages in the [furros] repository, updated by a plain <code>pacman -Syu</code> 🍋" },
        ] },
      ],
      quiz: [
        { q: "Where does package() put the files?", a: ["In $pkgdir, which then becomes the package", "Straight into /usr", "In your home folder"], ok: 0 },
        { q: "What checks a package for common mistakes?", a: ["namcap", "ping", "grep"], ok: 0 },
        { q: "Which command creates a repository database?", a: ["repo-add", "pacman -Syu", "mkinitcpio"], ok: 0 },
      ],
    },
    {
      id: "d-containers", mood: "wave", badge: "🍋 Container captain", title: "Containers",
      intro: "Podman and Docker, distrobox for apps from other distros, Flatpak permissions.",
      lessons: [
        { title: "Podman and Docker", blocks: [
          { p: "A container is an isolated box with its own mini-system. The program inside doesn't bother the main system and is removed with one command." },
          { cmd: "sudo pacman -S podman && podman run --rm -it archlinux bash", noRun: true, note: "A clean Arch in a container. --rm — delete it on exit. Podman works without root." },
          { cmd: "podman ps -a && podman images", noRun: true, note: "Containers and images. Clean up: podman system prune." },
          { p: "Docker works similarly (<code>sudo pacman -S docker && sudo systemctl enable --now docker</code>), but through a root service." },
        ] },
        { title: "distrobox and Flatpak", blocks: [
          { p: "<b>distrobox</b> runs another distro in a container, but with your home folder, sound and graphics. An app that only exists for Ubuntu? No problem:" },
          { cmd: "sudo pacman -S distrobox podman && distrobox create -n ubuntu -i ubuntu:24.04 && distrobox enter ubuntu", noRun: true },
          { cmd: "distrobox-export --app program-name", noRun: true, note: "Inside the container: add the app to the FurrOS menu." },
          { p: "Flatpak app permissions (folders, devices) are easy to view and change in <b>Flatseal</b>:" },
          { cmd: "flatpak install flathub com.github.tchx84.Flatseal", noRun: true },
          { say: "Want to try something dodgy? Do it in a container. Didn't like it — delete the box, the system stays clean. Like a lemon in a bag: no drips 🍋" },
        ] },
      ],
      quiz: [
        { q: "What does podman run --rm do?", a: ["Deletes the container on exit", "Deletes the image", "Deletes podman"], ok: 0 },
        { q: "What is distrobox for?", a: ["Running apps from other distros as if native", "Speeding up Wi-Fi", "Taking Btrfs snapshots"], ok: 0 },
        { q: "Where can you easily change Flatpak app permissions?", a: ["Flatseal", "GRUB", "htop"], ok: 0 },
      ],
    },
    {
      id: "d-vm", mood: "timer", badge: "🍋 VM wrangler", title: "Virtual machines",
      intro: "KVM/QEMU and virt-manager: Windows or another Linux in a window.",
      lessons: [
        { title: "Installing KVM", blocks: [
          { cmd: "grep -Ec '(vmx|svm)' /proc/cpuinfo", note: "More than zero — the CPU supports virtualization. If 0, enable VT-x/AMD-V (SVM) in the BIOS." },
          { cmd: "sudo pacman -S qemu-desktop libvirt virt-manager dnsmasq edk2-ovmf swtpm", noRun: true, note: "edk2-ovmf — UEFI, swtpm — the TPM Windows 11 needs." },
          { cmd: "sudo systemctl enable --now libvirtd && sudo usermod -aG libvirt $USER", noRun: true, note: "Log out and back in so the group applies." },
          { p: "Then open <b>Virtual Machine Manager</b>, click “Create a new VM” and pick an ISO. For simple cases there's also <b>GNOME Boxes</b>." },
        ] },
        { title: "Making it fast", blocks: [
          { ul: [
            "Disk and network — the <b>virtio</b> type: much faster than emulated ones. Windows needs the virtio-win drivers (an ISO from the Fedora site).",
            "CPU — <b>host-passthrough</b> mode.",
            "Don't give the VM more than half your cores and memory; the host has to live too.",
            "VM snapshots before experiments, same as with FurrOS itself.",
          ] },
          { say: "A VM is the best training ground. Want to break the boot loader to learn how to fix it? Break it there, not on your main system 🍋" },
        ] },
      ],
      quiz: [
        { q: "How do you check that the CPU supports virtualization?", a: ["grep -Ec '(vmx|svm)' /proc/cpuinfo", "uname -r", "lsusb"], ok: 0 },
        { q: "Which disk and network type is fastest in KVM?", a: ["virtio", "IDE", "floppy"], ok: 0 },
        { q: "Which group do you join for libvirt?", a: ["libvirt", "wheel", "audio"], ok: 0 },
      ],
    },
    {
      id: "d-security", mood: "grr", badge: "🍋 Paranoid", title: "Deep security",
      intro: "LUKS encryption, sudoers, pacman keys and Secure Boot.",
      lessons: [
        { title: "Encryption and sudo", blocks: [
          { p: "<b>LUKS</b> encrypts a whole partition: if your laptop is stolen, the data can't be read without the password. Encrypting a USB stick:" },
          { cmd: "sudo cryptsetup luksFormat /dev/sdX1", noRun: true, note: "WIPES everything on the partition! Then: sudo cryptsetup open /dev/sdX1 secret && sudo mkfs.ext4 /dev/mapper/secret" },
          { cmd: "sudo cryptsetup luksDump /dev/sdX1", noRun: true, note: "Details of the encryption and key slots." },
          { p: "sudo rights are only edited with <code>visudo</code>: it checks the syntax, so you can't lock yourself out of sudo." },
          { cmd: "sudo EDITOR=nano visudo -f /etc/sudoers.d/10-furry", noRun: true },
          { warn: "A broken sudoers = no sudo. So visudo only — never edit it with a regular editor." },
        ] },
        { title: "Keys and Secure Boot", blocks: [
          { p: "pacman checks every package's signature. If it complains about keys (happens after a long break):" },
          { cmd: "sudo pacman -Sy archlinux-keyring furros-keyring && sudo pacman -Su", noRun: true },
          { cmd: "pacman-key --list-keys | grep -i furros", note: "The [furros] repository key is in place." },
          { p: "<b>Secure Boot</b> with Linux can be turned on with your own keys using <b>sbctl</b> (<code>sbctl status</code>, <code>sbctl create-keys</code>, <code>sbctl enroll-keys -m</code>, then sign the boot loader and kernel). It's an advanced setup: read the Arch wiki and keep a FurrOS USB stick at hand." },
          { say: "Security is layers: updates, firewall, keys, encryption, backups. No layer is perfect; together they're a fortress. Even a lemon has a peel 🍋" },
        ] },
      ],
      quiz: [
        { q: "What do you edit sudo rights with?", a: ["visudo", "nano /etc/sudoers directly", "chmod 777"], ok: 0 },
        { q: "What does cryptsetup luksFormat do to a partition?", a: ["Creates an encrypted partition, wiping the data", "Checks the disk", "Speeds up the disk"], ok: 0 },
        { q: "pacman complains about keys. What do you update first?", a: ["archlinux-keyring (and furros-keyring)", "The kernel", "Firefox"], ok: 0 },
      ],
    },
    {
      id: "d-rescue", mood: "grr", badge: "🍋 Resuscitator", title: "Hardcore repairs",
      intro: "Fixing the boot loader, pacman's lock, an interrupted update and rescue.target.",
      lessons: [
        { title: "Typical crashes", blocks: [
          { table: { head: ["Problem", "Fix"], rows: [
            ["“unable to lock database”", "pacman isn't running? Then <code>sudo rm /var/lib/pacman/db.lck</code>"],
            ["An update was interrupted (power, battery)", "From the console or a chroot: <code>sudo pacman -Syu</code>, then <code>sudo mkinitcpio -P</code>"],
            ["“invalid or corrupted package (PGP signature)”", "Update the keyring (see the previous chapter)"],
            ["The FurrBoot menu vanished after Windows", "Pick «FurrOS» in the board's boot menu (F11/F12/F8): that is the spare GRUB. Then in the system: <code>sudo furrboot-install</code>"],
            ["Graphics won't start", "Ctrl+Alt+F3, the log: <code>journalctl -b -1 -p 3</code> (errors from the previous boot)"],
          ] } },
          { p: "If you can't even get to a console, press <kbd>E</kbd> in FurrBoot and add to the end of the parameters: <code>systemd.unit=rescue.target</code>. The system boots into a minimal mode with a root console." },
        ] },
        { title: "A full chroot", blocks: [
          { p: "From a FurrOS USB stick. For FurrOS on Btrfs:" },
          { cmd: "lsblk -f\nsudo mount -o subvol=@ /dev/nvme0n1p2 /mnt\nsudo mount /dev/nvme0n1p1 /mnt/boot/efi\nsudo arch-chroot /mnt", noRun: true, note: "Take the partition names from lsblk. The EFI partition goes to /boot/efi on a Btrfs install, to /boot on ext4 and encrypted ones. Open an encrypted disk first: cryptsetup open." },
          { p: "Inside, it's as if you were in your own system: update, reinstall the kernel (<code>pacman -S linux</code>), fix the boot menu (<code>furrboot-install</code>), edit fstab. To leave: <code>exit</code>, then <code>sudo umount -R /mnt</code>." },
          { say: "If you made it this far, a broken system doesn't scare you any more. You know how it works, so you know how to bring it back. That's what a master is 🍋" },
        ] },
      ],
      quiz: [
        { q: "pacman says “unable to lock database”, but it isn't running. What now?", a: ["Delete /var/lib/pacman/db.lck", "Reinstall the system", "Remove pacman"], ok: 0 },
        { q: "How do you boot into a minimal mode from the boot menu?", a: ["Add systemd.unit=rescue.target", "Press F12", "Add quiet"], ok: 0 },
        { q: "How do you see errors from the previous boot?", a: ["journalctl -b -1 -p 3", "dmesg --future", "pacman -Qe"], ok: 0 },
      ],
    },
    {
      id: "d-final", mood: "wave", badge: "🍋 FurrOS master", title: "Danyok's graduation",
      intro: "Git, bug reports, the Arch Wiki and how to help FurrOS.",
      lessons: [
        { title: "Git in five minutes", blocks: [
          { cmd: "git clone https://github.com/Vitlikxbox/FurrOS.git && cd FurrOS", noRun: true },
          { table: { head: ["Command", "What it does"], rows: [
            ["<code>git status</code>", "What's changed"], ["<code>git diff</code>", "The changes themselves"],
            ["<code>git add file</code>", "Stage it for saving"], ["<code>git commit -m \"what I did\"</code>", "Save a version"],
            ["<code>git log --oneline</code>", "History"], ["<code>git switch -c fix-typo</code>", "A new branch for your changes"],
          ] } },
          { tip: "Keeping your configs in git is a great habit: any bad edit can be rolled back, and moving to a new computer takes one command." },
        ] },
        { title: "How to help", blocks: [
          { ul: [
            "<b>A good bug report</b>: what you did, what you expected, what happened, the version (<code>fastfetch</code>), a log (<code>journalctl -b -p 3</code> or <code>/var/log/furros-install.log</code>).",
            "Found a mistake in a translation or a lesson? Write in the FurrOS Discord or open an issue on GitHub.",
            "The <b>Arch Wiki</b> is written by users just like you. Found something wrong? Fix it — the best gift to the Linux world.",
            "Help newcomers in the chat: explaining to someone else is the best way to understand it yourself.",
          ] },
          { say: "That's all. Three teachers, forty-two chapters. You've gone from “what's a terminal” to chroot and your own packages. Lapa is proud, Pixie approves, and from me — a lemon. You've earned it 🍋🎓" },
        ] },
      ],
      quiz: [
        { q: "What must a bug report include?", a: ["The steps, what you expected, what happened, and a log", "Just “it doesn't work”", "A screenshot of your wallpaper"], ok: 0 },
        { q: "Which command saves a version in git?", a: ["git commit", "git status", "git log"], ok: 0 },
        { q: "Who writes the Arch Wiki?", a: ["Users — and you can too", "Only Microsoft employees", "Nobody, it writes itself"], ok: 0 },
      ],
    },
  ] },
};
