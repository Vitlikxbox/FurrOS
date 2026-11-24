/* Lapa's School, levels 2 and 3: Pixie (a confident user) and Danyok (the system inside out). 14 chapters each. */
Object.assign(window.CONTENT.pl.ui, {
  levelsTitle: "Poziomy", level: "Poziom",
  levelsIntro: "Trzech nauczycieli, z każdym trudniej. Lapa uczy żyć w FurrOS, Pixie — pewnie rządzić systemem, Danyok — rozebrać go na części.",
  lvl_lapa: "Lapa", lvl_pixie: "Pixie", lvl_danyok: "Danyok",
  diff_lapa: "początkujący", diff_pixie: "pewny użytkownik", diff_danyok: "mistrz systemu",
  lvlIntro_lapa: "Pulpit, pliki, terminal, programy, gry i pierwsza pomoc.",
  lvlIntro_pixie: "Potoki, procesy, usługi, dyski, sieć, SSH, AUR i własne skrypty.",
  lvlIntro_danyok: "Rozruch, jądro, Btrfs, własne usługi, kontenery, maszyny wirtualne, szyfrowanie i hardkorowe naprawy.",
  lvlHello_lapa: "Poziom Lapy 🐾", lvlHello_pixie: "Siema, jestem Pixie. Teraz uczę ja 🖤", lvlHello_danyok: "Cześć. Jestem Danyok i mam cytrynę 🍋",
  lvlText_lapa: "Podstawy: jak żyć w FurrOS i niczego się nie bać. Zacznij tutaj, jeśli Linux jest dla ciebie nowy.",
  lvlText_pixie: "Lapa nauczyła cię nie bać się terminala. Ja nauczę cię nim rządzić: łączyć polecenia, znajdować wszystko, zarządzać procesami i usługami, łączyć się z innymi komputerami przez SSH i pisać własne skrypty. Będzie trochę trudniej, ale potem zrobisz w minutę to, co kiedyś zajmowało godzinę.",
  lvlText_danyok: "Ostatni poziom. Zajrzymy do środka: jak system się uruchamia, co robi jądro, jak działają Btrfs i systemd, jak zbudować własny pakiet, postawić kontener i maszynę wirtualną, zaszyfrować dysk i podnieść system z martwych. Nie spiesz się i próbuj wszystkiego na maszynie wirtualnej albo ze świeżą migawką.",
  lvlFirst: "Najpierw polecamy przejść poziom „{0}”. Ale jeśli czujesz się pewnie, możesz od razu.",
  says_pixie: "Pixie mówi", says_danyok: "Danyok mówi",
  nextLevel: "Dalej: {0}",
  diplomaTitle_pixie: "Dyplom Pixie 🎓", diplomaText_pixie: "Ukończyłeś(-aś) poziom pewnego użytkownika: potoki, procesy, usługi, dyski, sieć, SSH, AUR i skrypty. Teraz terminal pracuje dla ciebie, a nie odwrotnie. Pixie zatwierdza 🖤",
  diplomaTitle_danyok: "Dyplom Danyoka 🎓🍋", diplomaText_danyok: "Ukończyłeś(-aś) wszystkie trzy poziomy Szkoły Lapy. Rozruch, jądro, Btrfs, systemd, pakiety, kontenery, szyfrowanie i naprawy są teraz twoje. Oficjalnie jesteś mistrzem FurrOS. Trzymaj cytrynę 🍋",
});

