/* Lapa's School, levels 2 and 3: Velvet (a confident user) and Danyok (the system inside out). 14 chapters each. */
Object.assign(window.CONTENT.es.ui, {
  levelsTitle: "Niveles", level: "Nivel",
  levelsIntro: "Tres profes, y con cada uno más difícil. Lapa te enseña a vivir en FurrOS, Velvet a dominar el sistema con soltura y Danyok a desmontarlo hasta el último tornillo.",
  lvl_lapa: "Lapa", lvl_pixie: "Velvet", lvl_danyok: "Danyok",
  diff_lapa: "principiante", diff_pixie: "usuario con soltura", diff_danyok: "maestro del sistema",
  lvlIntro_lapa: "El escritorio, archivos, terminal, programas, juegos y primeros auxilios.",
  lvlIntro_pixie: "Tuberías, procesos, servicios, discos, red, SSH, el AUR y tus propios scripts.",
  lvlIntro_danyok: "Arranque, kernel, Btrfs, tus propios servicios, contenedores, máquinas virtuales, cifrado y reparaciones extremas.",
  lvlHello_lapa: "Nivel de Lapa 🐾", lvlHello_pixie: "Ey, soy Velvet. Ahora enseño yo 🖤", lvlHello_danyok: "Buenas. Soy Danyok y tengo un limón 🍋",
  lvlText_lapa: "Lo básico: cómo vivir en FurrOS sin miedo a nada. Empieza aquí si Linux es nuevo para ti.",
  lvlText_pixie: "Lapa te enseñó a no temer a la terminal. Yo te enseñaré a mandar en ella: encadenar comandos, encontrar cualquier cosa, gestionar procesos y servicios, saltar a otros ordenadores por SSH y escribir tus propios scripts. Será un poco más difícil, pero luego harás en un minuto lo que antes te llevaba una hora.",
  lvlText_danyok: "El último nivel. Nos metemos dentro: cómo arranca el sistema, qué hace el kernel, cómo funcionan Btrfs y systemd, cómo crear tu propio paquete, levantar un contenedor y una máquina virtual, cifrar un disco y resucitar el sistema. Sin prisa, y prueba todo en una máquina virtual o con una instantánea reciente.",
  lvlFirst: "Te recomendamos terminar antes el nivel «{0}». Pero si te sientes con confianza, adelante.",
  says_pixie: "Velvet dice", says_danyok: "Danyok dice",
  nextLevel: "Siguiente: {0}",
  diplomaTitle_pixie: "Diploma de Velvet 🎓", diplomaText_pixie: "Has terminado el nivel de usuario con soltura: tuberías, procesos, servicios, discos, red, SSH, el AUR y scripts. Ahora la terminal trabaja para ti, y no al revés. Velvet lo aprueba 🖤",
  diplomaTitle_danyok: "Diploma de Danyok 🎓🍋", diplomaText_danyok: "Has terminado los tres niveles de la Escuela de Lapa. Arranque, kernel, Btrfs, systemd, paquetes, contenedores, cifrado y reparaciones ya son tuyos. Eres oficialmente maestro de FurrOS. Toma un limón 🍋",
});