window.CONTENT.pl.levels = {
  pixie: { chapters: [
    {
      id: "p-shell", mood: "wave", badge: "⚡ Znawca basha", title: "Głębiej w bash",
      intro: "Ścieżki, wzorce, zmienne, aliasy i twój ~/.bashrc.",
      lessons: [
        { title: "Ścieżki i wzorce", blocks: [
          { p: "Ścieżka bywa <b>bezwzględna</b> (od korzenia: <code>/home/furry/Documents</code>) albo <b>względna</b> (od bieżącego folderu: <code>Documents/notes.txt</code>). <code>.</code> to bieżący folder, <code>..</code> folder wyżej, <code>~</code> folder domowy, a <code>-</code> w <code>cd -</code> poprzedni." },
          { p: "Wzorce (wildcards) dopasowują wiele plików naraz: <code>*</code> — dowolne znaki, <code>?</code> — jeden znak, <code>{a,b}</code> — warianty." },
          { cmd: "ls ~/Pictures/*.png", note: "Wszystkie pliki PNG w folderze Obrazy." },
          { cmd: "mkdir -p project/{src,docs,tests}", note: "Trzy foldery jednym poleceniem. -p tworzy też folder nadrzędny." },
          { say: "Wzorzec rozwija sam bash, a nie program. Dlatego przed <code>rm *</code> najpierw wykonaj <code>ls *</code> i zobacz, co oberwie 🖤" },
        ] },
        { title: "Zmienne i aliasy", blocks: [
          { p: "Powłoka ma <b>zmienne środowiskowe</b>. Widzą je wszystkie programy z niej uruchomione:" },
          { table: { head: ["Zmienna", "Co przechowuje"], rows: [
            ["<code>$HOME</code>", "Folder domowy"], ["<code>$USER</code>", "Nazwę użytkownika"],
            ["<code>$PATH</code>", "Gdzie szukać poleceń (foldery rozdzielone dwukropkami)"], ["<code>$EDITOR</code>", "Domyślny edytor"],
          ] } },
          { cmd: "echo $PATH" },
          { p: "<b>Alias</b> to krótka nazwa długiego polecenia. Żeby działał zawsze, dopisz go do <code>~/.bashrc</code>:" },
          { cmd: "echo \"alias update='sudo pacman -Syu'\" >> ~/.bashrc && source ~/.bashrc", note: "source wczytuje plik ponownie bez restartu terminala." },
          { tip: "Własne skrypty wygodnie trzymać w <code>~/.local/bin</code>: w FurrOS ten folder już jest w $PATH, więc skrypty uruchamiasz po nazwie z dowolnego miejsca." },
        ] },
      ],
      quiz: [
        { q: "Co robi cd - ?", a: ["Przechodzi do poprzedniego folderu", "Usuwa folder", "Przechodzi do korzenia"], ok: 0 },
        { q: "Co dopasuje wzorzec *.txt?", a: ["Wszystkie pliki kończące się na .txt", "Tylko plik o nazwie *.txt", "Wszystkie ukryte pliki"], ok: 0 },
        { q: "Gdzie jest lista folderów, w których bash szuka poleceń?", a: ["$HOME", "$PATH", "$USER"], ok: 1 },
      ],
    },
    {
      id: "p-pipes", mood: "wave", badge: "⚡ Hydraulik", title: "Przekierowania i potoki",
      intro: "Łączymy polecenia: >, >>, 2>, | i filtry grep, sort, wc.",
      lessons: [
        { title: "Dokąd trafia wynik", blocks: [
          { p: "Każde polecenie ma trzy strumienie: wejście (stdin), wyjście (stdout) i błędy (stderr). Można je przekierować:" },
          { table: { head: ["Zapis", "Co robi"], rows: [
            ["<code>polecenie > plik</code>", "Zapisz wynik do pliku (stara zawartość znika)"],
            ["<code>polecenie >> plik</code>", "Dopisz na końcu pliku"],
            ["<code>polecenie 2> plik</code>", "Zapisz tylko błędy"],
            ["<code>polecenie &> plik</code>", "Wynik i błędy razem"],
            ["<code>polecenie > /dev/null</code>", "Wyrzuć wynik („czarna dziura”)"],
            ["<code>polecenie &lt; plik</code>", "Weź wejście z pliku"],
          ] } },
          { cmd: "pacman -Qe > ~/my-packages.txt", note: "Lista jawnie zainstalowanych pakietów w pliku. Przyda się przy reinstalacji." },
        ] },
        { title: "Potok |", blocks: [
          { p: "Kreska <code>|</code> przekazuje wynik jednego polecenia na wejście następnego. Tak z małych poleceń powstają duże:" },
          { table: { head: ["Filtr", "Co robi"], rows: [
            ["<code>grep słowo</code>", "Zostaw linie ze słowem (<code>-i</code> bez wielkości liter, <code>-v</code> odwrotnie)"],
            ["<code>sort</code>", "Posortuj (<code>-n</code> liczbowo, <code>-r</code> odwrotnie)"],
            ["<code>uniq -c</code>", "Połącz identyczne sąsiednie linie i policz je"],
            ["<code>wc -l</code>", "Policz linie"],
            ["<code>head -n 5</code> / <code>tail -n 5</code>", "Pierwsze / ostatnie linie"],
            ["<code>less</code>", "Przewijaj długi wynik (wyjście: q, szukanie: /)"],
          ] } },
          { cmd: "pacman -Q | wc -l", note: "Ile pakietów jest zainstalowanych." },
          { cmd: "pacman -Q | grep -i nvidia", note: "Które pakiety NVIDIA są zainstalowane." },
          { cmd: "du -sh ~/* 2>/dev/null | sort -h | tail -n 5", note: "Pięć najcięższych folderów w katalogu domowym." },
          { say: "Potoki to supermoc Linuksa. Każde polecenie robi jedną rzecz, ale dobrze, a kreska skleja je w cokolwiek. Jak Lego, tylko dla dorosłych 🖤" },
        ] },
      ],
      quiz: [
        { q: "Czym > różni się od >>?", a: ["> nadpisuje plik, >> dopisuje na końcu", "Niczym", ">> usuwa plik"], ok: 0 },
        { q: "Co dostaje polecenie po prawej stronie | ?", a: ["Wynik lewego jako wejście", "Uruchamia się osobno i niezależnie", "Anuluje lewe"], ok: 0 },
        { q: "Jak wyrzucić błędy polecenia?", a: ["2>/dev/null", "| grep", ">> errors"], ok: 0 },
      ],
    },
    {
      id: "p-find", mood: "hoodie", badge: "⚡ Tropicielka", title: "Szukanie wszystkiego",
      intro: "find, grep -r, plocate, which: znajdź plik, tekst albo program.",
      lessons: [
        { title: "Znaleźć plik", blocks: [
          { cmd: "find ~ -name \"*.pdf\"", note: "Wszystkie PDF-y w katalogu domowym. -iname — bez wielkości liter." },
          { cmd: "find ~/Downloads -type f -size +500M", note: "Pliki większe niż 500 MB w Pobranych." },
          { cmd: "find ~ -type f -mtime -1", note: "Pliki zmienione w ciągu ostatniej doby." },
          { p: "find naprawdę przechodzi przez wszystkie foldery, więc bywa wolny. Szybciej szukać w gotowej bazie: <b>plocate</b>." },
          { cmd: "sudo pacman -S plocate && sudo updatedb", note: "Zainstaluj i zbuduj bazę. Potem aktualizuje się sama raz dziennie." },
          { cmd: "locate hyprland.lua" },
        ] },
        { title: "Znaleźć tekst i program", blocks: [
          { cmd: "grep -rn \"monitor\" ~/.config/hypr/", note: "We wszystkich plikach folderu: -r rekurencyjnie, -n z numerem linii." },
          { cmd: "which firefox", note: "Gdzie leży program uruchamiany przez polecenie." },
          { cmd: "pacman -F libGL.so.1", note: "Który pakiet zawiera plik, nawet niezainstalowany. Bazę plików aktualizuje sudo pacman -Fy." },
          { say: "Błąd „error while loading shared libraries: libcoś.so” leczy się właśnie tak: pacman -F znajduje pakiet, który trzeba doinstalować 🖤" },
        ] },
      ],
      quiz: [
        { q: "Jak znaleźć wszystkie .jpg w katalogu domowym?", a: ["find ~ -name \"*.jpg\"", "grep jpg ~", "ls -jpg"], ok: 0 },
        { q: "Czym najszybciej znaleźć plik po nazwie w całym systemie?", a: ["locate (plocate)", "cat", "wc"], ok: 0 },
        { q: "Jak sprawdzić, w którym pakiecie jest libGL.so.1?", a: ["pacman -F libGL.so.1", "which libGL.so.1", "pacman -Syu"], ok: 0 },
      ],
    },
    {
      id: "p-text", mood: "hoodie", badge: "⚡ Redaktorka", title: "Edytory i tekst",
      intro: "nano jak profi, przetrwanie w vimie, diff i szybkie poprawki sedem.",
      lessons: [
        { title: "nano i vim", blocks: [
          { p: "<b>nano</b>: podpowiedzi na dole, <code>^</code> to Ctrl. Przydatne: <kbd>Ctrl</kbd>+<kbd>W</kbd> szukaj, <kbd>Ctrl</kbd>+<kbd>K</kbd> wytnij linię, <kbd>Ctrl</kbd>+<kbd>U</kbd> wklej, <kbd>Alt</kbd>+<kbd>U</kbd> cofnij, <kbd>Ctrl</kbd>+<kbd>O</kbd> zapisz, <kbd>Ctrl</kbd>+<kbd>X</kbd> wyjdź." },
          { p: "<b>vim</b> prędzej czy później otworzy się sam (np. w gicie). Żeby przetrwać, wystarczy pięć rzeczy:" },
          { table: { head: ["Klawisze", "Co robi"], rows: [
            ["<kbd>i</kbd>", "Tryb wstawiania: teraz można pisać"], ["<kbd>Esc</kbd>", "Powrót do trybu poleceń"],
            ["<code>:w</code> + Enter", "Zapisz"], ["<code>:q!</code> + Enter", "Wyjdź bez zapisywania"], ["<code>:wq</code> + Enter", "Zapisz i wyjdź"],
          ] } },
          { cmd: "export EDITOR=nano", note: "Żeby programy otwierały nano zamiast vima. Dopisz do ~/.bashrc, żeby działało zawsze." },
        ] },
        { title: "Porównać i zamienić", blocks: [
          { cmd: "diff -u old.conf new.conf", note: "Czym różnią się dwa pliki: - usunięte, + dodane." },
          { cmd: "sed -i 's/stare/nowe/g' plik.txt", noRun: true, note: "Zamień wszędzie w pliku. Bez -i tylko pokaże wynik i nie ruszy pliku." },
          { warn: "sed -i od razu zmienia plik. Przed edycją konfiguracji systemowych zrób kopię: <code>sudo cp plik plik.bak</code>." },
          { say: "Trik Pixie: <code>sed</code> bez <code>-i</code> to podgląd. Najpierw patrzę, potem dodaję -i. Ani jednego zepsutego configu, mrr 🖤" },
        ] },
      ],
      quiz: [
        { q: "Jak wyjść z vima bez zapisywania?", a: [":q! i Enter", "Ctrl+C", "Alt+F4"], ok: 0 },
        { q: "Co pokaże diff -u a b?", a: ["Różnice między plikami", "Rozmiar plików", "Usunie b"], ok: 0 },
        { q: "Co robi flaga -i w sed?", a: ["Edytuje plik w miejscu", "Szuka bez wielkości liter", "Pokazuje pomoc"], ok: 0 },
      ],
    },
    {
      id: "p-proc", mood: "timer", badge: "⚡ Pogromczyni procesów", title: "Procesy",
      intro: "Co teraz działa, jak to zatrzymać i jak uruchamiać w tle.",
      lessons: [
        { title: "Podejrzeć i zatrzymać", blocks: [
          { p: "Każdy uruchomiony program to <b>proces</b> z własnym numerem (PID)." },
          { cmd: "htop", note: "Żywa lista procesów: F6 sortowanie, F9 zabij, q wyjście. Jeśli brak: sudo pacman -S htop" },
          { cmd: "ps aux | grep firefox", note: "Znajdź proces i jego PID." },
          { table: { head: ["Polecenie", "Co robi"], rows: [
            ["<code>kill PID</code>", "Grzecznie poproś o zakończenie (sygnał TERM)"],
            ["<code>kill -9 PID</code>", "Zabij bez gadania (KILL), jeśli zawiesił się na amen"],
            ["<code>pkill firefox</code>", "Zakończ po nazwie"],
            ["<code>xkill</code> / <code>kill</code> w KRunnerze", "Kliknij zawieszone okno (X11 i KDE)"],
          ] } },
          { say: "Najpierw zwykły kill, a dopiero gdy proces nie reaguje, -9. Kill -9 nie pozwala programowi zapisać danych, więc można stracić niezapisaną pracę 🖤" },
        ] },
        { title: "Tło i pierwszy plan", blocks: [
          { ul: [
            "<code>polecenie &</code> — uruchom w tle i dalej pracuj w terminalu.",
            "<kbd>Ctrl</kbd>+<kbd>Z</kbd> — wstrzymaj bieżące polecenie.",
            "<code>jobs</code> — lista zadań w tle, <code>bg</code> — kontynuuj w tle, <code>fg</code> — przywróć na pierwszy plan.",
            "<code>nohup polecenie &</code> — przeżyje nawet zamknięcie terminala.",
          ] },
          { cmd: "free -h", note: "Ile pamięci jest zajęte. Kolumna available to to, co naprawdę wolne." },
          { cmd: "uptime", note: "Jak długo komputer działa i średnie obciążenie." },
        ] },
      ],
      quiz: [
        { q: "Co to jest PID?", a: ["Numer procesu", "Hasło administratora", "Typ pliku"], ok: 0 },
        { q: "Kiedy użyć kill -9?", a: ["Gdy proces zawisł i nie reaguje na zwykły kill", "Zawsze zamiast kill", "Żeby zrestartować PC"], ok: 0 },
        { q: "Co robi Ctrl+Z w terminalu?", a: ["Wstrzymuje polecenie", "Cofa ostatnią czynność", "Zamyka terminal"], ok: 0 },
      ],
    },
    {
      id: "p-systemd", mood: "timer", badge: "⚡ Dyspozytorka usług", title: "Usługi systemd",
      intro: "systemctl, autostart, logi jednej usługi i timery.",
      lessons: [
        { title: "systemctl", blocks: [
          { p: "<b>systemd</b> uruchamia system i pilnuje <b>usług</b>: sieci, dźwięku, Bluetootha, ekranu logowania. Zarządzasz nimi przez <code>systemctl</code>:" },
          { table: { head: ["Polecenie", "Co robi"], rows: [
            ["<code>systemctl status nazwa</code>", "Czy usługa działa i ostatnie linie jej logu"],
            ["<code>sudo systemctl start / stop nazwa</code>", "Uruchom / zatrzymaj teraz"],
            ["<code>sudo systemctl restart nazwa</code>", "Uruchom ponownie"],
            ["<code>sudo systemctl enable nazwa</code>", "Uruchamiaj przy starcie (<code>--now</code> — i od razu)"],
            ["<code>sudo systemctl disable nazwa</code>", "Usuń z autostartu"],
            ["<code>systemctl list-units --type=service</code>", "Wszystkie działające usługi"],
          ] } },
          { cmd: "sudo systemctl enable --now bluetooth" },
          { p: "Są też usługi <b>użytkownika</b>, działające jako ty: <code>systemctl --user status pipewire</code>." },
        ] },
        { title: "Logi i timery", blocks: [
          { cmd: "journalctl -u NetworkManager -b", note: "Log jednej usługi od bieżącego uruchomienia." },
          { cmd: "journalctl -f", note: "Oglądaj log na żywo (wyjście: Ctrl+C)." },
          { p: "<b>Timery</b> systemd zastępują crona: uruchamiają usługi według harmonogramu. FurrOS czyści nimi na przykład pamięć podręczną pacmana:" },
          { cmd: "systemctl list-timers" },
          { say: "Jeśli coś „samo się nie uruchamia po restarcie”, prawie zawsze ktoś zapomniał o <code>enable</code>. start jest na teraz, enable na zawsze 🖤" },
        ] },
      ],
      quiz: [
        { q: "Jak włączyć usługę w autostarcie i od razu ją uruchomić?", a: ["sudo systemctl enable --now nazwa", "sudo systemctl start nazwa", "systemctl status nazwa"], ok: 0 },
        { q: "Jak zobaczyć log jednej usługi?", a: ["journalctl -u nazwa", "cat nazwa", "pacman -Qi nazwa"], ok: 0 },
        { q: "Czym są timery systemd?", a: ["Uruchamianiem usług według harmonogramu", "Zegarem na panelu", "Stoperem w terminalu"], ok: 0 },
      ],
    },
    {
      id: "p-disks", mood: "hoodie", badge: "⚡ Strażniczka dysków", title: "Dyski i miejsce",
      intro: "lsblk, df, du, montowanie, UUID i /etc/fstab.",
      lessons: [
        { title: "Jakie dyski i gdzie miejsce", blocks: [
          { cmd: "lsblk -f", note: "Wszystkie dyski i partycje: system plików, etykieta, UUID, gdzie zamontowane." },
          { cmd: "df -h", note: "Ile wolnego miejsca na każdej partycji." },
          { cmd: "du -sh ~/.cache", note: "Ile waży folder." },
          { cmd: "sudo pacman -S ncdu && ncdu ~", note: "Interaktywnie: strzałkami chodzisz po folderach i widzisz, co zjadło miejsce." },
          { warn: "Na Btrfs <code>df</code> czasem kłamie przez migawki i kompresję. Dokładny obraz: <code>sudo btrfs filesystem usage /</code>." },
        ] },
        { title: "Zamontować dysk na stałe", blocks: [
          { p: "Pendrive’y montują się same. Drugi dysk wewnętrzny można montować przy każdym starcie: wpisuje się go do <code>/etc/fstab</code> po <b>UUID</b> (nazwy typu sdb mogą się zmieniać, UUID nigdy)." },
          { cmd: "sudo mkdir -p /mnt/data && sudo mount /dev/sdb1 /mnt/data", noRun: true, note: "Zamontuj ręcznie raz. Odmontuj: sudo umount /mnt/data" },
          { p: "Linijka do fstab (UUID weź z <code>lsblk -f</code>):" },
          { cmd: "UUID=xxxx-xxxx  /mnt/data  ext4  defaults,nofail  0 2", noRun: true, note: "nofail — system się uruchomi, nawet jeśli dysku nie ma." },
          { cmd: "sudo mount -a", note: "Sprawdź fstab bez restartu: brak błędów oznacza, że wszystko się zamontuje." },
          { say: "Błąd w fstab może nie pozwolić systemowi się uruchomić. Dlatego zawsze <code>nofail</code> dla dodatkowych dysków i koniecznie <code>sudo mount -a</code> przed restartem 🖤" },
        ] },
      ],
      quiz: [
        { q: "Które polecenie pokazuje wolne miejsce na partycjach?", a: ["df -h", "ls -l", "free -h"], ok: 0 },
        { q: "Dlaczego w fstab lepiej pisać UUID niż /dev/sdb1?", a: ["Nazwy sdX mogą się zmieniać, UUID jest stały", "UUID jest krótszy", "Tak jest szybciej"], ok: 0 },
        { q: "Co robi opcja nofail?", a: ["System się uruchomi, nawet jeśli dysku nie ma", "Dysk nigdy się nie zepsuje", "Wyłącza sprawdzanie dysku na zawsze"], ok: 0 },
      ],
    },
    {
      id: "p-users", mood: "grr", badge: "⚡ Odźwierna", title: "Użytkownicy, grupy, uprawnienia",
      intro: "Nowi użytkownicy, grupy, chmod liczbami i chown.",
      lessons: [
        { title: "Użytkownicy i grupy", blocks: [
          { cmd: "sudo useradd -m -G wheel -s /bin/bash sister && sudo passwd sister", noRun: true, note: "Nowy użytkownik z folderem domowym i prawem do sudo (grupa wheel)." },
          { cmd: "groups", note: "W jakich grupach jesteś." },
          { cmd: "sudo usermod -aG docker $USER", noRun: true, note: "Dodaj siebie do grupy. -a jest konieczne, inaczej wypadniesz z pozostałych grup! Zmiany po ponownym zalogowaniu." },
          { p: "Grupy dają dostęp do urządzeń i funkcji: <code>wheel</code> — sudo, <code>libvirt</code> — maszyny wirtualne, <code>docker</code> — Docker." },
        ] },
        { title: "chmod liczbami i chown", blocks: [
          { p: "Uprawnienia można zapisać cyframi: r=4, w=2, x=1, sumowane dla właściciela, grupy i pozostałych." },
          { table: { head: ["Liczba", "Uprawnienia", "Do czego"], rows: [
            ["<code>755</code>", "rwxr-xr-x", "Skrypty i foldery"], ["<code>644</code>", "rw-r--r--", "Zwykłe pliki"],
            ["<code>600</code>", "rw-------", "Sekrety: klucze SSH, hasła"], ["<code>700</code>", "rwx------", "Prywatny folder"],
          ] } },
          { cmd: "chmod 600 ~/.ssh/id_ed25519" },
          { cmd: "sudo chown -R $USER:$USER ~/Games", note: "Odzyskaj folder, który przypadkiem utworzyłeś(-aś) przez sudo." },
          { say: "Klasyka: pliki utworzone przez sudo, a potem „Permission denied” we własnym folderze. Leczy to jeden chown. Nie rób chmod 777, to jak zostawić drzwi otworem 😤" },
        ] },
      ],
      quiz: [
        { q: "Co znaczą uprawnienia 644?", a: ["Właściciel czyta i pisze, pozostali tylko czytają", "Wszyscy mogą wszystko", "Nikt nic"], ok: 0 },
        { q: "Dlaczego usermod potrzebuje -a razem z -G?", a: ["Bez -a wypadniesz z pozostałych grup", "To przyspiesza polecenie", "Bez -a użytkownik zostanie usunięty"], ok: 0 },
        { q: "Która grupa daje prawo do sudo w Arch i FurrOS?", a: ["wheel", "users", "audio"], ok: 0 },
      ],
    },
    {
      id: "p-net", mood: "wave", badge: "⚡ Sieciowiec", title: "Sieć od środka",
      intro: "Adresy IP, ping, kto nasłuchuje na portach, curl i pobieranie.",
      lessons: [
        { title: "Diagnostyka", blocks: [
          { cmd: "ip -br a", note: "Interfejsy sieciowe i ich adresy IP, w skrócie." },
          { cmd: "ping -c 4 archlinux.org", note: "Czy jest łączność. Jeśli IP odpowiada (ping 1.1.1.1), a nazwa nie — problem z DNS." },
          { cmd: "ip route", note: "Przez który router idzie internet (linia default)." },
          { cmd: "sudo ss -tulpn", note: "Które programy nasłuchują na portach twojego komputera." },
          { cmd: "resolvectl status", note: "Jakie serwery DNS są używane." },
        ] },
        { title: "Pobieranie z terminala", blocks: [
          { cmd: "curl -LO https://example.com/file.iso", noRun: true, note: "-L podążaj za przekierowaniami, -O zapisz pod oryginalną nazwą." },
          { cmd: "curl -s ifconfig.me", note: "Twój zewnętrzny adres IP." },
          { cmd: "sha256sum file.iso", noRun: true, note: "Suma kontrolna: porównaj z tą na stronie. Zgadza się — plik jest cały." },
          { say: "Pobrałeś(-aś) ISO — sprawdź sumę. To dziesięć sekund, a oszczędza godzinę walki z uszkodzonym obrazem 🖤" },
        ] },
      ],
      quiz: [
        { q: "ping 1.1.1.1 działa, a ping archlinux.org nie. Gdzie problem?", a: ["W DNS", "Spaliła się karta sieciowa", "Trzeba przeinstalować system"], ok: 0 },
        { q: "Jak zobaczyć, które programy nasłuchują na portach?", a: ["sudo ss -tulpn", "ls /ports", "pacman -Q"], ok: 0 },
        { q: "Po co sha256sum po pobraniu?", a: ["Sprawdzić, czy plik nie jest uszkodzony ani podmieniony", "Przyspieszyć pobieranie", "Rozpakować plik"], ok: 0 },
      ],
    },
    {
      id: "p-ssh", mood: "hoodie", badge: "⚡ Teleport", title: "SSH: inne komputery",
      intro: "Połączenie z serwerem, klucze zamiast haseł i kopiowanie plików.",
      lessons: [
        { title: "Połączenie i klucze", blocks: [
          { p: "<b>SSH</b> to bezpieczny terminal na innym komputerze: serwerze, Raspberry Pi, drugim PC." },
          { cmd: "ssh user@192.168.1.50", noRun: true },
          { p: "Hasło za każdym razem jest niewygodne i mniej bezpieczne. Zrób parę kluczy: prywatny zostaje u ciebie, publiczny idzie na serwer." },
          { cmd: "ssh-keygen -t ed25519", note: "Na pytania można wciskać Enter. Hasło do klucza (passphrase) to dobry pomysł." },
          { cmd: "ssh-copy-id user@192.168.1.50", noRun: true, note: "Wyślij klucz publiczny na serwer. Potem logowanie bez hasła." },
          { warn: "Plik <code>~/.ssh/id_ed25519</code> bez .pub to twój klucz prywatny. Nikomu go nie wysyłaj, tak jak hasła." },
        ] },
        { title: "Pliki i wygoda", blocks: [
          { cmd: "scp photo.png user@192.168.1.50:~/", noRun: true, note: "Skopiuj plik na serwer." },
          { cmd: "rsync -avP ~/Music/ user@192.168.1.50:~/Music/", noRun: true, note: "Synchronizuj folder: kolejnym razem wysyłane są tylko zmiany." },
          { p: "Żeby nie wpisywać adresów, utwórz plik <code>~/.ssh/config</code>:" },
          { cmd: "Host pi\n    HostName 192.168.1.50\n    User furry", noRun: true, note: "Teraz wystarczy ssh pi." },
          { say: "Żeby inni łączyli się z tobą, potrzebny jest serwer: <code>sudo pacman -S openssh && sudo systemctl enable --now sshd</code> i port 22 w zaporze. Nie włączaj, jeśli nie trzeba — mniej drzwi, mniej problemów 🖤" },
        ] },
      ],
      quiz: [
        { q: "Który klucz można dać serwerowi?", a: ["Publiczny (.pub)", "Prywatny (bez .pub)", "Oba"], ok: 0 },
        { q: "Czym skopiować plik na inny komputer przez SSH?", a: ["scp", "cp", "mv"], ok: 0 },
        { q: "Po co ~/.ssh/config?", a: ["Krótkie nazwy i ustawienia dla serwerów", "Przechowywanie haseł otwartym tekstem", "Włączenie serwera SSH"], ok: 0 },
      ],
    },
    {
      id: "p-pacman", mood: "timer", badge: "⚡ Władczyni pacmana", title: "pacman dla dorosłych",
      intro: "Informacje o pakietach, cofanie wersji, IgnorePkg i .pacnew.",
      lessons: [
        { title: "Wszystko o pakietach", blocks: [
          { table: { head: ["Polecenie", "Co robi"], rows: [
            ["<code>pacman -Qi nazwa</code>", "Szczegóły zainstalowanego pakietu (wersja, rozmiar, zależności)"],
            ["<code>pacman -Ql nazwa</code>", "Jakie pliki zainstalował pakiet"],
            ["<code>pacman -Qe</code>", "Co zainstalowałeś(-aś) sam(a), bez zależności"],
            ["<code>pacman -Qdt</code>", "Sieroty: zależności, których nikt już nie potrzebuje"],
            ["<code>pactree nazwa</code>", "Drzewo zależności (pakiet pacman-contrib)"],
            ["<code>expac -H M '%m\\t%n' | sort -h | tail</code>", "Najcięższe pakiety (pakiet expac)"],
          ] } },
        ] },
        { title: "Cofnięcie i blokada", blocks: [
          { p: "Nowa wersja programu się zepsuła? Stara leży w pamięci podręcznej i można ją zainstalować z powrotem:" },
          { cmd: "ls /var/cache/pacman/pkg/ | grep firefox" },
          { cmd: "sudo pacman -U /var/cache/pacman/pkg/firefox-WERSJA-x86_64.pkg.tar.zst", noRun: true },
          { p: "Żeby pacman na razie nie aktualizował tego pakietu, dopisz go w <code>/etc/pacman.conf</code> linią <code>IgnorePkg = firefox</code>. Pamiętaj, by potem usunąć: długie trzymanie starych wersji w Archu jest ryzykowne." },
          { cmd: "sudo pacdiff", note: "Ogarnij pliki .pacnew: porównaj nowy wzór konfiguracji ze swoim i zdecyduj, co zostawić." },
          { say: "Cofnięcie to plaster, a nie lekarstwo. Cofnęłam, zgłosiłam błąd, za parę dni zaktualizowałam. Tak robią zawodowcy 🖤" },
        ] },
      ],
      quiz: [
        { q: "Jak zobaczyć pliki zainstalowane przez pakiet?", a: ["pacman -Ql nazwa", "pacman -Ss nazwa", "pacman -R nazwa"], ok: 0 },
        { q: "Gdzie leżą stare wersje pakietów do cofnięcia?", a: ["/var/cache/pacman/pkg", "/tmp", "~/Downloads"], ok: 0 },
        { q: "Co robi pacdiff?", a: ["Pomaga ogarnąć pliki .pacnew", "Usuwa pacmana", "Porównuje dwa systemy"], ok: 0 },
      ],
    },
    {
      id: "p-aur", mood: "grr", badge: "⚡ Budowniczka", title: "AUR własnymi rękami",
      intro: "Co jest w PKGBUILD, makepkg i jak nie złapać szkodliwego pakietu.",
      lessons: [
        { title: "Budowanie bez pomocnika", blocks: [
          { p: "yay robi to za ciebie, ale warto rozumieć, co się dzieje. Pakiet w AUR to nie program, tylko <b>przepis</b>: plik PKGBUILD, według którego program budowany jest u ciebie." },
          { cmd: "sudo pacman -S --needed base-devel git" },
          { cmd: "git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin" },
          { cmd: "less PKGBUILD", note: "Najpierw czytamy przepis! Patrz na source (skąd pobiera) i na polecenia w package()." },
          { cmd: "makepkg -si", note: "Zbuduj i zainstaluj (z zależnościami). Nigdy nie uruchamiaj makepkg przez sudo." },
        ] },
        { title: "Jak nie wpaść", blocks: [
          { ul: [
            "Patrz na liczbę głosów i popularność na aur.archlinux.org.",
            "Sprawdź datę ostatniej aktualizacji i komentarze: tam pisze się o problemach.",
            "W PKGBUILD podejrzane jest wszystko, co pobiera pliki z dziwnych stron albo robi <code>curl … | sh</code>.",
            "Przy aktualizacji yay pokazuje diff przepisu. Czytaj go, zwłaszcza przy mało znanych pakietach.",
          ] },
          { cmd: "yay -Sua", note: "Zaktualizuj tylko pakiety z AUR." },
          { say: "AUR to targowisko: są tam świetne rzeczy i podejrzane. Pakiet z pięcioma głosami i przepisem, który ściąga coś z hostingu plików? Odpada 😤" },
        ] },
      ],
      quiz: [
        { q: "Czym jest PKGBUILD?", a: ["Przepisem na zbudowanie pakietu", "Gotowym programem", "Logami pacmana"], ok: 0 },
        { q: "Czy można uruchamiać makepkg przez sudo?", a: ["Nie, makepkg uruchamia zwykły użytkownik", "Tak, tak trzeba", "Tylko w piątki"], ok: 0 },
        { q: "Co jest podejrzane w PKGBUILD?", a: ["Pobieranie z dziwnych stron i curl | sh", "Komentarze", "Pole pkgver"], ok: 0 },
      ],
    },
    {
      id: "p-archive", mood: "hoodie", badge: "⚡ Pakowaczka", title: "Archiwa i kompresja",
      intro: "tar, zip, zstd i 7z: spakować, rozpakować, zajrzeć do środka.",
      lessons: [
        { title: "tar i przyjaciele", blocks: [
          { p: "<b>tar</b> skleja wiele plików w jeden, a kompresują go gzip, xz albo zstd. Zapamiętaj litery: <b>c</b> utwórz, <b>x</b> rozpakuj, <b>t</b> pokaż, <b>f</b> plik, <b>v</b> szczegółowo." },
          { cmd: "tar -czf backup.tar.gz ~/Documents", note: "Spakuj z gzip." },
          { cmd: "tar --zstd -cf backup.tar.zst ~/Documents", note: "zstd: szybszy i zwykle lepiej kompresuje. Nim skompresowane są też pakiety Archa." },
          { cmd: "tar -xf backup.tar.gz -C ~/restore", note: "Rozpakuj do folderu (tar sam rozpozna kompresję)." },
          { cmd: "tar -tf backup.tar.gz | head", note: "Zobacz, co jest w środku, bez rozpakowywania." },
        ] },
        { title: "zip, 7z i rar", blocks: [
          { cmd: "zip -r photos.zip ~/Pictures", note: "zip rozumie każdy system — wygodnie wysłać znajomym na Windowsie." },
          { cmd: "unzip photos.zip -d photos" },
          { cmd: "sudo pacman -S 7zip && 7z x archive.7z", note: "7z rozpakuje prawie wszystko, także .rar." },
          { say: "Menedżery plików też obsługują archiwa: prawy klik → „Kompresuj” albo „Rozpakuj”. Terminal — gdy trzeba dużo i szybko 🖤" },
        ] },
      ],
      quiz: [
        { q: "Która litera w tar oznacza „rozpakuj”?", a: ["x", "c", "z"], ok: 0 },
        { q: "Jak zobaczyć zawartość archiwum bez rozpakowywania?", a: ["tar -tf archiwum", "tar -xf archiwum", "cat archiwum"], ok: 0 },
        { q: "Jaki format najwygodniej wysłać znajomemu na Windowsie?", a: ["zip", "tar.zst", "pkg.tar.zst"], ok: 0 },
      ],
    },
    {
      id: "p-script", mood: "wave", badge: "⚡ Skrypciara", title: "Własne skrypty",
      intro: "shebang, zmienne, warunki, pętle, argumenty i zakończenie poziomu Pixie.",
      lessons: [
        { title: "Pierwszy skrypt", blocks: [
          { p: "Skrypt to plik tekstowy z poleceniami. Pierwsza linia (<b>shebang</b>) mówi, czym go uruchamiać:" },
          { cmd: "#!/bin/bash\nset -euo pipefail\nname=${1:-przyjacielu}\necho \"Cześć, $name! Dziś jest $(date +%A)\"", noRun: true, note: "set -euo pipefail: zatrzymaj się przy pierwszym błędzie. $1 to pierwszy argument, :-przyjacielu — wartość domyślna. $(…) wstawia wynik polecenia." },
          { cmd: "nano ~/.local/bin/hello && chmod +x ~/.local/bin/hello", note: "Utwórz skrypt i nadaj mu prawo uruchamiania. Potem po prostu: hello Pixie" },
        ] },
        { title: "Warunki i pętle", blocks: [
          { cmd: "if [ -f ~/.bashrc ]; then\n  echo \"bashrc jest\"\nelse\n  echo \"brak bashrc\"\nfi", noRun: true, note: "-f plik istnieje, -d folder, -z pusty napis. Spacje wewnątrz [ ] są obowiązkowe!" },
          { cmd: "for f in ~/Pictures/*.png; do\n  echo \"Znalazłam: $f\"\ndone", noRun: true },
          { p: "Przykład z życia: zmień nazwy wszystkich zrzutów ekranu, dodając datę:" },
          { cmd: "for f in Screenshot*.png; do mv -- \"$f\" \"$(date +%F)-$f\"; done", noRun: true },
          { tip: "Sprawdzaj skrypty programem <b>shellcheck</b> (<code>sudo pacman -S shellcheck</code>): znajdzie błędy, które inaczej wyskoczą w najgorszym momencie." },
          { say: "Gotowe, ukończyłeś(-aś) mój poziom! Łączysz polecenia, zarządzasz usługami, chodzisz po SSH i piszesz skrypty. Dalej czeka Danyok, i chyba ma cytrynę 🍋🖤", mood: "lying" },
        ] },
      ],
      quiz: [
        { q: "Co to jest shebang?", a: ["Pierwsza linia #!, która mówi, czym uruchomić skrypt", "Błąd basha", "Komentarz na końcu"], ok: 0 },
        { q: "Co przechowuje $1?", a: ["Pierwszy argument skryptu", "Cenę skryptu", "Numer linii"], ok: 0 },
        { q: "Co robi set -e?", a: ["Zatrzymuje skrypt przy pierwszym błędzie", "Włącza emoji", "Usuwa zmienne"], ok: 0 },
      ],
    },
  ] },

  danyok: { chapters: [
    {
      id: "d-boot", mood: "wave", badge: "🍋 Bootloader", title: "Jak uruchamia się Linux",
      intro: "UEFI, menu startowe FurrBoot, jądro, initramfs i systemd: co się dzieje po wciśnięciu przycisku zasilania.",
      lessons: [
        { title: "Łańcuch rozruchu", blocks: [
          { ol: [
            "<b>UEFI</b> (firmware płyty) znajduje partycję EFI i uruchamia z niej bootloader.",
            "<b>FurrBoot</b> pokazuje menu FurrOS i ładuje do pamięci <b>jądro</b> (vmlinuz) oraz <b>initramfs</b>. Stare komputery bez UEFI dostają zamiast niego Limine, a zapasowy GRUB jest zawsze w menu rozruchu płyty (F11/F12/F8).",
            "<b>initramfs</b> to mały tymczasowy system: ma sterowniki, by znaleźć i zamontować prawdziwą partycję główną (Btrfs, szyfrowanie, NVMe).",
            "Jądro uruchamia <b>systemd</b> (PID 1), a ten — wszystkie usługi i ekran logowania.",
          ] },
          { cmd: "systemd-analyze", note: "Ile trwał każdy etap rozruchu." },
          { cmd: "systemd-analyze blame | head", note: "Które usługi uruchamiają się najdłużej." },
        ] },
        { title: "Parametry jądra i initramfs", blocks: [
          { p: "Parametry jądra ustawia się w pliku <code>/etc/kernel/cmdline</code>. Po zmianie odśwież menu startowe:" },
          { cmd: "sudo furrboot-update" },
          { p: "Zapasowy GRUB ma własne ustawienia: <code>/etc/default/grub</code>, potem <code>sudo grub-mkconfig -o /boot/grub/grub.cfg</code>." },
          { cmd: "cat /proc/cmdline", note: "Z jakimi parametrami jądro jest uruchomione teraz." },
          { p: "Skład initramfs ustawia się w <code>/etc/mkinitcpio.conf</code> (linie MODULES i HOOKS). Po zmianie przebuduj:" },
          { cmd: "sudo mkinitcpio -P" },
          { say: "Raz w menu FurrBoot wciśnij <kbd>E</kbd> — zobaczysz linię rozruchu i dodasz parametr tylko na ten raz. To ratuje, gdy system nie startuje z nowymi ustawieniami. A jeśli nowe jądro trzy razy z rzędu się nie uruchomi, FurrBoot sam włączy zapasowe. Cytryna zatwierdza 🍋" },
        ] },
      ],
      quiz: [
        { q: "Czym jest initramfs?", a: ["Małym tymczasowym systemem, który montuje prawdziwy korzeń", "Plikiem wymiany", "Menu startowe"], ok: 0 },
        { q: "Co uruchamia się jako pierwszy proces (PID 1)?", a: ["systemd", "GRUB", "bash"], ok: 0 },
        { q: "Co zrobić po zmianie /etc/kernel/cmdline?", a: ["sudo furrboot-update", "Nic", "sudo pacman -Syu"], ok: 0 },
      ],
    },
    {
      id: "d-kernel", mood: "hoodie", badge: "🍋 Jądrowiec", title: "Jądro i moduły",
      intro: "Wersje jąder, moduły, czarna lista, DKMS i sysctl.",
      lessons: [
        { title: "Jądra i moduły", blocks: [
          { cmd: "uname -r", note: "Wersja bieżącego jądra." },
          { p: "Arch ma kilka jąder: <code>linux</code> (najnowsze), <code>linux-lts</code> (długoterminowe, zapasowe), <code>linux-zen</code> (strojone pod responsywność). FurrOS ma też własne — <code>linux-furros</code>. Można trzymać dwa: menu startowe odświeży się samo, a drugie jądro będzie w pozycji «Inne jądro»." },
          { cmd: "sudo pacman -S linux-lts linux-lts-headers", noRun: true, note: "Zapasowe jądro: jeśli nowe coś zepsuje, uruchomisz LTS." },
          { cmd: "lsmod | head", note: "Załadowane moduły (sterowniki)." },
          { cmd: "modinfo btusb", note: "Co to za moduł i jakie ma parametry." },
        ] },
        { title: "Czarna lista, DKMS, sysctl", blocks: [
          { p: "Moduł przeszkadza (np. wadliwy sterownik kamerki)? Zablokuj go:" },
          { cmd: "echo 'blacklist uvcvideo' | sudo tee /etc/modprobe.d/no-webcam.conf", noRun: true },
          { p: "<b>DKMS</b> przebudowuje zewnętrzne moduły (np. nvidia-580xx) pod każde nowe jądro. Do tego potrzebne są nagłówki: <code>linux-headers</code> dla każdego zainstalowanego jądra." },
          { cmd: "dkms status" },
          { p: "<b>sysctl</b> zmienia parametry jądra w locie. Stałe — w plikach <code>/etc/sysctl.d/*.conf</code>:" },
          { cmd: "sysctl vm.swappiness" },
          { say: "Rada warta milion cytryn: trzymaj <code>linux-lts</code> jako zapasowe jądro. Zajmuje grosze miejsca, a w zły dzień ratuje cały system 🍋" },
        ] },
      ],
      quiz: [
        { q: "Po co trzymać linux-lts obok linux?", a: ["Zapasowe jądro, gdy nowe coś zepsuje", "Żeby gry szły szybciej", "To wymagane dla Wi-Fi"], ok: 0 },
        { q: "Co robi DKMS?", a: ["Przebudowuje zewnętrzne moduły pod nowe jądro", "Usuwa stare jądra", "Aktualizuje BIOS"], ok: 0 },
        { q: "Gdzie trzymać stałe ustawienia sysctl?", a: ["/etc/sysctl.d/*.conf", "~/.bashrc", "/boot/grub"], ok: 0 },
      ],
    },
    {
      id: "d-btrfs", mood: "timer", badge: "🍋 Mistrz Btrfs", title: "Btrfs na poważnie",
      intro: "Podwoluminy, migawki, kompresja, scrub i ile miejsca naprawdę zajęte.",
      lessons: [
        { title: "Podwoluminy i migawki", blocks: [
          { p: "FurrOS na Btrfs tworzy <b>podwoluminy</b>: <code>@</code> (system), <code>@home</code>, <code>@log</code>, <code>@pkg</code>. Migawkę robi się dla podwoluminu, więc cofnięcie systemu nie rusza twoich plików w home." },
          { cmd: "sudo btrfs subvolume list /" },
          { cmd: "sudo snapper -c root list", note: "Migawki systemu. Działają na zasadzie kopiowania przy zapisie: prawie nie zajmują miejsca, dopóki pliki się nie zmieniają." },
          { cmd: "sudo snapper -c root create -d \"przed eksperymentem\"", note: "Ręczna migawka przed ryzykownymi zmianami." },
          { cmd: "sudo snapper -c root status 41..42", noRun: true, note: "Co się zmieniło między dwiema migawkami." },
        ] },
        { title: "Kompresja i zdrowie", blocks: [
          { p: "FurrOS montuje Btrfs z kompresją zstd: pliki zajmują mniej miejsca, a często nawet szybciej się czytają." },
          { cmd: "sudo pacman -S compsize && sudo compsize /usr", note: "Ile naprawdę oszczędza kompresja." },
          { cmd: "sudo btrfs filesystem usage /", note: "Dokładny obraz miejsca (df na Btrfs kłamie)." },
          { cmd: "sudo btrfs scrub start / && sudo btrfs scrub status /", note: "Sprawdź wszystkie dane po sumach kontrolnych. Warto raz w miesiącu." },
          { warn: "<code>btrfs check --repair</code> to ostateczność, tylko na radę znających się ludzi i z kopią zapasową. Można nim pogorszyć sprawę." },
          { say: "Migawka to nie kopia zapasowa. Leży na tym samym dysku. Dysk padł — migawki padły razem z nim. Kopia — na innym dysku, cytryna — w lodówce 🍋" },
        ] },
      ],
      quiz: [
        { q: "Dlaczego cofnięcie systemu nie rusza plików w home?", a: ["home to osobny podwolumin @home", "Snapper nie umie cofać", "Pliki w home są tylko do odczytu"], ok: 0 },
        { q: "Czym sprawdzić dane Btrfs po sumach kontrolnych?", a: ["btrfs scrub", "fsck.vfat", "rm -rf"], ok: 0 },
        { q: "Czy migawki zastępują kopię zapasową?", a: ["Nie, migawki są na tym samym dysku", "Tak, całkowicie", "Tylko na SSD"], ok: 0 },
      ],
    },
    {
      id: "d-units", mood: "hoodie", badge: "🍋 Służbista", title: "Własne usługi i timery",
      intro: "Piszemy pliki unit, poprawki drop-in i timery zamiast crona.",
      lessons: [
        { title: "Własna usługa", blocks: [
          { p: "Usługę opisuje plik <b>unit</b>. Własne systemowe kładzie się w <code>/etc/systemd/system/</code>, użytkownika — w <code>~/.config/systemd/user/</code>." },
          { cmd: "[Unit]\nDescription=Mój bot\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nExecStart=/home/furry/bot/run.sh\nRestart=on-failure\n\n[Install]\nWantedBy=default.target", noRun: true, note: "~/.config/systemd/user/bot.service — bot, który restartuje się po awarii." },
          { cmd: "systemctl --user daemon-reload && systemctl --user enable --now bot", noRun: true },
          { cmd: "loginctl enable-linger $USER", noRun: true, note: "Żeby usługi użytkownika działały, nawet gdy nie jesteś zalogowany(-a)." },
        ] },
        { title: "Poprawki i timery", blocks: [
          { p: "Systemowych plików unit nie edytuje się bezpośrednio (aktualizacja je nadpisze). Zamiast tego robi się <b>drop-in</b>:" },
          { cmd: "sudo systemctl edit sddm", noRun: true, note: "Otworzy edytor pliku-dodatku. Wszystko, co tam napiszesz, przetrwa aktualizacje." },
          { p: "Timer to para .timer i .service o tej samej nazwie:" },
          { cmd: "[Timer]\nOnCalendar=daily\nPersistent=true\n\n[Install]\nWantedBy=timers.target", noRun: true, note: "backup.timer: raz dziennie uruchamia backup.service. Persistent — nadrobi pominięte uruchomienie, jeśli PC był wyłączony." },
          { cmd: "systemd-analyze calendar \"Mon *-*-* 10:00\"", note: "Sprawdź harmonogram: kiedy zadziała następnym razem." },
          { say: "Timery są lepsze od crona: wszystko widać w <code>systemctl list-timers</code>, logi są w journalctl, a pominięte uruchomienia się nadrabiają. Kwaśna rada, ale prawdziwa 🍋" },
        ] },
      ],
      quiz: [
        { q: "Gdzie trzymać własne usługi użytkownika?", a: ["~/.config/systemd/user/", "/boot", "/tmp"], ok: 0 },
        { q: "Jak poprawnie zmienić usługę systemową?", a: ["sudo systemctl edit nazwa (drop-in)", "Edytować plik w /usr/lib/systemd bezpośrednio", "Nijak"], ok: 0 },
        { q: "Co robi Persistent=true w timerze?", a: ["Nadrabia pominięte uruchomienie", "Zabrania zatrzymania", "Uruchamia co sekundę"], ok: 0 },
      ],
    },
    {
      id: "d-net", mood: "wave", badge: "🍋 Admin sieci", title: "Sieć od podszewki",
      intro: "NetworkManager z terminala, DNS, /etc/hosts, reguły ufw i VPN, który działa nawet przy blokadach.",
      lessons: [
        { title: "Połączenia i DNS", blocks: [
          { cmd: "nmcli connection show" },
          { cmd: "nmcli connection modify \"Moja sieć\" ipv4.dns \"1.1.1.1 9.9.9.9\" ipv4.ignore-auto-dns yes", noRun: true, note: "Własny DNS dla jednej sieci. Zastosuj: nmcli connection up \"Moja sieć\"." },
          { p: "<code>/etc/hosts</code> to lokalna „książka telefoniczna”: nazwa → IP. Wygodne dla domowych serwerów:" },
          { cmd: "192.168.1.50  pi.home", noRun: true, note: "Linia w /etc/hosts. Teraz ssh furry@pi.home." },
        ] },
        { title: "Zapora i VPN", blocks: [
          { cmd: "sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp", noRun: true, note: "SSH tylko z sieci domowej." },
          { cmd: "sudo ufw status numbered", note: "Reguły z numerami; usuń: sudo ufw delete N." },
          { p: "<b>VPN szczerze:</b> zwykły <b>WireGuard</b> jest wbudowany w jądro i bardzo szybki, ale w Rosji (tak jak OpenVPN) często jest blokowany: blokady rozpoznają sam protokół. Działa tam, gdzie go nie blokują, np. do łączenia się z własnym serwerem w domu. Konfiguracja trafia do <code>/etc/wireguard/wg0.conf</code>:" },
          { cmd: "sudo pacman -S wireguard-tools && sudo wg-quick up wg0", noRun: true, note: "Rozłącz: sudo wg-quick down wg0." },
          { p: "Jeśli WireGuard się nie łączy, potrzebny jest protokół z maskowaniem. <b>AmneziaWG</b> to fork WireGuarda, który ukrywa rozpoznawalne pakiety. Najprościej przez aplikację <b>AmneziaVPN</b> z AUR: wklejasz klucz lub konfigurację od swojego dostawcy VPN (albo własnego serwera z Amnezią) i klikasz Połącz:" },
          { cmd: "yay -S amneziavpn-bin", noRun: true, note: "Do terminala jest amneziawg-tools + amneziawg-dkms (AUR): konfiguracja w /etc/amnezia/amneziawg/awg0.conf, uruchomienie: sudo awg-quick up awg0." },
          { p: "Jeśli dostawca daje <b>subskrypcję VLESS / Reality</b> (link vless://… albo adres subskrypcji), potrzebny jest klient do niej: <b>Throne</b> (dawniej NekoRay) albo <b>Hiddify</b>. Oba są w AUR, wklejasz link i gotowe:" },
          { cmd: "yay -S throne-bin", noRun: true, note: "Albo yay -S hiddify. Pakiety z AUR robią ludzie, nie Arch: sprawdzaj, co instalujesz, i bierz klucze tylko od swojego dostawcy." },
          { say: "Reguła zapory jest jak zamek: pisz najwęższą, która działa. „Otwórz wszystko wszystkim” to nie ustawienie, to lemoniada zamiast cytryny 🍋" },
        ] },
      ],
      quiz: [
        { q: "Do czego służy /etc/hosts?", a: ["Lokalne przypisanie nazw do adresów IP", "Przechowywanie haseł Wi-Fi", "Lista pakietów"], ok: 0 },
        { q: "Jak pozwolić na SSH tylko z sieci domowej?", a: ["ufw allow from 192.168.1.0/24 to any port 22", "ufw disable", "ufw allow 22 dla wszystkich"], ok: 0 },
        { q: "WireGuard nie łączy się przez blokady. Co spróbować?", a: ["AmneziaWG (aplikacja AmneziaVPN) albo klient VLESS/Reality", "Przeinstalować jądro", "Wyłączyć zaporę"], ok: 0 },
      ],
    },
    {
      id: "d-sshd", mood: "grr", badge: "🍋 Pan serwera", title: "Własny serwer SSH",
      intro: "Logowanie tylko kluczami, bez roota, i tunele.",
      lessons: [
        { title: "Dokręcamy śruby", blocks: [
          { cmd: "sudo pacman -S openssh && sudo systemctl enable --now sshd", noRun: true },
          { p: "Ustawienia — w <code>/etc/ssh/sshd_config.d/</code> (własny plik, np. <code>10-furros.conf</code>):" },
          { cmd: "PermitRootLogin no\nPasswordAuthentication no\nKbdInteractiveAuthentication no", noRun: true, note: "Tylko klucze, żadnego roota. Najpierw upewnij się, że logowanie kluczem działa!" },
          { cmd: "sudo sshd -t && sudo systemctl reload sshd", noRun: true, note: "sshd -t sprawdza konfigurację. Błąd w niej może odciąć ci dostęp." },
          { warn: "Edytujesz SSH na zdalnym serwerze? Trzymaj otwartą drugą sesję, dopóki nie sprawdzisz nowego logowania. Inaczej możesz zamknąć się na zewnątrz." },
        ] },
        { title: "Tunele", blocks: [
          { cmd: "ssh -L 8080:localhost:80 user@server", noRun: true, note: "Panel WWW serwera (port 80) otworzy się u ciebie na localhost:8080. Nic nie trzeba wystawiać do internetu." },
          { cmd: "ssh -D 1080 user@server", noRun: true, note: "Proxy SOCKS przez serwer." },
          { cmd: "sudo journalctl -u sshd | grep -i failed | tail", note: "Kto próbował zgadnąć hasło." },
          { say: "Serwer z hasłem i otwartym portem 22 zaczynają atakować kilka minut po starcie. Klucze — i boty mogą sobie odpocząć w kącie. Z cytryną 🍋" },
        ] },
      ],
      quiz: [
        { q: "Co zrobić przed PasswordAuthentication no?", a: ["Upewnić się, że logowanie kluczem działa", "Usunąć klucze", "Wyłączyć zaporę"], ok: 0 },
        { q: "Jak sprawdzić konfigurację sshd pod kątem błędów?", a: ["sudo sshd -t", "ssh -v", "cat sshd"], ok: 0 },
        { q: "Co robi ssh -L 8080:localhost:80?", a: ["Przekierowuje port serwera do ciebie", "Otwiera port do internetu", "Usuwa port 80"], ok: 0 },
      ],
    },
    {
      id: "d-perf", mood: "timer", badge: "🍋 Podkręcacz", title: "Wydajność",
      intro: "Gdzie zwalnia: procesor, pamięć, dysk. zram, governor i temperatury.",
      lessons: [
        { title: "Znaleźć wąskie gardło", blocks: [
          { table: { head: ["Narzędzie", "Co pokazuje"], rows: [
            ["<code>btop</code>", "Wszystko naraz, ładnie: CPU, pamięć, dyski, sieć, procesy"],
            ["<code>sudo iotop</code>", "Kto obciąża dysk"], ["<code>free -h</code>", "Pamięć i swap"],
            ["<code>sensors</code>", "Temperatury (pakiet lm_sensors)"], ["<code>nvtop</code>", "Obciążenie karty graficznej"],
            ["<code>journalctl -k -p 4</code>", "Ostrzeżenia jądra: przegrzanie, błędy dysków"],
          ] } },
          { cmd: "sudo pacman -S btop lm_sensors nvtop iotop" },
        ] },
        { title: "Pamięć i procesor", blocks: [
          { p: "<b>zram</b> to skompresowany swap prosto w pamięci: przy braku RAM system zwalnia o wiele mniej niż ze swapem na dysku." },
          { cmd: "zramctl", note: "Czy jest zram. Konfiguracja: pakiet zram-generator i /etc/systemd/zram-generator.conf." },
          { p: "<b>Governor</b> decyduje, jak szybko procesor podnosi taktowanie:" },
          { cmd: "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" },
          { cmd: "powerprofilesctl set performance", noRun: true, note: "Profil wydajności (albo balanced / power-saver). Wygodne przed grą; na laptopie kosztuje baterię." },
          { say: "Najpierw zmierz, potem kręć. „Tweak z internetu” bez pomiarów to wróżenie z pestek cytryny 🍋" },
        ] },
      ],
      quiz: [
        { q: "Czym jest zram?", a: ["Skompresowanym swapem w pamięci RAM", "Nowym rodzajem SSD", "Sterownikiem karty graficznej"], ok: 0 },
        { q: "Czym sprawdzić, kto obciąża dysk?", a: ["iotop", "ping", "ls"], ok: 0 },
        { q: "Co zrobić przed tweakami wydajności?", a: ["Zmierzyć, gdzie jest wąskie gardło", "Od razu zmieniać wszystko", "Przeinstalować system"], ok: 0 },
      ],
    },
    {
      id: "d-gpu", mood: "wave", badge: "🍋 Czarodziej grafiki", title: "Grafika: Wayland, X11, sterowniki",
      intro: "Mesa i NVIDIA, Wayland kontra X11, grafika hybrydowa i sprawdzanie Vulkana.",
      lessons: [
        { title: "Kto rysuje obraz", blocks: [
          { p: "<b>Mesa</b> to otwarte sterowniki dla AMD i Intela, są już w jądrze i działają od razu. Dla NVIDIA: <code>nvidia-open</code> (RTX i GTX 16xx) albo <code>nvidia-580xx</code> z [furros] (GTX 750–10xx). Co jest zainstalowane: <code>furros-drivers</code>." },
          { cmd: "echo $XDG_SESSION_TYPE", note: "wayland albo x11: na czym działa sesja." },
          { cmd: "sudo pacman -S vulkan-tools mesa-utils && vulkaninfo --summary && glxinfo -B", noRun: true, note: "Jaka karta i jaki sterownik obsługują Vulkan i OpenGL." },
          { p: "<b>Wayland</b> to nowy protokół graficzny: płynniejszy, bezpieczniejszy, lepszy z różnymi częstotliwościami monitorów. <b>X11</b> jest stary, ale niektóre programy wciąż żyją tylko w nim. W Waylandzie działają przez <b>Xwayland</b>." },
        ] },
        { title: "Grafika hybrydowa i NVIDIA", blocks: [
          { p: "Laptop z dwiema kartami: domyślnie pracuje zintegrowana (oszczędza baterię), a ciężkie rzeczy uruchamia się na dedykowanej:" },
          { cmd: "prime-run steam", noRun: true, note: "Pakiet nvidia-prime. Dla AMD+AMD: DRI_PRIME=1 program." },
          { cmd: "cat /sys/module/nvidia_drm/parameters/modeset", note: "Y — tryb potrzebny dla Waylanda z NVIDIA jest włączony." },
          { say: "Czarny ekran na NVIDIA po aktualizacji? Prawie zawsze sterownik nie pasuje do jądra. Konsola (Ctrl+Alt+F3), <code>sudo pacman -Syu</code>, restart. Albo zapasowe jądro LTS 🍋" },
        ] },
      ],
      quiz: [
        { q: "Jak sprawdzić, czy masz Wayland czy X11?", a: ["echo $XDG_SESSION_TYPE", "uname -r", "ls /wayland"], ok: 0 },
        { q: "Czym jest Xwayland?", a: ["Sposobem uruchamiania programów X11 w Waylandzie", "Nowym pulpitem", "Sterownikiem NVIDIA"], ok: 0 },
        { q: "Jak uruchomić program na dedykowanej NVIDIA w laptopie?", a: ["prime-run program", "sudo program", "nvidia program --fast"], ok: 0 },
      ],
    },
    {
      id: "d-pkg", mood: "hoodie", badge: "🍋 Pakieciarz", title: "Własny pakiet i repozytorium",
      intro: "Piszemy PKGBUILD, sprawdzamy namcapem i budujemy własne repozytorium.",
      lessons: [
        { title: "PKGBUILD od zera", blocks: [
          { p: "Własny skrypt czy program lepiej instalować jako pakiet: pacman zna jego pliki, zaktualizuje go i czysto usunie." },
          { cmd: "pkgname=lemon-timer\npkgver=1.0\npkgrel=1\npkgdesc=\"Minutnik z cytryną\"\narch=(any)\nlicense=(MIT)\ndepends=(bash libnotify)\nsource=(lemon-timer)\nsha256sums=(SKIP)\n\npackage() {\n  install -Dm755 lemon-timer \"$pkgdir/usr/bin/lemon-timer\"\n}", noRun: true, note: "PKGBUILD obok skryptu lemon-timer." },
          { cmd: "makepkg -si", noRun: true },
          { cmd: "namcap PKGBUILD *.pkg.tar.zst", noRun: true, note: "Sprawdza typowe błędy: zależności, uprawnienia, ścieżki." },
          { tip: "Zamiast SKIP wstaw prawdziwe sumy: <code>updpkgsums</code> (pakiet pacman-contrib) policzy je sam." },
        ] },
        { title: "Własne repozytorium", blocks: [
          { p: "Kilka własnych pakietów na kilka komputerów najwygodniej trzymać w repozytorium, tak jak FurrOS ze swoim [furros]:" },
          { cmd: "repo-add ~/repo/lemon.db.tar.zst ~/repo/*.pkg.tar.zst", noRun: true },
          { cmd: "[lemon]\nSigLevel = Optional TrustAll\nServer = file:///home/furry/repo", noRun: true, note: "Sekcja w /etc/pacman.conf. Dla innych ludzi pakiety się podpisuje (gpg + makepkg --sign) i ustawia SigLevel = Required." },
          { say: "Właśnie tak FurrOS dostarcza ci tapety, Szkołę Lapy i sterowniki: podpisane pakiety w repozytorium [furros], aktualizowane zwykłym <code>pacman -Syu</code> 🍋" },
        ] },
      ],
      quiz: [
        { q: "Gdzie package() kładzie pliki?", a: ["Do $pkgdir, który potem staje się pakietem", "Prosto do /usr", "Do folderu domowego"], ok: 0 },
        { q: "Czym sprawdzić pakiet pod kątem typowych błędów?", a: ["namcap", "ping", "grep"], ok: 0 },
        { q: "Które polecenie tworzy bazę repozytorium?", a: ["repo-add", "pacman -Syu", "mkinitcpio"], ok: 0 },
      ],
    },
    {
      id: "d-containers", mood: "wave", badge: "🍋 Kontenerowiec", title: "Kontenery",
      intro: "Podman i Docker, distrobox dla programów z innych dystrybucji, uprawnienia Flatpaka.",
      lessons: [
        { title: "Podman i Docker", blocks: [
          { p: "Kontener to odizolowane pudełko z własnym minisystemem. Program w nim nie przeszkadza głównemu systemowi i usuwa się go jednym poleceniem." },
          { cmd: "sudo pacman -S podman && podman run --rm -it archlinux bash", noRun: true, note: "Czysty Arch w kontenerze. --rm — usuń po wyjściu. Podman działa bez roota." },
          { cmd: "podman ps -a && podman images", noRun: true, note: "Kontenery i obrazy. Sprzątanie: podman system prune." },
          { p: "Docker działa podobnie (<code>sudo pacman -S docker && sudo systemctl enable --now docker</code>), ale przez usługę roota." },
        ] },
        { title: "distrobox i Flatpak", blocks: [
          { p: "<b>distrobox</b> uruchamia inną dystrybucję w kontenerze, ale z twoim folderem domowym, dźwiękiem i grafiką. Program, który jest tylko dla Ubuntu? Żaden problem:" },
          { cmd: "sudo pacman -S distrobox podman && distrobox create -n ubuntu -i ubuntu:24.04 && distrobox enter ubuntu", noRun: true },
          { cmd: "distrobox-export --app nazwa-programu", noRun: true, note: "Wewnątrz kontenera: dodaj program do menu FurrOS." },
          { p: "Uprawnienia programów Flatpak (dostęp do folderów, urządzeń) wygodnie przeglądać i zmieniać we <b>Flatseal</b>:" },
          { cmd: "flatpak install flathub com.github.tchx84.Flatseal", noRun: true },
          { say: "Chcesz spróbować czegoś podejrzanego — rób to w kontenerze. Nie spodobało się — usuwasz pudełko, system czysty. Jak cytryna w woreczku: nie kapie 🍋" },
        ] },
      ],
      quiz: [
        { q: "Co robi podman run --rm?", a: ["Usuwa kontener po wyjściu", "Usuwa obraz", "Usuwa podmana"], ok: 0 },
        { q: "Po co distrobox?", a: ["Uruchamiać programy z innych dystrybucji jak natywne", "Przyspieszyć Wi-Fi", "Robić migawki Btrfs"], ok: 0 },
        { q: "Gdzie wygodnie zmieniać uprawnienia programów Flatpak?", a: ["Flatseal", "GRUB", "htop"], ok: 0 },
      ],
    },
    {
      id: "d-vm", mood: "timer", badge: "🍋 Wirtualizator", title: "Maszyny wirtualne",
      intro: "KVM/QEMU i virt-manager: Windows albo inny Linux w oknie.",
      lessons: [
        { title: "Instalujemy KVM", blocks: [
          { cmd: "grep -Ec '(vmx|svm)' /proc/cpuinfo", note: "Więcej niż zero — procesor obsługuje wirtualizację. Jeśli 0, włącz VT-x/AMD-V (SVM) w BIOS-ie." },
          { cmd: "sudo pacman -S qemu-desktop libvirt virt-manager dnsmasq edk2-ovmf swtpm", noRun: true, note: "edk2-ovmf — UEFI, swtpm — TPM dla Windows 11." },
          { cmd: "sudo systemctl enable --now libvirtd && sudo usermod -aG libvirt $USER", noRun: true, note: "Zaloguj się ponownie, żeby grupa zadziałała." },
          { p: "Potem otwórz <b>Virtual Machine Manager</b>, kliknij „Utwórz maszynę wirtualną” i wybierz ISO. Do prostych zastosowań jest też <b>GNOME Boxes</b>." },
        ] },
        { title: "Żeby było szybko", blocks: [
          { ul: [
            "Dysk i sieć — typ <b>virtio</b>: wyraźnie szybsze od emulowanych. Windows potrzebuje sterowników virtio-win (ISO ze strony Fedory).",
            "Procesor — tryb <b>host-passthrough</b>.",
            "Nie dawaj maszynie więcej niż połowy rdzeni i pamięci, gospodarz też musi żyć.",
            "Migawki maszyny — przed eksperymentami, tak jak w samym FurrOS.",
          ] },
          { say: "Maszyna wirtualna to najlepszy poligon. Chcesz zepsuć bootloader, żeby nauczyć się go naprawiać? Psuj tam, a nie w głównym systemie 🍋" },
        ] },
      ],
      quiz: [
        { q: "Jak sprawdzić, czy procesor obsługuje wirtualizację?", a: ["grep -Ec '(vmx|svm)' /proc/cpuinfo", "uname -r", "lsusb"], ok: 0 },
        { q: "Jaki typ dysków i sieci jest najszybszy w KVM?", a: ["virtio", "IDE", "dyskietka"], ok: 0 },
        { q: "Do jakiej grupy dodać się dla libvirt?", a: ["libvirt", "wheel", "audio"], ok: 0 },
      ],
    },
    {
      id: "d-security", mood: "grr", badge: "🍋 Paranoik", title: "Głębokie bezpieczeństwo",
      intro: "Szyfrowanie LUKS, sudoers, klucze pacmana i Secure Boot.",
      lessons: [
        { title: "Szyfrowanie i sudo", blocks: [
          { p: "<b>LUKS</b> szyfruje całą partycję: ktoś ukradnie laptopa — bez hasła danych nie odczyta. Zaszyfrowanie pendrive’a:" },
          { cmd: "sudo cryptsetup luksFormat /dev/sdX1", noRun: true, note: "WYMAŻE wszystko na partycji! Potem: sudo cryptsetup open /dev/sdX1 secret && sudo mkfs.ext4 /dev/mapper/secret" },
          { cmd: "sudo cryptsetup luksDump /dev/sdX1", noRun: true, note: "Informacje o szyfrowaniu i slotach kluczy." },
          { p: "Uprawnienia sudo edytuje się tylko przez <code>visudo</code>: sprawdzi składnię, więc nie odetniesz sobie sudo." },
          { cmd: "sudo EDITOR=nano visudo -f /etc/sudoers.d/10-furry", noRun: true },
          { warn: "Zepsuty sudoers = brak sudo. Dlatego tylko visudo, nigdy zwykłym edytorem." },
        ] },
        { title: "Klucze i Secure Boot", blocks: [
          { p: "pacman sprawdza podpis każdego pakietu. Jeśli marudzi o klucze (zdarza się po długiej przerwie):" },
          { cmd: "sudo pacman -Sy archlinux-keyring furros-keyring && sudo pacman -Su", noRun: true },
          { cmd: "pacman-key --list-keys | grep -i furros", note: "Klucz repozytorium [furros] jest na miejscu." },
          { p: "<b>Secure Boot</b> z Linuksem można włączyć własnymi kluczami przez <b>sbctl</b> (<code>sbctl status</code>, <code>sbctl create-keys</code>, <code>sbctl enroll-keys -m</code>, potem podpisać bootloader i jądro). To zaawansowana konfiguracja: czytaj wiki Archa i trzymaj pendrive z FurrOS pod ręką." },
          { say: "Bezpieczeństwo to warstwy: aktualizacje, zapora, klucze, szyfrowanie, kopie. Żadna warstwa nie jest idealna, razem to twierdza. Nawet cytryna ma skórkę 🍋" },
        ] },
      ],
      quiz: [
        { q: "Czym edytuje się uprawnienia sudo?", a: ["visudo", "nano /etc/sudoers bezpośrednio", "chmod 777"], ok: 0 },
        { q: "Co robi cryptsetup luksFormat z partycją?", a: ["Tworzy zaszyfrowaną partycję, wymazując dane", "Sprawdza dysk", "Przyspiesza dysk"], ok: 0 },
        { q: "pacman marudzi o klucze. Co zaktualizować najpierw?", a: ["archlinux-keyring (i furros-keyring)", "Jądro", "Firefoksa"], ok: 0 },
      ],
    },
    {
      id: "d-rescue", mood: "grr", badge: "🍋 Reanimator", title: "Hardkorowe naprawy",
      intro: "Naprawa bootloadera, blokady pacmana, przerwanej aktualizacji i rescue.target.",
      lessons: [
        { title: "Typowe awarie", blocks: [
          { table: { head: ["Problem", "Leczenie"], rows: [
            ["„unable to lock database”", "pacman nie działa? To <code>sudo rm /var/lib/pacman/db.lck</code>"],
            ["Aktualizacja przerwana (prąd, bateria)", "Z konsoli albo chroota: <code>sudo pacman -Syu</code>, potem <code>sudo mkinitcpio -P</code>"],
            ["„invalid or corrupted package (PGP signature)”", "Zaktualizuj keyring (patrz poprzedni rozdział)"],
            ["Zniknęło menu FurrBoot po Windowsie", "W menu rozruchu płyty (F11/F12/F8) wybierz «FurrOS» — to zapasowy GRUB. Potem w systemie: <code>sudo furrboot-install</code>"],
            ["Grafika się nie uruchamia", "Ctrl+Alt+F3, log: <code>journalctl -b -1 -p 3</code> (błędy z poprzedniego rozruchu)"],
          ] } },
          { p: "Jeśli nie da się wejść nawet do konsoli, w FurrBoot wciśnij <kbd>E</kbd> i dopisz na końcu parametrów: <code>systemd.unit=rescue.target</code>. System uruchomi się w trybie minimalnym z konsolą roota." },
        ] },
        { title: "Pełny chroot", blocks: [
          { p: "Z pendrive’a FurrOS. Dla FurrOS na Btrfs:" },
          { cmd: "lsblk -f\nsudo mount -o subvol=@ /dev/nvme0n1p2 /mnt\nsudo mount /dev/nvme0n1p1 /mnt/boot/efi\nsudo arch-chroot /mnt", noRun: true, note: "Nazwy partycji weź z lsblk. Partycja EFI przy instalacji na Btrfs idzie do /boot/efi, przy ext4 i szyfrowanej do /boot. Zaszyfrowany dysk najpierw otwórz: cryptsetup open." },
          { p: "W środku jesteś jak we własnym systemie: aktualizuj, przeinstaluj jądro (<code>pacman -S linux</code>), napraw menu startowe (<code>furrboot-install</code>), popraw fstab. Wyjście: <code>exit</code>, potem <code>sudo umount -R /mnt</code>." },
          { say: "Jeśli dotarłeś(-aś) tutaj, zepsuty system już cię nie straszy. Wiesz, jak działa, więc wiesz, jak go podnieść. To jest właśnie mistrz 🍋" },
        ] },
      ],
      quiz: [
        { q: "pacman pisze „unable to lock database”, a nie działa. Co robić?", a: ["Usunąć /var/lib/pacman/db.lck", "Przeinstalować system", "Usunąć pacmana"], ok: 0 },
        { q: "Jak uruchomić tryb minimalny z menu startowego?", a: ["Dopisać systemd.unit=rescue.target", "Wcisnąć F12", "Dopisać quiet"], ok: 0 },
        { q: "Jak zobaczyć błędy z poprzedniego rozruchu?", a: ["journalctl -b -1 -p 3", "dmesg --future", "pacman -Qe"], ok: 0 },
      ],
    },
    {
      id: "d-final", mood: "wave", badge: "🍋 Mistrz FurrOS", title: "Zakończenie u Danyoka",
      intro: "Git, zgłoszenia błędów, Arch Wiki i jak pomagać FurrOS.",
      lessons: [
        { title: "Git w pięć minut", blocks: [
          { cmd: "git clone https://github.com/Vitlikxbox/FurrOS.git && cd FurrOS", noRun: true },
          { table: { head: ["Polecenie", "Co robi"], rows: [
            ["<code>git status</code>", "Co zmienione"], ["<code>git diff</code>", "Same zmiany"],
            ["<code>git add plik</code>", "Przygotuj do zapisu"], ["<code>git commit -m \"co zrobiłem\"</code>", "Zapisz wersję"],
            ["<code>git log --oneline</code>", "Historia"], ["<code>git switch -c fix-typo</code>", "Nowa gałąź na twoje zmiany"],
          ] } },
          { tip: "Trzymanie konfiguracji w gicie to świetny nawyk: każdą nieudaną zmianę da się cofnąć, a na nowy komputer przenieść jednym poleceniem." },
        ] },
        { title: "Jak pomagać", blocks: [
          { ul: [
            "<b>Dobre zgłoszenie błędu</b>: co robiłeś(-aś), czego oczekiwałeś(-aś), co wyszło, wersja (<code>fastfetch</code>), log (<code>journalctl -b -p 3</code> albo <code>/var/log/furros-install.log</code>).",
            "Znalazłeś(-aś) błąd w tłumaczeniu albo lekcji — napisz na Discordzie FurrOS albo otwórz issue na GitHubie.",
            "<b>Arch Wiki</b> piszą tacy sami użytkownicy. Znalazłeś(-aś) nieścisłość — popraw, to najlepszy wkład w świat Linuksa.",
            "Pomagaj nowicjuszom na czacie: wytłumaczyć komuś to najlepszy sposób, by zrozumieć samemu.",
          ] },
          { say: "To wszystko. Trzech nauczycieli, czterdzieści dwa rozdziały. Przeszedłeś(-aś) drogę od „co to jest terminal” do chroota i własnych pakietów. Lapa jest dumna, Pixie zatwierdza, a ode mnie — cytryna. Zasłużyłeś(-aś) 🍋🎓" },
        ] },
      ],
      quiz: [
        { q: "Co koniecznie dołączyć do zgłoszenia błędu?", a: ["Kroki, oczekiwania, wynik i log", "Tylko „nie działa”", "Zrzut ekranu tapety"], ok: 0 },
        { q: "Które polecenie zapisuje wersję w gicie?", a: ["git commit", "git status", "git log"], ok: 0 },
        { q: "Kto pisze Arch Wiki?", a: ["Użytkownicy, i ty też możesz", "Tylko pracownicy Microsoftu", "Nikt, pisze się sama"], ok: 0 },
      ],
    },
  ] },
};