window.CONTENT.es.levels = {
  pixie: { chapters: [
    {
      id: "p-shell", mood: "wave", badge: "⚡ Experta en bash", title: "Bash más a fondo",
      intro: "Rutas, comodines, variables, alias y tu ~/.bashrc.",
      lessons: [
        { title: "Rutas y comodines", blocks: [
          { p: "Una ruta puede ser <b>absoluta</b> (desde la raíz: <code>/home/furry/Documents</code>) o <b>relativa</b> (desde la carpeta actual: <code>Documents/notes.txt</code>). <code>.</code> es la carpeta actual, <code>..</code> la de arriba, <code>~</code> tu carpeta personal y <code>-</code> en <code>cd -</code> la anterior." },
          { p: "Los comodines (wildcards) abarcan muchos archivos a la vez: <code>*</code> cualquier cosa, <code>?</code> un solo carácter, <code>{a,b}</code> alternativas." },
          { cmd: "ls ~/Pictures/*.png", note: "Todos los PNG de tu carpeta Imágenes." },
          { cmd: "mkdir -p project/{src,docs,tests}", note: "Tres carpetas con un solo comando. -p crea también la carpeta padre." },
          { say: "El comodín lo expande bash, no el programa. Así que antes de <code>rm *</code> ejecuta <code>ls *</code> y mira a quién le va a tocar 🖤" },
        ] },
        { title: "Variables y alias", blocks: [
          { p: "La shell tiene <b>variables de entorno</b>. Todos los programas lanzados desde ella las ven:" },
          { table: { head: ["Variable", "Qué guarda"], rows: [
            ["<code>$HOME</code>", "Tu carpeta personal"], ["<code>$USER</code>", "Tu nombre de usuario"],
            ["<code>$PATH</code>", "Dónde buscar comandos (carpetas separadas por dos puntos)"], ["<code>$EDITOR</code>", "Editor predeterminado"],
          ] } },
          { cmd: "echo $PATH" },
          { p: "Un <b>alias</b> es un nombre corto para un comando largo. Para que dure siempre, añádelo a <code>~/.bashrc</code>:" },
          { cmd: "echo \"alias update='sudo pacman -Syu'\" >> ~/.bashrc && source ~/.bashrc", note: "source vuelve a leer el archivo sin reiniciar la terminal." },
          { tip: "Guarda tus scripts en <code>~/.local/bin</code>: en FurrOS esa carpeta ya está en $PATH, así que se ejecutan por su nombre desde cualquier sitio." },
        ] },
      ],
      quiz: [
        { q: "¿Qué hace cd - ?", a: ["Vuelve a la carpeta anterior", "Borra la carpeta", "Va a la raíz"], ok: 0 },
        { q: "¿Qué abarca el comodín *.txt?", a: ["Todos los archivos que terminan en .txt", "Solo un archivo llamado *.txt", "Todos los archivos ocultos"], ok: 0 },
        { q: "¿Qué variable guarda las carpetas donde bash busca comandos?", a: ["$HOME", "$PATH", "$USER"], ok: 1 },
      ],
    },
    {
      id: "p-pipes", mood: "wave", badge: "⚡ Fontanera", title: "Redirecciones y tuberías",
      intro: "Encadenamos comandos: >, >>, 2>, | y los filtros grep, sort, wc.",
      lessons: [
        { title: "Adónde va la salida", blocks: [
          { p: "Todo comando tiene tres flujos: entrada (stdin), salida (stdout) y errores (stderr). Se pueden redirigir:" },
          { table: { head: ["Sintaxis", "Qué hace"], rows: [
            ["<code>comando > archivo</code>", "Escribir la salida en un archivo (se borra lo anterior)"],
            ["<code>comando >> archivo</code>", "Añadir al final del archivo"],
            ["<code>comando 2> archivo</code>", "Escribir solo los errores"],
            ["<code>comando &> archivo</code>", "Salida y errores juntos"],
            ["<code>comando > /dev/null</code>", "Tirar la salida (un «agujero negro»)"],
            ["<code>comando &lt; archivo</code>", "Tomar la entrada de un archivo"],
          ] } },
          { cmd: "pacman -Qe > ~/my-packages.txt", note: "La lista de paquetes instalados a propósito, en un archivo. Útil al reinstalar." },
        ] },
        { title: "La tubería |", blocks: [
          { p: "La barra <code>|</code> pasa la salida de un comando a la entrada del siguiente. Así se montan comandos grandes con piezas pequeñas:" },
          { table: { head: ["Filtro", "Qué hace"], rows: [
            ["<code>grep palabra</code>", "Quedarse con las líneas que la contienen (<code>-i</code> sin mayúsculas, <code>-v</code> al revés)"],
            ["<code>sort</code>", "Ordenar (<code>-n</code> por números, <code>-r</code> al revés)"],
            ["<code>uniq -c</code>", "Juntar líneas vecinas iguales y contarlas"],
            ["<code>wc -l</code>", "Contar líneas"],
            ["<code>head -n 5</code> / <code>tail -n 5</code>", "Primeras / últimas líneas"],
            ["<code>less</code>", "Pasar páginas de una salida larga (salir: q, buscar: /)"],
          ] } },
          { cmd: "pacman -Q | wc -l", note: "Cuántos paquetes hay instalados." },
          { cmd: "pacman -Q | grep -i nvidia", note: "Qué paquetes de NVIDIA hay instalados." },
          { cmd: "du -sh ~/* 2>/dev/null | sort -h | tail -n 5", note: "Las cinco carpetas más pesadas de tu carpeta personal." },
          { say: "Las tuberías son el superpoder de Linux. Cada comando hace una cosa, pero bien, y la barra los une en lo que quieras. Como Lego, pero para mayores 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿En qué se diferencia > de >>?", a: ["> sobrescribe el archivo, >> añade al final", "En nada", ">> borra el archivo"], ok: 0 },
        { q: "¿Qué recibe el comando a la derecha de | ?", a: ["La salida del de la izquierda como entrada", "Se ejecuta aparte y de forma independiente", "Cancela el de la izquierda"], ok: 0 },
        { q: "¿Cómo tiras los errores de un comando?", a: ["2>/dev/null", "| grep", ">> errors"], ok: 0 },
      ],
    },
    {
      id: "p-find", mood: "hoodie", badge: "⚡ Sabueso", title: "Encontrarlo todo",
      intro: "find, grep -r, plocate, which: encontrar un archivo, un texto o un programa.",
      lessons: [
        { title: "Encontrar un archivo", blocks: [
          { cmd: "find ~ -name \"*.pdf\"", note: "Todos los PDF de tu carpeta personal. -iname no distingue mayúsculas." },
          { cmd: "find ~/Downloads -type f -size +500M", note: "Archivos de más de 500 MB en Descargas." },
          { cmd: "find ~ -type f -mtime -1", note: "Archivos modificados en las últimas 24 horas." },
          { p: "find recorre de verdad todas las carpetas, así que puede ser lento. Es más rápido buscar en una base ya hecha: <b>plocate</b>." },
          { cmd: "sudo pacman -S plocate && sudo updatedb", note: "Instálalo y crea la base. Después se actualiza sola una vez al día." },
          { cmd: "locate hyprland.lua" },
        ] },
        { title: "Encontrar texto y programas", blocks: [
          { cmd: "grep -rn \"monitor\" ~/.config/hypr/", note: "En todos los archivos de la carpeta: -r recursivo, -n con número de línea." },
          { cmd: "which firefox", note: "Dónde está el programa que lanza un comando." },
          { cmd: "pacman -F libGL.so.1", note: "Qué paquete contiene un archivo, aunque no esté instalado. sudo pacman -Fy actualiza la base de archivos." },
          { say: "El error «error while loading shared libraries: libalgo.so» se arregla justo así: pacman -F encuentra el paquete que hay que instalar 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Cómo encuentras todos los .jpg de tu carpeta personal?", a: ["find ~ -name \"*.jpg\"", "grep jpg ~", "ls -jpg"], ok: 0 },
        { q: "¿Qué es lo más rápido para encontrar un archivo por nombre en todo el sistema?", a: ["locate (plocate)", "cat", "wc"], ok: 0 },
        { q: "¿Cómo sabes en qué paquete está libGL.so.1?", a: ["pacman -F libGL.so.1", "which libGL.so.1", "pacman -Syu"], ok: 0 },
      ],
    },
    {
      id: "p-text", mood: "hoodie", badge: "⚡ Editora", title: "Editores y texto",
      intro: "nano como una pro, sobrevivir a vim, diff y cambios rápidos con sed.",
      lessons: [
        { title: "nano y vim", blocks: [
          { p: "<b>nano</b>: pistas abajo, <code>^</code> significa Ctrl. Útil: <kbd>Ctrl</kbd>+<kbd>W</kbd> buscar, <kbd>Ctrl</kbd>+<kbd>K</kbd> cortar línea, <kbd>Ctrl</kbd>+<kbd>U</kbd> pegar, <kbd>Alt</kbd>+<kbd>U</kbd> deshacer, <kbd>Ctrl</kbd>+<kbd>O</kbd> guardar, <kbd>Ctrl</kbd>+<kbd>X</kbd> salir." },
          { p: "Tarde o temprano <b>vim</b> se abrirá solo (en git, por ejemplo). Para sobrevivir bastan cinco cosas:" },
          { table: { head: ["Teclas", "Qué hace"], rows: [
            ["<kbd>i</kbd>", "Modo inserción: ya puedes escribir"], ["<kbd>Esc</kbd>", "Volver al modo de órdenes"],
            ["<code>:w</code> + Enter", "Guardar"], ["<code>:q!</code> + Enter", "Salir sin guardar"], ["<code>:wq</code> + Enter", "Guardar y salir"],
          ] } },
          { cmd: "export EDITOR=nano", note: "Para que los programas abran nano en vez de vim. Añádelo a ~/.bashrc para que sea permanente." },
        ] },
        { title: "Comparar y reemplazar", blocks: [
          { cmd: "diff -u old.conf new.conf", note: "En qué se diferencian dos archivos: - quitado, + añadido." },
          { cmd: "sed -i 's/viejo/nuevo/g' archivo.txt", noRun: true, note: "Reemplazar en todo el archivo. Sin -i solo muestra el resultado y no toca el archivo." },
          { warn: "sed -i cambia el archivo al momento. Antes de tocar configuraciones del sistema, haz una copia: <code>sudo cp archivo archivo.bak</code>." },
          { say: "Truco de Velvet: <code>sed</code> sin <code>-i</code> es una vista previa. Primero miro, luego añado -i. Ni una configuración rota, miau 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Cómo sales de vim sin guardar?", a: [":q! y Enter", "Ctrl+C", "Alt+F4"], ok: 0 },
        { q: "¿Qué muestra diff -u a b?", a: ["Las diferencias entre los archivos", "El tamaño de los archivos", "Borra b"], ok: 0 },
        { q: "¿Qué hace la opción -i de sed?", a: ["Edita el archivo en el sitio", "Busca sin distinguir mayúsculas", "Muestra la ayuda"], ok: 0 },
      ],
    },
    {
      id: "p-proc", mood: "timer", badge: "⚡ Domadora de procesos", title: "Procesos",
      intro: "Qué se está ejecutando, cómo pararlo y cómo lanzar cosas en segundo plano.",
      lessons: [
        { title: "Ver y parar", blocks: [
          { p: "Cada programa en marcha es un <b>proceso</b> con su propio número (PID)." },
          { cmd: "htop", note: "Lista de procesos en vivo: F6 ordenar, F9 matar, q salir. Si no está: sudo pacman -S htop" },
          { cmd: "ps aux | grep firefox", note: "Encontrar un proceso y su PID." },
          { table: { head: ["Comando", "Qué hace"], rows: [
            ["<code>kill PID</code>", "Pedirle con educación que termine (señal TERM)"],
            ["<code>kill -9 PID</code>", "Matarlo sin preguntar (KILL), si está colgado del todo"],
            ["<code>pkill firefox</code>", "Terminar por nombre"],
            ["<code>xkill</code> / <code>kill</code> en KRunner", "Hacer clic en la ventana colgada (X11 y KDE)"],
          ] } },
          { say: "Primero kill normal, y solo si el proceso no responde, -9. Kill -9 no deja guardar al programa, así que puedes perder trabajo sin guardar 🖤" },
        ] },
        { title: "Segundo plano y primer plano", blocks: [
          { ul: [
            "<code>comando &</code> — lánzalo en segundo plano y sigue usando la terminal.",
            "<kbd>Ctrl</kbd>+<kbd>Z</kbd> — pausar el comando actual.",
            "<code>jobs</code> — lista de tareas en segundo plano, <code>bg</code> — seguir en segundo plano, <code>fg</code> — traerla al frente.",
            "<code>nohup comando &</code> — sobrevive aunque cierres la terminal.",
          ] },
          { cmd: "free -h", note: "Cuánta memoria está ocupada. La columna available es lo realmente libre." },
          { cmd: "uptime", note: "Cuánto tiempo lleva encendido el ordenador y la carga media." },
        ] },
      ],
      quiz: [
        { q: "¿Qué es un PID?", a: ["El número de un proceso", "La contraseña de administrador", "Un tipo de archivo"], ok: 0 },
        { q: "¿Cuándo usar kill -9?", a: ["Cuando un proceso está colgado e ignora un kill normal", "Siempre, en vez de kill", "Para reiniciar el PC"], ok: 0 },
        { q: "¿Qué hace Ctrl+Z en la terminal?", a: ["Pausa el comando", "Deshace la última acción", "Cierra la terminal"], ok: 0 },
      ],
    },
    {
      id: "p-systemd", mood: "timer", badge: "⚡ Jefa de servicios", title: "Servicios de systemd",
      intro: "systemctl, arranque automático, el registro de un servicio y los temporizadores.",
      lessons: [
        { title: "systemctl", blocks: [
          { p: "<b>systemd</b> arranca el sistema y cuida de los <b>servicios</b>: la red, el sonido, el Bluetooth, la pantalla de inicio de sesión. Se manejan con <code>systemctl</code>:" },
          { table: { head: ["Comando", "Qué hace"], rows: [
            ["<code>systemctl status nombre</code>", "Si el servicio funciona y las últimas líneas de su registro"],
            ["<code>sudo systemctl start / stop nombre</code>", "Arrancar / parar ahora"],
            ["<code>sudo systemctl restart nombre</code>", "Reiniciarlo"],
            ["<code>sudo systemctl enable nombre</code>", "Arrancarlo al encender (<code>--now</code> — y también ahora)"],
            ["<code>sudo systemctl disable nombre</code>", "Quitarlo del arranque automático"],
            ["<code>systemctl list-units --type=service</code>", "Todos los servicios en marcha"],
          ] } },
          { cmd: "sudo systemctl enable --now bluetooth" },
          { p: "También hay servicios de <b>usuario</b>, que funcionan a tu nombre: <code>systemctl --user status pipewire</code>." },
        ] },
        { title: "Registros y temporizadores", blocks: [
          { cmd: "journalctl -u NetworkManager -b", note: "El registro de un servicio desde este arranque." },
          { cmd: "journalctl -f", note: "Ver el registro en vivo (salir: Ctrl+C)." },
          { p: "Los <b>temporizadores</b> de systemd sustituyen a cron: arrancan servicios según un horario. FurrOS los usa, por ejemplo, para limpiar la caché de pacman:" },
          { cmd: "systemctl list-timers" },
          { say: "Si algo «no arranca solo tras reiniciar», casi siempre alguien olvidó el <code>enable</code>. start es para ahora, enable para siempre 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Cómo activas un servicio al arrancar y lo inicias ya?", a: ["sudo systemctl enable --now nombre", "sudo systemctl start nombre", "systemctl status nombre"], ok: 0 },
        { q: "¿Cómo ves el registro de un solo servicio?", a: ["journalctl -u nombre", "cat nombre", "pacman -Qi nombre"], ok: 0 },
        { q: "¿Qué son los temporizadores de systemd?", a: ["Arrancar servicios según un horario", "El reloj del panel", "Un cronómetro en la terminal"], ok: 0 },
      ],
    },
    {
      id: "p-disks", mood: "hoodie", badge: "⚡ Guardiana de discos", title: "Discos y espacio",
      intro: "lsblk, df, du, montaje, UUID y /etc/fstab.",
      lessons: [
        { title: "Qué discos hay y dónde está el espacio", blocks: [
          { cmd: "lsblk -f", note: "Todos los discos y particiones: sistema de archivos, etiqueta, UUID, dónde están montados." },
          { cmd: "df -h", note: "Espacio libre en cada partición." },
          { cmd: "du -sh ~/.cache", note: "Cuánto pesa una carpeta." },
          { cmd: "sudo pacman -S ncdu && ncdu ~", note: "Interactivo: recorres las carpetas con las flechas y ves qué se comió el espacio." },
          { warn: "En Btrfs, <code>df</code> a veces miente por las instantáneas y la compresión. La imagen exacta: <code>sudo btrfs filesystem usage /</code>." },
        ] },
        { title: "Montar un disco para siempre", blocks: [
          { p: "Los USB se montan solos. Un segundo disco interno se puede montar en cada arranque: se añade a <code>/etc/fstab</code> por su <b>UUID</b> (los nombres tipo sdb pueden cambiar, el UUID nunca)." },
          { cmd: "sudo mkdir -p /mnt/data && sudo mount /dev/sdb1 /mnt/data", noRun: true, note: "Montarlo a mano una vez. Desmontar: sudo umount /mnt/data" },
          { p: "La línea para fstab (toma el UUID de <code>lsblk -f</code>):" },
          { cmd: "UUID=xxxx-xxxx  /mnt/data  ext4  defaults,nofail  0 2", noRun: true, note: "nofail — el sistema arranca aunque falte el disco." },
          { cmd: "sudo mount -a", note: "Probar fstab sin reiniciar: si no hay errores, todo se monta." },
          { say: "Un error en fstab puede impedir que el sistema arranque. Por eso siempre <code>nofail</code> en los discos extra, y siempre <code>sudo mount -a</code> antes de reiniciar 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Qué comando muestra el espacio libre de las particiones?", a: ["df -h", "ls -l", "free -h"], ok: 0 },
        { q: "¿Por qué usar el UUID en fstab en vez de /dev/sdb1?", a: ["Los nombres sdX pueden cambiar, el UUID no", "El UUID es más corto", "Es más rápido"], ok: 0 },
        { q: "¿Qué hace la opción nofail?", a: ["El sistema arranca aunque falte el disco", "El disco nunca se romperá", "Desactiva la comprobación del disco para siempre"], ok: 0 },
      ],
    },
    {
      id: "p-users", mood: "grr", badge: "⚡ Portera", title: "Usuarios, grupos y permisos",
      intro: "Usuarios nuevos, grupos, chmod con números y chown.",
      lessons: [
        { title: "Usuarios y grupos", blocks: [
          { cmd: "sudo useradd -m -G wheel -s /bin/bash sister && sudo passwd sister", noRun: true, note: "Un usuario nuevo con carpeta personal y permiso de sudo (grupo wheel)." },
          { cmd: "groups", note: "A qué grupos perteneces." },
          { cmd: "sudo usermod -aG docker $USER", noRun: true, note: "Añadirte a un grupo. ¡-a es obligatorio, o te sacará de los demás grupos! Se aplica al volver a iniciar sesión." },
          { p: "Los grupos dan acceso a dispositivos y funciones: <code>wheel</code> — sudo, <code>libvirt</code> — máquinas virtuales, <code>docker</code> — Docker." },
        ] },
        { title: "chmod con números, y chown", blocks: [
          { p: "Los permisos se pueden escribir con números: r=4, w=2, x=1, sumados para el dueño, el grupo y los demás." },
          { table: { head: ["Número", "Permisos", "Para qué"], rows: [
            ["<code>755</code>", "rwxr-xr-x", "Scripts y carpetas"], ["<code>644</code>", "rw-r--r--", "Archivos normales"],
            ["<code>600</code>", "rw-------", "Secretos: claves SSH, contraseñas"], ["<code>700</code>", "rwx------", "Una carpeta privada"],
          ] } },
          { cmd: "chmod 600 ~/.ssh/id_ed25519" },
          { cmd: "sudo chown -R $USER:$USER ~/Games", note: "Recuperar una carpeta que creaste sin querer con sudo." },
          { say: "Un clásico: creaste archivos con sudo y ahora te sale «Permission denied» en tu propia carpeta. Un chown lo arregla. No hagas chmod 777, es como dejar la puerta abierta de par en par 😤" },
        ] },
      ],
      quiz: [
        { q: "¿Qué significan los permisos 644?", a: ["El dueño lee y escribe, los demás solo leen", "Todos pueden todo", "Nadie puede nada"], ok: 0 },
        { q: "¿Por qué usermod necesita -a junto a -G?", a: ["Sin -a te sacan de tus otros grupos", "Hace el comando más rápido", "Sin -a se borra el usuario"], ok: 0 },
        { q: "¿Qué grupo da permiso de sudo en Arch y FurrOS?", a: ["wheel", "users", "audio"], ok: 0 },
      ],
    },
    {
      id: "p-net", mood: "wave", badge: "⚡ Redera", title: "La red más a fondo",
      intro: "Direcciones IP, ping, quién escucha en cada puerto, curl y descargas.",
      lessons: [
        { title: "Diagnóstico", blocks: [
          { cmd: "ip -br a", note: "Las interfaces de red y sus direcciones IP, en resumen." },
          { cmd: "ping -c 4 archlinux.org", note: "¿Hay conexión? Si una IP responde (ping 1.1.1.1) pero un nombre no, el problema es el DNS." },
          { cmd: "ip route", note: "Por qué router sale internet (la línea default)." },
          { cmd: "sudo ss -tulpn", note: "Qué programas escuchan en puertos de tu ordenador." },
          { cmd: "resolvectl status", note: "Qué servidores DNS se usan." },
        ] },
        { title: "Descargar desde la terminal", blocks: [
          { cmd: "curl -LO https://example.com/file.iso", noRun: true, note: "-L sigue las redirecciones, -O guarda con el nombre original." },
          { cmd: "curl -s ifconfig.me", note: "Tu dirección IP pública." },
          { cmd: "sha256sum file.iso", noRun: true, note: "La suma de comprobación: compárala con la de la web. Si coincide, el archivo está entero." },
          { say: "¿Descargaste una ISO? Comprueba la suma. Son diez segundos y te ahorran una hora peleando con una imagen rota 🖤" },
        ] },
      ],
      quiz: [
        { q: "ping 1.1.1.1 funciona pero ping archlinux.org no. ¿Qué falla?", a: ["El DNS", "Se quemó la tarjeta de red", "Hay que reinstalar el sistema"], ok: 0 },
        { q: "¿Cómo ves qué programas escuchan en puertos?", a: ["sudo ss -tulpn", "ls /ports", "pacman -Q"], ok: 0 },
        { q: "¿Para qué sha256sum tras una descarga?", a: ["Para comprobar que el archivo no está roto ni alterado", "Para acelerar la descarga", "Para descomprimirlo"], ok: 0 },
      ],
    },
    {
      id: "p-ssh", mood: "hoodie", badge: "⚡ Teletransporte", title: "SSH: otros ordenadores",
      intro: "Conectarse a un servidor, claves en vez de contraseñas y copiar archivos.",
      lessons: [
        { title: "Conexión y claves", blocks: [
          { p: "<b>SSH</b> es una terminal segura en otro ordenador: un servidor, una Raspberry Pi, tu segundo PC." },
          { cmd: "ssh user@192.168.1.50", noRun: true },
          { p: "Escribir la contraseña cada vez es pesado y menos seguro. Crea un par de claves: la privada se queda contigo y la pública va al servidor." },
          { cmd: "ssh-keygen -t ed25519", note: "Puedes pulsar Enter en las preguntas. Una frase de paso para la clave es buena idea." },
          { cmd: "ssh-copy-id user@192.168.1.50", noRun: true, note: "Enviar la clave pública al servidor. A partir de ahí, sin contraseña." },
          { warn: "El archivo <code>~/.ssh/id_ed25519</code> sin .pub es tu clave privada. No se la envíes a nadie, igual que una contraseña." },
        ] },
        { title: "Archivos y comodidad", blocks: [
          { cmd: "scp photo.png user@192.168.1.50:~/", noRun: true, note: "Copiar un archivo al servidor." },
          { cmd: "rsync -avP ~/Music/ user@192.168.1.50:~/Music/", noRun: true, note: "Sincronizar una carpeta: la próxima vez solo se envían los cambios." },
          { p: "Para no escribir direcciones, crea <code>~/.ssh/config</code>:" },
          { cmd: "Host pi\n    HostName 192.168.1.50\n    User furry", noRun: true, note: "Ahora basta con ssh pi." },
          { say: "Para que otros se conecten a ti hace falta un servidor: <code>sudo pacman -S openssh && sudo systemctl enable --now sshd</code> y el puerto 22 en el cortafuegos. No lo actives si no lo necesitas — menos puertas, menos problemas 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Qué clave puedes darle al servidor?", a: ["La pública (.pub)", "La privada (sin .pub)", "Las dos"], ok: 0 },
        { q: "¿Con qué copias un archivo a otro ordenador por SSH?", a: ["scp", "cp", "mv"], ok: 0 },
        { q: "¿Para qué sirve ~/.ssh/config?", a: ["Nombres cortos y ajustes para servidores", "Guardar contraseñas en texto plano", "Activar el servidor SSH"], ok: 0 },
      ],
    },
    {
      id: "p-pacman", mood: "timer", badge: "⚡ Reina de pacman", title: "pacman para mayores",
      intro: "Detalles de paquetes, volver a una versión anterior, IgnorePkg y .pacnew.",
      lessons: [
        { title: "Saberlo todo de los paquetes", blocks: [
          { table: { head: ["Comando", "Qué hace"], rows: [
            ["<code>pacman -Qi nombre</code>", "Detalles de un paquete instalado (versión, tamaño, dependencias)"],
            ["<code>pacman -Ql nombre</code>", "Qué archivos instaló el paquete"],
            ["<code>pacman -Qe</code>", "Lo que instalaste tú, sin dependencias"],
            ["<code>pacman -Qdt</code>", "Huérfanos: dependencias que ya nadie necesita"],
            ["<code>pactree nombre</code>", "Árbol de dependencias (paquete pacman-contrib)"],
            ["<code>expac -H M '%m\\t%n' | sort -h | tail</code>", "Los paquetes más pesados (paquete expac)"],
          ] } },
        ] },
        { title: "Volver atrás y congelar", blocks: [
          { p: "¿La nueva versión de un programa falla? La anterior está en la caché y puedes volver a instalarla:" },
          { cmd: "ls /var/cache/pacman/pkg/ | grep firefox" },
          { cmd: "sudo pacman -U /var/cache/pacman/pkg/firefox-VERSIÓN-x86_64.pkg.tar.zst", noRun: true },
          { p: "Para que pacman no actualice ese paquete de momento, añádelo en <code>/etc/pacman.conf</code> con la línea <code>IgnorePkg = firefox</code>. Acuérdate de quitarlo luego: mantener versiones viejas mucho tiempo en Arch es arriesgado." },
          { cmd: "sudo pacdiff", note: "Ordenar los archivos .pacnew: comparar la nueva configuración de ejemplo con la tuya y decidir qué quedarte." },
          { say: "Volver atrás es una tirita, no una cura. Vuelvo atrás, informo del fallo y en un par de días actualizo. Así lo hacen los pros 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Cómo ves los archivos que instaló un paquete?", a: ["pacman -Ql nombre", "pacman -Ss nombre", "pacman -R nombre"], ok: 0 },
        { q: "¿Dónde están las versiones viejas de los paquetes para volver atrás?", a: ["/var/cache/pacman/pkg", "/tmp", "~/Downloads"], ok: 0 },
        { q: "¿Qué hace pacdiff?", a: ["Ayuda a ordenar los archivos .pacnew", "Desinstala pacman", "Compara dos sistemas"], ok: 0 },
      ],
    },
    {
      id: "p-aur", mood: "grr", badge: "⚡ Constructora", title: "El AUR a mano",
      intro: "Qué hay dentro de un PKGBUILD, makepkg y cómo no pillar un paquete malo.",
      lessons: [
        { title: "Compilar sin ayudante", blocks: [
          { p: "yay lo hace por ti, pero conviene saber qué pasa. Un paquete del AUR no es un programa, es una <b>receta</b>: un archivo PKGBUILD con el que el programa se construye en tu equipo." },
          { cmd: "sudo pacman -S --needed base-devel git" },
          { cmd: "git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin" },
          { cmd: "less PKGBUILD", note: "¡Primero se lee la receta! Mira source (de dónde descarga) y los comandos de package()." },
          { cmd: "makepkg -si", note: "Compilar e instalar (con dependencias). Nunca ejecutes makepkg con sudo." },
        ] },
        { title: "Cómo no caer", blocks: [
          { ul: [
            "Mira los votos y la popularidad en aur.archlinux.org.",
            "Revisa la fecha de la última actualización y los comentarios: ahí se avisa de los problemas.",
            "En un PKGBUILD es sospechoso todo lo que descarga de webs raras o hace <code>curl … | sh</code>.",
            "Al actualizar, yay muestra un diff de la receta. Léelo, sobre todo en paquetes poco conocidos.",
          ] },
          { cmd: "yay -Sua", note: "Actualizar solo los paquetes del AUR." },
          { say: "El AUR es un mercado: hay cosas geniales y cosas turbias. ¿Un paquete con cinco votos y una receta que baja algo de una web de descargas? Paso 😤" },
        ] },
      ],
      quiz: [
        { q: "¿Qué es un PKGBUILD?", a: ["Una receta para construir un paquete", "Un programa ya hecho", "Los registros de pacman"], ok: 0 },
        { q: "¿Se puede ejecutar makepkg con sudo?", a: ["No, makepkg se ejecuta como usuario normal", "Sí, así se hace", "Solo los viernes"], ok: 0 },
        { q: "¿Qué es sospechoso en un PKGBUILD?", a: ["Descargas de webs raras y curl | sh", "Los comentarios", "El campo pkgver"], ok: 0 },
      ],
    },
    {
      id: "p-archive", mood: "hoodie", badge: "⚡ Empaquetadora", title: "Archivos comprimidos",
      intro: "tar, zip, zstd y 7z: empaquetar, desempaquetar, mirar dentro.",
      lessons: [
        { title: "tar y sus amigos", blocks: [
          { p: "<b>tar</b> junta muchos archivos en uno, y gzip, xz o zstd lo comprimen. Recuerda las letras: <b>c</b> crear, <b>x</b> extraer, <b>t</b> listar, <b>f</b> archivo, <b>v</b> detallado." },
          { cmd: "tar -czf backup.tar.gz ~/Documents", note: "Empaquetar con gzip." },
          { cmd: "tar --zstd -cf backup.tar.zst ~/Documents", note: "zstd: más rápido y suele comprimir mejor. Los paquetes de Arch también usan zstd." },
          { cmd: "tar -xf backup.tar.gz -C ~/restore", note: "Extraer en una carpeta (tar detecta solo la compresión)." },
          { cmd: "tar -tf backup.tar.gz | head", note: "Ver qué hay dentro sin extraerlo." },
        ] },
        { title: "zip, 7z y rar", blocks: [
          { cmd: "zip -r photos.zip ~/Pictures", note: "Cualquier sistema entiende zip: ideal para amigos con Windows." },
          { cmd: "unzip photos.zip -d photos" },
          { cmd: "sudo pacman -S 7zip && 7z x archive.7z", note: "7z extrae casi todo, también .rar." },
          { say: "Los gestores de archivos también saben: clic derecho → «Comprimir» o «Extraer». La terminal es para cuando hay mucho y con prisa 🖤" },
        ] },
      ],
      quiz: [
        { q: "¿Qué letra de tar significa «extraer»?", a: ["x", "c", "z"], ok: 0 },
        { q: "¿Cómo ves el contenido de un archivo comprimido sin extraerlo?", a: ["tar -tf archivo", "tar -xf archivo", "cat archivo"], ok: 0 },
        { q: "¿Qué formato es más cómodo para enviar a un amigo con Windows?", a: ["zip", "tar.zst", "pkg.tar.zst"], ok: 0 },
      ],
    },
    {
      id: "p-script", mood: "wave", badge: "⚡ Scriptera", title: "Tus propios scripts",
      intro: "shebang, variables, condiciones, bucles, argumentos y la graduación de Velvet.",
      lessons: [
        { title: "Tu primer script", blocks: [
          { p: "Un script es un archivo de texto con comandos. La primera línea (el <b>shebang</b>) dice con qué se ejecuta:" },
          { cmd: "#!/bin/bash\nset -euo pipefail\nname=${1:-amigo}\necho \"¡Hola, $name! Hoy es $(date +%A)\"", noRun: true, note: "set -euo pipefail: parar en el primer error. $1 es el primer argumento, :-amigo un valor por defecto. $(…) inserta la salida de un comando." },
          { cmd: "nano ~/.local/bin/hello && chmod +x ~/.local/bin/hello", note: "Crear el script y hacerlo ejecutable. Luego basta con: hello Velvet" },
        ] },
        { title: "Condiciones y bucles", blocks: [
          { cmd: "if [ -f ~/.bashrc ]; then\n  echo \"bashrc existe\"\nelse\n  echo \"no hay bashrc\"\nfi", noRun: true, note: "-f existe el archivo, -d carpeta, -z texto vacío. ¡Los espacios dentro de [ ] son obligatorios!" },
          { cmd: "for f in ~/Pictures/*.png; do\n  echo \"Encontré: $f\"\ndone", noRun: true },
          { p: "Un ejemplo real: renombrar todas las capturas añadiendo la fecha:" },
          { cmd: "for f in Screenshot*.png; do mv -- \"$f\" \"$(date +%F)-$f\"; done", noRun: true },
          { tip: "Revisa tus scripts con <b>shellcheck</b> (<code>sudo pacman -S shellcheck</code>): encuentra errores que, si no, saldrían en el peor momento." },
          { say: "¡Listo, has terminado mi nivel! Encadenas comandos, gestionas servicios, saltas por SSH y escribes scripts. Ahora te espera Danyok, y creo que tiene un limón 🍋🖤", mood: "lying" },
        ] },
      ],
      quiz: [
        { q: "¿Qué es el shebang?", a: ["La primera línea #! que dice con qué ejecutar el script", "Un error de bash", "Un comentario al final"], ok: 0 },
        { q: "¿Qué guarda $1?", a: ["El primer argumento del script", "El precio del script", "El número de línea"], ok: 0 },
        { q: "¿Qué hace set -e?", a: ["Para el script en el primer error", "Activa los emoji", "Borra las variables"], ok: 0 },
      ],
    },
  ] },

  danyok: { chapters: [
    {
      id: "d-boot", mood: "wave", badge: "🍋 Gestor de arranque", title: "Cómo arranca Linux",
      intro: "UEFI, el menú de arranque FurrBoot, el kernel, initramfs y systemd: qué pasa después del botón de encendido.",
      lessons: [
        { title: "La cadena de arranque", blocks: [
          { ol: [
            "<b>UEFI</b> (el firmware de la placa) encuentra la partición EFI y lanza desde ella el gestor de arranque.",
            "<b>FurrBoot</b> muestra el menú de FurrOS y carga en memoria el <b>kernel</b> (vmlinuz) y el <b>initramfs</b>. Los PC antiguos sin UEFI usan Limine en su lugar, y el GRUB de reserva siempre está en el menú de arranque de la placa (F11/F12/F8).",
            "El <b>initramfs</b> es un sistema diminuto y temporal: lleva los controladores para encontrar y montar la partición raíz de verdad (Btrfs, cifrado, NVMe).",
            "El kernel lanza <b>systemd</b> (PID 1), y systemd arranca todos los servicios y la pantalla de inicio de sesión.",
          ] },
          { cmd: "systemd-analyze", note: "Cuánto tardó cada fase del arranque." },
          { cmd: "systemd-analyze blame | head", note: "Qué servicios tardan más en arrancar." },
        ] },
        { title: "Parámetros del kernel e initramfs", blocks: [
          { p: "Los parámetros del kernel están en <code>/etc/kernel/cmdline</code>. Tras editarlo, actualiza el menú de arranque:" },
          { cmd: "sudo furrboot-update" },
          { p: "El GRUB de reserva tiene sus propios ajustes: <code>/etc/default/grub</code>, luego <code>sudo grub-mkconfig -o /boot/grub/grub.cfg</code>." },
          { cmd: "cat /proc/cmdline", note: "Con qué parámetros arrancó el kernel ahora." },
          { p: "Lo que lleva el initramfs se define en <code>/etc/mkinitcpio.conf</code> (líneas MODULES y HOOKS). Tras editarlo, regenéralo:" },
          { cmd: "sudo mkinitcpio -P" },
          { say: "Pulsa una vez <kbd>E</kbd> en el menú de FurrBoot: verás la línea de arranque y podrás añadir un parámetro solo para esta vez. Te salva cuando el sistema no arranca con ajustes nuevos. Y si un kernel nuevo falla tres veces seguidas, FurrBoot arranca solo el de reserva. El limón lo aprueba 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Qué es el initramfs?", a: ["Un sistema diminuto y temporal que monta la raíz de verdad", "Un archivo de intercambio", "El menú de arranque"], ok: 0 },
        { q: "¿Qué se lanza como primer proceso (PID 1)?", a: ["systemd", "GRUB", "bash"], ok: 0 },
        { q: "¿Qué haces tras editar /etc/kernel/cmdline?", a: ["sudo furrboot-update", "Nada", "sudo pacman -Syu"], ok: 0 },
      ],
    },
    {
      id: "d-kernel", mood: "hoodie", badge: "🍋 Kernelero", title: "El kernel y los módulos",
      intro: "Versiones del kernel, módulos, listas negras, DKMS y sysctl.",
      lessons: [
        { title: "Kernels y módulos", blocks: [
          { cmd: "uname -r", note: "La versión del kernel en uso." },
          { p: "Arch tiene varios kernels: <code>linux</code> (el más reciente), <code>linux-lts</code> (soporte largo, de repuesto), <code>linux-zen</code> (ajustado para respuesta rápida). FurrOS también tiene el suyo, <code>linux-furros</code>. Puedes tener dos: el menú de arranque se actualiza solo y el segundo aparece en «Otro kernel»." },
          { cmd: "sudo pacman -S linux-lts linux-lts-headers", noRun: true, note: "Un kernel de repuesto: si el nuevo rompe algo, arrancas con el LTS." },
          { cmd: "lsmod | head", note: "Módulos (controladores) cargados." },
          { cmd: "modinfo btusb", note: "Qué es un módulo y qué parámetros acepta." },
        ] },
        { title: "Listas negras, DKMS, sysctl", blocks: [
          { p: "¿Un módulo molesta (un controlador de webcam con fallos, por ejemplo)? Bloquéalo:" },
          { cmd: "echo 'blacklist uvcvideo' | sudo tee /etc/modprobe.d/no-webcam.conf", noRun: true },
          { p: "<b>DKMS</b> recompila los módulos de terceros (nvidia-580xx, por ejemplo) para cada kernel nuevo. Para eso hacen falta las cabeceras: <code>linux-headers</code> de cada kernel instalado." },
          { cmd: "dkms status" },
          { p: "<b>sysctl</b> cambia parámetros del kernel en caliente. Los permanentes van en <code>/etc/sysctl.d/*.conf</code>:" },
          { cmd: "sysctl vm.swappiness" },
          { say: "Un consejo que vale un millón de limones: ten <code>linux-lts</code> como kernel de repuesto. Ocupa casi nada y un mal día te salva el sistema entero 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Para qué tener linux-lts junto a linux?", a: ["Un kernel de repuesto si el nuevo rompe algo", "Para que los juegos vayan más rápido", "El Wi-Fi lo exige"], ok: 0 },
        { q: "¿Qué hace DKMS?", a: ["Recompila módulos de terceros para el kernel nuevo", "Borra kernels viejos", "Actualiza la BIOS"], ok: 0 },
        { q: "¿Dónde van los ajustes permanentes de sysctl?", a: ["/etc/sysctl.d/*.conf", "~/.bashrc", "/boot/grub"], ok: 0 },
      ],
    },
    {
      id: "d-btrfs", mood: "timer", badge: "🍋 Maestro de Btrfs", title: "Btrfs en serio",
      intro: "Subvolúmenes, instantáneas, compresión, scrub y cuánto espacio se usa de verdad.",
      lessons: [
        { title: "Subvolúmenes e instantáneas", blocks: [
          { p: "FurrOS sobre Btrfs crea <b>subvolúmenes</b>: <code>@</code> (el sistema), <code>@home</code>, <code>@log</code>, <code>@pkg</code>. La instantánea se hace por subvolumen, así que volver atrás el sistema no toca tus archivos de home." },
          { cmd: "sudo btrfs subvolume list /" },
          { cmd: "sudo snapper -c root list", note: "Instantáneas del sistema. Usan copia en escritura: casi no ocupan espacio mientras los archivos no cambien." },
          { cmd: "sudo snapper -c root create -d \"antes del experimento\"", note: "Una instantánea manual antes de cambios arriesgados." },
          { cmd: "sudo snapper -c root status 41..42", noRun: true, note: "Qué cambió entre dos instantáneas." },
        ] },
        { title: "Compresión y salud", blocks: [
          { p: "FurrOS monta Btrfs con compresión zstd: los archivos ocupan menos en disco y a menudo incluso se leen más rápido." },
          { cmd: "sudo pacman -S compsize && sudo compsize /usr", note: "Cuánto ahorra de verdad la compresión." },
          { cmd: "sudo btrfs filesystem usage /", note: "La imagen exacta del espacio (df miente en Btrfs)." },
          { cmd: "sudo btrfs scrub start / && sudo btrfs scrub status /", note: "Comprobar todos los datos con sus sumas. Conviene una vez al mes." },
          { warn: "<code>btrfs check --repair</code> es el último recurso, solo si te lo aconseja gente que sabe y con copia de seguridad. Puede empeorarlo todo." },
          { say: "Una instantánea no es una copia de seguridad. Está en el mismo disco. Si muere el disco, mueren con él. Las copias, en otro disco; los limones, en la nevera 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Por qué volver atrás el sistema no toca tus archivos de home?", a: ["home es un subvolumen aparte, @home", "Snapper no sabe volver atrás", "Los archivos de home son de solo lectura"], ok: 0 },
        { q: "¿Qué comprueba los datos de Btrfs con sus sumas?", a: ["btrfs scrub", "fsck.vfat", "rm -rf"], ok: 0 },
        { q: "¿Las instantáneas sustituyen a las copias de seguridad?", a: ["No, están en el mismo disco", "Sí, del todo", "Solo en SSD"], ok: 0 },
      ],
    },
    {
      id: "d-units", mood: "hoodie", badge: "🍋 De servicio", title: "Tus propios servicios y temporizadores",
      intro: "Escribir archivos unit, cambios drop-in y temporizadores en vez de cron.",
      lessons: [
        { title: "Tu propio servicio", blocks: [
          { p: "Un servicio se describe con un archivo <b>unit</b>. Los tuyos del sistema van en <code>/etc/systemd/system/</code>, los de usuario en <code>~/.config/systemd/user/</code>." },
          { cmd: "[Unit]\nDescription=Mi bot\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nExecStart=/home/furry/bot/run.sh\nRestart=on-failure\n\n[Install]\nWantedBy=default.target", noRun: true, note: "~/.config/systemd/user/bot.service — un bot que se reinicia si se cae." },
          { cmd: "systemctl --user daemon-reload && systemctl --user enable --now bot", noRun: true },
          { cmd: "loginctl enable-linger $USER", noRun: true, note: "Para que los servicios de usuario funcionen aunque no hayas iniciado sesión." },
        ] },
        { title: "Cambios y temporizadores", blocks: [
          { p: "Los archivos unit del sistema no se editan directamente (una actualización los sobrescribiría). Se usa un <b>drop-in</b>:" },
          { cmd: "sudo systemctl edit sddm", noRun: true, note: "Abre un editor para un archivo de anulación. Lo que escribas ahí sobrevive a las actualizaciones." },
          { p: "Un temporizador es un .timer y un .service con el mismo nombre:" },
          { cmd: "[Timer]\nOnCalendar=daily\nPersistent=true\n\n[Install]\nWantedBy=timers.target", noRun: true, note: "backup.timer: lanza backup.service una vez al día. Persistent — recupera una ejecución perdida si el PC estaba apagado." },
          { cmd: "systemd-analyze calendar \"Mon *-*-* 10:00\"", note: "Comprobar un horario: cuándo salta la próxima vez." },
          { say: "Los temporizadores le ganan a cron: todo se ve en <code>systemctl list-timers</code>, los registros están en journalctl y las ejecuciones perdidas se recuperan. Consejo ácido, pero cierto 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Dónde van tus servicios de usuario?", a: ["~/.config/systemd/user/", "/boot", "/tmp"], ok: 0 },
        { q: "¿Cuál es la forma correcta de cambiar un servicio del sistema?", a: ["sudo systemctl edit nombre (un drop-in)", "Editar el archivo de /usr/lib/systemd directamente", "No se puede"], ok: 0 },
        { q: "¿Qué hace Persistent=true en un temporizador?", a: ["Recupera una ejecución perdida", "Impide pararlo", "Lo lanza cada segundo"], ok: 0 },
      ],
    },
    {
      id: "d-net", mood: "wave", badge: "🍋 Admin de red", title: "La red por dentro",
      intro: "NetworkManager desde la terminal, DNS, /etc/hosts, reglas de ufw y una VPN que funciona incluso con bloqueos.",
      lessons: [
        { title: "Conexiones y DNS", blocks: [
          { cmd: "nmcli connection show" },
          { cmd: "nmcli connection modify \"Mi red\" ipv4.dns \"1.1.1.1 9.9.9.9\" ipv4.ignore-auto-dns yes", noRun: true, note: "Tu propio DNS para una red. Aplicar: nmcli connection up \"Mi red\"." },
          { p: "<code>/etc/hosts</code> es una «agenda» local: nombre → IP. Práctica para servidores de casa:" },
          { cmd: "192.168.1.50  pi.home", noRun: true, note: "Una línea en /etc/hosts. Ahora ssh furry@pi.home." },
        ] },
        { title: "Cortafuegos y VPN", blocks: [
          { cmd: "sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp", noRun: true, note: "SSH solo desde la red de casa." },
          { cmd: "sudo ufw status numbered", note: "Reglas numeradas; borrar una: sudo ufw delete N." },
          { p: "<b>VPN, con sinceridad:</b> el <b>WireGuard</b> normal va integrado en el kernel y es muy rápido, pero en Rusia (igual que OpenVPN) suele estar bloqueado: los bloqueos reconocen el propio protocolo. Funciona donde no lo bloquean, por ejemplo para entrar a tu propio servidor de casa. La configuración va en <code>/etc/wireguard/wg0.conf</code>:" },
          { cmd: "sudo pacman -S wireguard-tools && sudo wg-quick up wg0", noRun: true, note: "Desconectar: sudo wg-quick down wg0." },
          { p: "Si WireGuard no conecta, hace falta un protocolo camuflado. <b>AmneziaWG</b> es un fork de WireGuard que oculta los paquetes reconocibles. Lo más fácil es la app <b>AmneziaVPN</b> del AUR: pegas la clave o la configuración de tu proveedor de VPN (o de tu propio servidor con Amnezia) y pulsas Conectar:" },
          { cmd: "yay -S amneziavpn-bin", noRun: true, note: "Para la terminal está amneziawg-tools + amneziawg-dkms (AUR): configuración en /etc/amnezia/amneziawg/awg0.conf, se inicia con sudo awg-quick up awg0." },
          { p: "Si tu proveedor te da una <b>suscripción VLESS / Reality</b> (un enlace vless://… o una URL de suscripción), necesitas un cliente para ella: <b>Throne</b> (antes NekoRay) o <b>Hiddify</b>. Los dos están en el AUR: pegas el enlace y listo:" },
          { cmd: "yay -S throne-bin", noRun: true, note: "O yay -S hiddify. Los paquetes del AUR los hacen personas, no Arch: revisa lo que instalas y usa claves solo de tu propio proveedor." },
          { say: "Una regla del cortafuegos es un candado: escribe la más estrecha que funcione. «Abrir todo a todos» no es un ajuste, es limonada en vez de limón 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Para qué sirve /etc/hosts?", a: ["Asociar nombres a IP en local", "Guardar contraseñas del Wi-Fi", "Una lista de paquetes"], ok: 0 },
        { q: "¿Cómo permites SSH solo desde la red de casa?", a: ["ufw allow from 192.168.1.0/24 to any port 22", "ufw disable", "ufw allow 22 para todos"], ok: 0 },
        { q: "WireGuard no conecta por los bloqueos. ¿Qué probar?", a: ["AmneziaWG (la app AmneziaVPN) o un cliente VLESS/Reality", "Reinstalar el kernel", "Apagar el cortafuegos"], ok: 0 },
      ],
    },
    {
      id: "d-sshd", mood: "grr", badge: "🍋 Dueño del servidor", title: "Tu propio servidor SSH",
      intro: "Solo con claves, sin root, y túneles.",
      lessons: [
        { title: "Apretando tornillos", blocks: [
          { cmd: "sudo pacman -S openssh && sudo systemctl enable --now sshd", noRun: true },
          { p: "Los ajustes van en <code>/etc/ssh/sshd_config.d/</code> (tu propio archivo, p. ej. <code>10-furros.conf</code>):" },
          { cmd: "PermitRootLogin no\nPasswordAuthentication no\nKbdInteractiveAuthentication no", noRun: true, note: "Solo claves, nada de root. ¡Antes comprueba que entrar con clave funciona!" },
          { cmd: "sudo sshd -t && sudo systemctl reload sshd", noRun: true, note: "sshd -t comprueba la configuración. Un error ahí puede dejarte fuera." },
          { warn: "¿Editas SSH en un servidor remoto? Deja abierta una segunda sesión hasta probar el nuevo acceso. Si no, te puedes quedar fuera." },
        ] },
        { title: "Túneles", blocks: [
          { cmd: "ssh -L 8080:localhost:80 user@server", noRun: true, note: "El panel web del servidor (puerto 80) se abre en tu localhost:8080. No hace falta exponer nada a internet." },
          { cmd: "ssh -D 1080 user@server", noRun: true, note: "Un proxy SOCKS a través del servidor." },
          { cmd: "sudo journalctl -u sshd | grep -i failed | tail", note: "Quién intentó adivinar la contraseña." },
          { say: "A un servidor con contraseña y el puerto 22 abierto lo empiezan a atacar minutos después de encenderlo. Con claves, los bots se quedan mirando. Con un limón 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Qué debes hacer antes de PasswordAuthentication no?", a: ["Comprobar que entrar con clave funciona", "Borrar las claves", "Apagar el cortafuegos"], ok: 0 },
        { q: "¿Cómo compruebas errores en la configuración de sshd?", a: ["sudo sshd -t", "ssh -v", "cat sshd"], ok: 0 },
        { q: "¿Qué hace ssh -L 8080:localhost:80?", a: ["Te trae el puerto del servidor", "Abre el puerto a internet", "Borra el puerto 80"], ok: 0 },
      ],
    },
    {
      id: "d-perf", mood: "timer", badge: "🍋 Overclocker", title: "Rendimiento",
      intro: "Dónde va lento: CPU, memoria, disco. zram, governor y temperaturas.",
      lessons: [
        { title: "Encontrar el cuello de botella", blocks: [
          { table: { head: ["Herramienta", "Qué muestra"], rows: [
            ["<code>btop</code>", "Todo a la vez y bonito: CPU, memoria, discos, red, procesos"],
            ["<code>sudo iotop</code>", "Quién machaca el disco"], ["<code>free -h</code>", "Memoria y swap"],
            ["<code>sensors</code>", "Temperaturas (paquete lm_sensors)"], ["<code>nvtop</code>", "Carga de la tarjeta gráfica"],
            ["<code>journalctl -k -p 4</code>", "Avisos del kernel: sobrecalentamiento, errores de disco"],
          ] } },
          { cmd: "sudo pacman -S btop lm_sensors nvtop iotop" },
        ] },
        { title: "Memoria y CPU", blocks: [
          { p: "<b>zram</b> es swap comprimido en la propia memoria: cuando falta RAM, el sistema se ralentiza mucho menos que con swap en disco." },
          { cmd: "zramctl", note: "¿Hay zram? Para configurarlo: el paquete zram-generator y /etc/systemd/zram-generator.conf." },
          { p: "El <b>governor</b> decide lo rápido que la CPU sube la frecuencia:" },
          { cmd: "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" },
          { cmd: "powerprofilesctl set performance", noRun: true, note: "El perfil de rendimiento (o balanced / power-saver). Útil antes de jugar; en un portátil gasta más batería." },
          { say: "Primero mide, luego toca. Un «truco de internet» sin medir es leer el futuro en pepitas de limón 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Qué es zram?", a: ["Swap comprimido en la RAM", "Un nuevo tipo de SSD", "Un controlador gráfico"], ok: 0 },
        { q: "¿Qué muestra quién carga el disco?", a: ["iotop", "ping", "ls"], ok: 0 },
        { q: "¿Qué hacer antes de ajustar el rendimiento?", a: ["Medir dónde está el cuello de botella", "Cambiarlo todo a la vez", "Reinstalar el sistema"], ok: 0 },
      ],
    },
    {
      id: "d-gpu", mood: "wave", badge: "🍋 Mago de los píxeles", title: "Gráficos: Wayland, X11, controladores",
      intro: "Mesa y NVIDIA, Wayland contra X11, gráficos híbridos y comprobar Vulkan.",
      lessons: [
        { title: "Quién dibuja la imagen", blocks: [
          { p: "<b>Mesa</b> son los controladores libres para AMD e Intel; ya están en el kernel y funcionan desde el primer momento. Para NVIDIA: <code>nvidia-open</code> (RTX y GTX 16xx) o <code>nvidia-580xx</code> de [furros] (GTX 750–10xx). Qué tienes instalado: <code>furros-drivers</code>." },
          { cmd: "echo $XDG_SESSION_TYPE", note: "wayland o x11: sobre qué funciona tu sesión." },
          { cmd: "sudo pacman -S vulkan-tools mesa-utils && vulkaninfo --summary && glxinfo -B", noRun: true, note: "Qué tarjeta y qué controlador usan Vulkan y OpenGL." },
          { p: "<b>Wayland</b> es el protocolo gráfico nuevo: más fluido, más seguro, mejor con monitores de distintas frecuencias. <b>X11</b> es el antiguo, pero algunos programas aún solo viven ahí. En Wayland funcionan gracias a <b>Xwayland</b>." },
        ] },
        { title: "Gráficos híbridos y NVIDIA", blocks: [
          { p: "Un portátil con dos tarjetas: por defecto trabaja la integrada (ahorra batería), y lo pesado se lanza en la dedicada:" },
          { cmd: "prime-run steam", noRun: true, note: "El paquete nvidia-prime. Para AMD+AMD: DRI_PRIME=1 programa." },
          { cmd: "cat /sys/module/nvidia_drm/parameters/modeset", note: "Y — el modo que Wayland necesita con NVIDIA está activo." },
          { say: "¿Pantalla negra con NVIDIA tras actualizar? Casi siempre el controlador no coincide con el kernel. Consola (Ctrl+Alt+F3), <code>sudo pacman -Syu</code>, reinicio. O el kernel LTS de repuesto 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Cómo sabes si usas Wayland o X11?", a: ["echo $XDG_SESSION_TYPE", "uname -r", "ls /wayland"], ok: 0 },
        { q: "¿Qué es Xwayland?", a: ["Una forma de ejecutar programas X11 dentro de Wayland", "Un escritorio nuevo", "Un controlador de NVIDIA"], ok: 0 },
        { q: "¿Cómo lanzas un programa en la NVIDIA dedicada de un portátil?", a: ["prime-run programa", "sudo programa", "nvidia programa --fast"], ok: 0 },
      ],
    },
    {
      id: "d-pkg", mood: "hoodie", badge: "🍋 Empaquetador", title: "Tu propio paquete y repositorio",
      intro: "Escribir un PKGBUILD, revisarlo con namcap y montar tu propio repositorio.",
      lessons: [
        { title: "Un PKGBUILD desde cero", blocks: [
          { p: "Tu propio script o programa se instala mejor como paquete: pacman conoce sus archivos, lo actualiza y lo quita limpiamente." },
          { cmd: "pkgname=lemon-timer\npkgver=1.0\npkgrel=1\npkgdesc=\"Un temporizador con limón\"\narch=(any)\nlicense=(MIT)\ndepends=(bash libnotify)\nsource=(lemon-timer)\nsha256sums=(SKIP)\n\npackage() {\n  install -Dm755 lemon-timer \"$pkgdir/usr/bin/lemon-timer\"\n}", noRun: true, note: "Un PKGBUILD junto al script lemon-timer." },
          { cmd: "makepkg -si", noRun: true },
          { cmd: "namcap PKGBUILD *.pkg.tar.zst", noRun: true, note: "Busca errores típicos: dependencias, permisos, rutas." },
          { tip: "En vez de SKIP, pon sumas reales: <code>updpkgsums</code> (paquete pacman-contrib) las calcula por ti." },
        ] },
        { title: "Tu propio repositorio", blocks: [
          { p: "Varios paquetes propios para varios ordenadores se gestionan mejor en un repositorio, igual que FurrOS con su [furros]:" },
          { cmd: "repo-add ~/repo/lemon.db.tar.zst ~/repo/*.pkg.tar.zst", noRun: true },
          { cmd: "[lemon]\nSigLevel = Optional TrustAll\nServer = file:///home/furry/repo", noRun: true, note: "Una sección en /etc/pacman.conf. Para otras personas, los paquetes se firman (gpg + makepkg --sign) y se pone SigLevel = Required." },
          { say: "Así es justo como FurrOS te entrega los fondos, la Escuela de Lapa y los controladores: paquetes firmados en el repositorio [furros], que un simple <code>pacman -Syu</code> actualiza 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Dónde pone package() los archivos?", a: ["En $pkgdir, que luego se convierte en el paquete", "Directamente en /usr", "En tu carpeta personal"], ok: 0 },
        { q: "¿Qué revisa un paquete en busca de errores típicos?", a: ["namcap", "ping", "grep"], ok: 0 },
        { q: "¿Qué comando crea la base de datos de un repositorio?", a: ["repo-add", "pacman -Syu", "mkinitcpio"], ok: 0 },
      ],
    },
    {
      id: "d-containers", mood: "wave", badge: "🍋 Capitán de contenedores", title: "Contenedores",
      intro: "Podman y Docker, distrobox para programas de otras distros, permisos de Flatpak.",
      lessons: [
        { title: "Podman y Docker", blocks: [
          { p: "Un contenedor es una caja aislada con su propio minisistema. El programa de dentro no molesta al sistema principal y se borra con un comando." },
          { cmd: "sudo pacman -S podman && podman run --rm -it archlinux bash", noRun: true, note: "Un Arch limpio en un contenedor. --rm — borrarlo al salir. Podman funciona sin root." },
          { cmd: "podman ps -a && podman images", noRun: true, note: "Contenedores e imágenes. Limpiar: podman system prune." },
          { p: "Docker funciona parecido (<code>sudo pacman -S docker && sudo systemctl enable --now docker</code>), pero a través de un servicio de root." },
        ] },
        { title: "distrobox y Flatpak", blocks: [
          { p: "<b>distrobox</b> ejecuta otra distro en un contenedor, pero con tu carpeta personal, sonido y gráficos. ¿Un programa que solo existe para Ubuntu? Sin problema:" },
          { cmd: "sudo pacman -S distrobox podman && distrobox create -n ubuntu -i ubuntu:24.04 && distrobox enter ubuntu", noRun: true },
          { cmd: "distrobox-export --app nombre-del-programa", noRun: true, note: "Dentro del contenedor: añadir el programa al menú de FurrOS." },
          { p: "Los permisos de las apps Flatpak (carpetas, dispositivos) se ven y cambian fácilmente en <b>Flatseal</b>:" },
          { cmd: "flatpak install flathub com.github.tchx84.Flatseal", noRun: true },
          { say: "¿Quieres probar algo dudoso? Hazlo en un contenedor. Si no te gusta, borras la caja y el sistema queda limpio. Como un limón en bolsa: no gotea 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Qué hace podman run --rm?", a: ["Borra el contenedor al salir", "Borra la imagen", "Desinstala podman"], ok: 0 },
        { q: "¿Para qué sirve distrobox?", a: ["Ejecutar programas de otras distros como si fueran nativos", "Acelerar el Wi-Fi", "Hacer instantáneas de Btrfs"], ok: 0 },
        { q: "¿Dónde cambias fácilmente los permisos de las apps Flatpak?", a: ["Flatseal", "GRUB", "htop"], ok: 0 },
      ],
    },
    {
      id: "d-vm", mood: "timer", badge: "🍋 Domador de VMs", title: "Máquinas virtuales",
      intro: "KVM/QEMU y virt-manager: Windows u otro Linux en una ventana.",
      lessons: [
        { title: "Instalar KVM", blocks: [
          { cmd: "grep -Ec '(vmx|svm)' /proc/cpuinfo", note: "Más de cero — la CPU admite virtualización. Si sale 0, activa VT-x/AMD-V (SVM) en la BIOS." },
          { cmd: "sudo pacman -S qemu-desktop libvirt virt-manager dnsmasq edk2-ovmf swtpm", noRun: true, note: "edk2-ovmf — UEFI, swtpm — el TPM que pide Windows 11." },
          { cmd: "sudo systemctl enable --now libvirtd && sudo usermod -aG libvirt $USER", noRun: true, note: "Cierra sesión y vuelve a entrar para que se aplique el grupo." },
          { p: "Luego abre <b>Virtual Machine Manager</b>, pulsa «Crear una máquina virtual» y elige una ISO. Para casos sencillos también está <b>GNOME Boxes</b>." },
        ] },
        { title: "Que vaya rápido", blocks: [
          { ul: [
            "Disco y red — tipo <b>virtio</b>: bastante más rápidos que los emulados. Windows necesita los controladores virtio-win (una ISO de la web de Fedora).",
            "CPU — modo <b>host-passthrough</b>.",
            "No le des a la VM más de la mitad de núcleos y memoria; el anfitrión también tiene que vivir.",
            "Instantáneas de la VM antes de experimentar, igual que en el propio FurrOS.",
          ] },
          { say: "Una máquina virtual es el mejor campo de pruebas. ¿Quieres romper el gestor de arranque para aprender a arreglarlo? Rómpelo ahí, no en tu sistema principal 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Cómo compruebas que la CPU admite virtualización?", a: ["grep -Ec '(vmx|svm)' /proc/cpuinfo", "uname -r", "lsusb"], ok: 0 },
        { q: "¿Qué tipo de disco y red es el más rápido en KVM?", a: ["virtio", "IDE", "disquete"], ok: 0 },
        { q: "¿A qué grupo te unes para libvirt?", a: ["libvirt", "wheel", "audio"], ok: 0 },
      ],
    },
    {
      id: "d-security", mood: "grr", badge: "🍋 Paranoico", title: "Seguridad a fondo",
      intro: "Cifrado LUKS, sudoers, claves de pacman y Secure Boot.",
      lessons: [
        { title: "Cifrado y sudo", blocks: [
          { p: "<b>LUKS</b> cifra una partición entera: si te roban el portátil, sin la contraseña no se pueden leer los datos. Cifrar un USB:" },
          { cmd: "sudo cryptsetup luksFormat /dev/sdX1", noRun: true, note: "¡BORRA todo lo de la partición! Luego: sudo cryptsetup open /dev/sdX1 secret && sudo mkfs.ext4 /dev/mapper/secret" },
          { cmd: "sudo cryptsetup luksDump /dev/sdX1", noRun: true, note: "Detalles del cifrado y de las ranuras de claves." },
          { p: "Los permisos de sudo solo se editan con <code>visudo</code>: revisa la sintaxis, así no te quedas sin sudo." },
          { cmd: "sudo EDITOR=nano visudo -f /etc/sudoers.d/10-furry", noRun: true },
          { warn: "Un sudoers roto = sin sudo. Así que solo visudo, nunca un editor normal." },
        ] },
        { title: "Claves y Secure Boot", blocks: [
          { p: "pacman comprueba la firma de cada paquete. Si se queja de las claves (pasa tras una pausa larga):" },
          { cmd: "sudo pacman -Sy archlinux-keyring furros-keyring && sudo pacman -Su", noRun: true },
          { cmd: "pacman-key --list-keys | grep -i furros", note: "La clave del repositorio [furros] está en su sitio." },
          { p: "<b>Secure Boot</b> con Linux se puede activar con tus propias claves usando <b>sbctl</b> (<code>sbctl status</code>, <code>sbctl create-keys</code>, <code>sbctl enroll-keys -m</code>, y firmar el gestor de arranque y el kernel). Es un ajuste avanzado: lee la wiki de Arch y ten a mano un USB de FurrOS." },
          { say: "La seguridad son capas: actualizaciones, cortafuegos, claves, cifrado, copias. Ninguna capa es perfecta; juntas son una fortaleza. Hasta un limón tiene piel 🍋" },
        ] },
      ],
      quiz: [
        { q: "¿Con qué se editan los permisos de sudo?", a: ["visudo", "nano /etc/sudoers directamente", "chmod 777"], ok: 0 },
        { q: "¿Qué hace cryptsetup luksFormat con una partición?", a: ["Crea una partición cifrada borrando los datos", "Comprueba el disco", "Acelera el disco"], ok: 0 },
        { q: "pacman se queja de las claves. ¿Qué actualizas primero?", a: ["archlinux-keyring (y furros-keyring)", "El kernel", "Firefox"], ok: 0 },
      ],
    },
    {
      id: "d-rescue", mood: "grr", badge: "🍋 Reanimador", title: "Reparaciones extremas",
      intro: "Arreglar el gestor de arranque, el bloqueo de pacman, una actualización cortada y rescue.target.",
      lessons: [
        { title: "Averías típicas", blocks: [
          { table: { head: ["Problema", "Solución"], rows: [
            ["«unable to lock database»", "¿pacman no está en marcha? Entonces <code>sudo rm /var/lib/pacman/db.lck</code>"],
            ["Una actualización se cortó (luz, batería)", "Desde la consola o un chroot: <code>sudo pacman -Syu</code>, luego <code>sudo mkinitcpio -P</code>"],
            ["«invalid or corrupted package (PGP signature)»", "Actualiza el keyring (ver el capítulo anterior)"],
            ["Desapareció el menú de FurrBoot tras Windows", "Elige «FurrOS» en el menú de arranque de la placa (F11/F12/F8): es el GRUB de reserva. Luego en el sistema: <code>sudo furrboot-install</code>"],
            ["No arrancan los gráficos", "Ctrl+Alt+F3, el registro: <code>journalctl -b -1 -p 3</code> (errores del arranque anterior)"],
          ] } },
          { p: "Si ni siquiera llegas a una consola, pulsa <kbd>E</kbd> en FurrBoot y añade al final de los parámetros: <code>systemd.unit=rescue.target</code>. El sistema arranca en un modo mínimo con consola de root." },
        ] },
        { title: "Un chroot completo", blocks: [
          { p: "Desde un USB de FurrOS. Para FurrOS sobre Btrfs:" },
          { cmd: "lsblk -f\nsudo mount -o subvol=@ /dev/nvme0n1p2 /mnt\nsudo mount /dev/nvme0n1p1 /mnt/boot/efi\nsudo arch-chroot /mnt", noRun: true, note: "Toma los nombres de las particiones de lsblk. La partición EFI va a /boot/efi en una instalación Btrfs, a /boot en ext4 y cifrada. Un disco cifrado se abre antes: cryptsetup open." },
          { p: "Dentro es como estar en tu sistema: actualiza, reinstala el kernel (<code>pacman -S linux</code>), arregla el menú de arranque (<code>furrboot-install</code>), corrige fstab. Para salir: <code>exit</code>, luego <code>sudo umount -R /mnt</code>." },
          { say: "Si has llegado hasta aquí, un sistema roto ya no te asusta. Sabes cómo funciona, así que sabes cómo levantarlo. Eso es ser maestro 🍋" },
        ] },
      ],
      quiz: [
        { q: "pacman dice «unable to lock database» pero no está en marcha. ¿Qué haces?", a: ["Borrar /var/lib/pacman/db.lck", "Reinstalar el sistema", "Desinstalar pacman"], ok: 0 },
        { q: "¿Cómo arrancas en modo mínimo desde el menú de arranque?", a: ["Añadiendo systemd.unit=rescue.target", "Pulsando F12", "Añadiendo quiet"], ok: 0 },
        { q: "¿Cómo ves los errores del arranque anterior?", a: ["journalctl -b -1 -p 3", "dmesg --future", "pacman -Qe"], ok: 0 },
      ],
    },
    {
      id: "d-final", mood: "wave", badge: "🍋 Maestro de FurrOS", title: "La graduación de Danyok",
      intro: "Git, informes de fallos, la Arch Wiki y cómo ayudar a FurrOS.",
      lessons: [
        { title: "Git en cinco minutos", blocks: [
          { cmd: "git clone https://github.com/Vitlikxbox/FurrOS.git && cd FurrOS", noRun: true },
          { table: { head: ["Comando", "Qué hace"], rows: [
            ["<code>git status</code>", "Qué ha cambiado"], ["<code>git diff</code>", "Los cambios en sí"],
            ["<code>git add archivo</code>", "Prepararlo para guardar"], ["<code>git commit -m \"qué hice\"</code>", "Guardar una versión"],
            ["<code>git log --oneline</code>", "El historial"], ["<code>git switch -c fix-typo</code>", "Una rama nueva para tus cambios"],
          ] } },
          { tip: "Guardar tus configuraciones en git es un gran hábito: cualquier cambio fallido se deshace, y pasarlas a un ordenador nuevo es un solo comando." },
        ] },
        { title: "Cómo ayudar", blocks: [
          { ul: [
            "<b>Un buen informe de fallo</b>: qué hiciste, qué esperabas, qué pasó, la versión (<code>fastfetch</code>) y un registro (<code>journalctl -b -p 3</code> o <code>/var/log/furros-install.log</code>).",
            "¿Encontraste un error en una traducción o una lección? Escribe en el Discord de FurrOS o abre una issue en GitHub.",
            "La <b>Arch Wiki</b> la escriben usuarios como tú. ¿Ves algo mal? Corrígelo: es el mejor regalo al mundo Linux.",
            "Ayuda a los novatos en el chat: explicárselo a otro es la mejor forma de entenderlo tú.",
          ] },
          { say: "Eso es todo. Tres profes, cuarenta y dos capítulos. Has pasado de «qué es una terminal» a chroot y tus propios paquetes. Lapa está orgullosa, Velvet lo aprueba, y de mi parte, un limón. Te lo has ganado 🍋🎓" },
        ] },
      ],
      quiz: [
        { q: "¿Qué debe incluir un informe de fallo?", a: ["Los pasos, lo esperado, lo que pasó y un registro", "Solo «no funciona»", "Una captura de tu fondo de pantalla"], ok: 0 },
        { q: "¿Qué comando guarda una versión en git?", a: ["git commit", "git status", "git log"], ok: 0 },
        { q: "¿Quién escribe la Arch Wiki?", a: ["Los usuarios, y tú también puedes", "Solo empleados de Microsoft", "Nadie, se escribe sola"], ok: 0 },
      ],
    },
  ] },
};
