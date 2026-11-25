"""Polish and Spanish for the FurrOS Downloader window. Keys are the English texts; Russian and English live in the
code next to each other (T(ru, en)). Anything missing here is shown in English."""

LANGS = [("ru", "Русский"), ("en", "English"), ("pl", "Polski"), ("es", "Español")]

TR = {
    "GitHub didn't accept the token: check it was copied whole and hasn't expired":
        ("GitHub nie przyjął tokenu: sprawdź, czy skopiowano go w całości i czy nie wygasł",
         "GitHub no aceptó el token: comprueba que lo copiaste entero y que no ha caducado"),
    "Build not found. If it's a private test build, a GitHub token is needed":
        ("Nie znaleziono wersji. Jeśli to prywatna wersja testowa, potrzebny jest token GitHub",
         "No se encontró la versión. Si es una versión de prueba privada, hace falta un token de GitHub"),
    "Private test build: paste your GitHub token. To make one: github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token, tick “repo”, expiry 7 days. The token is not saved.":
        ("Prywatna wersja testowa: wklej swój token GitHub. Jak go utworzyć: github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token, zaznacz „repo”, ważność 7 dni. Token nie jest zapisywany.",
         "Versión de prueba privada: pega tu token de GitHub. Para crearlo: github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token, marca «repo», caducidad 7 días. El token no se guarda."),
    "The ISO hash doesn't match. Delete the files and download again":
        ("Suma kontrolna ISO się nie zgadza. Usuń pliki i pobierz ponownie",
         "El hash del ISO no coincide. Borra los archivos y descárgalo de nuevo"),
    "The stick is smaller than the image": ("Pendrive jest mniejszy niż obraz", "El pendrive es más pequeño que la imagen"),
    "Writing to the stick failed. Try again or another stick":
        ("Zapis na pendrive się nie udał. Spróbuj ponownie albo użyj innego pendrive'a",
         "No se pudo escribir en el pendrive. Inténtalo de nuevo o usa otro pendrive"),
    "Skip ›": ("Pomiń ›", "Saltar ›"),
    "click to continue": ("kliknij, aby kontynuować", "haz clic para continuar"),
    "Looking for the latest build…": ("Szukam najnowszej wersji…", "Buscando la última versión…"),
    "Browse…": ("Wybierz…", "Elegir…"),
    "Then write it to a USB stick": ("Potem zapisz na pendrive", "Después grabarlo en un USB"),
    "Download FurrOS": ("Pobierz FurrOS", "Descargar FurrOS"),
    "Folder for the ISO": ("Folder na ISO", "Carpeta para la ISO"),
    "Pause": ("Pauza", "Pausa"),
    "Connecting…": ("Łączę się…", "Conectando…"),
    "Downloading FurrOS": ("Pobieram FurrOS", "Descargando FurrOS"),
    "Velvet": ("Velvet", "Velvet"),
    "Lapa": ("Łapa", "Lapa"),
    "Danyok": ("Danek", "Danyok"),
    "Done! 🎉": ("Gotowe! 🎉", "¡Listo! 🎉"),
    "Open folder": ("Otwórz folder", "Abrir carpeta"),
    "Write to a USB stick": ("Zapisz na pendrive", "Grabar en un USB"),
    "Close": ("Zamknij", "Cerrar"),
    "Refresh": ("Odśwież", "Actualizar"),
    "I understand that EVERYTHING on the chosen stick will be erased":
        ("Rozumiem, że WSZYSTKO na wybranym pendrivie zostanie usunięte",
         "Entiendo que se borrará TODO en el USB elegido"),
    "Back": ("Wstecz", "Atrás"),
    "Write": ("Zapisz", "Grabar"),
    "Try again": ("Spróbuj ponownie", "Intentar de nuevo"),
    "Writing to the stick — don't unplug it": ("Zapisuję na pendrive — nie wyjmuj go", "Grabando en el USB — no lo desconectes"),
    "A fluffy Arch-based Linux distro": ("Puszysta dystrybucja Linuksa oparta na Archu", "Una distro Linux esponjosa basada en Arch"),
    "Where to save the ISO": ("Gdzie zapisać ISO", "Dónde guardar la ISO"),
    "The stick is ready! 🎉": ("Pendrive gotowy! 🎉", "¡El USB está listo! 🎉"),
    "Plug it in and pick it in the boot menu (F8 / F11 / F12 / Esc).":
        ("Podłącz go i wybierz w menu rozruchu (F8 / F11 / F12 / Esc).",
         "Conéctalo y elígelo en el menú de arranque (F8 / F11 / F12 / Esc)."),
    "Next: write the ISO to a USB stick — here, with Rufus (DD mode) or Ventoy — and boot from it.":
        ("Dalej: zapisz ISO na pendrive — tutaj, Rufusem (tryb DD) lub Ventoyem — i uruchom z niego komputer.",
         "Siguiente: graba la ISO en un USB — aquí, con Rufus (modo DD) o Ventoy — y arranca desde él."),
    "Only USB disks are shown here — the computer's internal disks never are.":
        ("Widać tu tylko dyski USB — wewnętrznych dysków komputera nigdy.",
         "Aquí solo aparecen discos USB — nunca los discos internos del equipo."),
    "No stick found — plug it in and press Refresh.":
        ("Nie znaleziono pendrive'a — podłącz go i naciśnij Odśwież.",
         "No se encontró ningún USB — conéctalo y pulsa Actualizar."),
    "Grr, something went wrong": ("Grr, coś poszło nie tak", "Grr, algo salió mal"),
    "Nothing downloaded is lost: next time it resumes from the same point.":
        ("Nic pobranego nie przepadnie: następnym razem pobieranie wznowi się w tym samym miejscu.",
         "No se pierde nada de lo descargado: la próxima vez continúa desde el mismo punto."),
    "On Windows write the stick with Rufus (DD mode) or Ventoy — I'll remind you at the end.":
        ("Na Windowsie zapisz pendrive Rufusem (tryb DD) lub Ventoyem — przypomnę na końcu.",
         "En Windows graba el USB con Rufus (modo DD) o Ventoy — te lo recordaré al final."),
    "Found the build! Pick a folder and press the button.":
        ("Znalazłam wersję! Wybierz folder i naciśnij przycisk.", "¡Encontré la versión! Elige una carpeta y pulsa el botón."),
    "Danyok is gluing the parts into one ISO": ("Danek skleja części w jedno ISO", "Danyok está pegando las partes en una ISO"),
    "Checking that everything arrived intact": ("Sprawdzam, czy wszystko dotarło bez błędów", "Comprobando que todo llegó intacto"),
    "Piece by piece… Lemon, don't let me down! 🍋": ("Kawałek po kawałku… Cytrynko, nie zawiedź! 🍋",
                                                    "Pieza a pieza… ¡Limón, no me falles! 🍋"),
    "FurrOS has 17 desktops — from cosy KDE to tiling Hyprland. You pick one in the installer!":
        ("FurrOS ma 17 pulpitów — od przytulnego KDE po kafelkowy Hyprland. Wybierzesz w instalatorze!",
         "FurrOS tiene 17 escritorios — desde el acogedor KDE hasta el mosaico Hyprland. ¡Lo eliges en el instalador!"),
    "Lapa's School teaches Linux basics right after install. No boring lectures, promise.":
        ("Szkoła Łapy nauczy podstaw Linuksa zaraz po instalacji. Bez nudnych wykładów, obiecuję.",
         "La Escuela de Lapa enseña lo básico de Linux justo después de instalar. Sin clases aburridas, lo prometo."),
    "System snapshots: if an update breaks something, pick a snapshot in the boot menu — and it's all back.":
        ("Migawki systemu: jeśli aktualizacja coś zepsuje, wybierz migawkę w menu rozruchu — i wszystko wraca.",
         "Instantáneas del sistema: si una actualización rompe algo, elige una en el menú de arranque — y todo vuelve."),
    "Live wallpapers move right on your desktop. My favourites are the Lapa ones.":
        ("Żywe tapety ruszają się na pulpicie. Moje ulubione są te z Łapą.",
         "Los fondos animados se mueven en tu escritorio. Mis favoritos son los de Lapa."),
    "FurrOS installs next to Windows: you choose the system when the computer starts.":
        ("FurrOS instaluje się obok Windowsa: system wybierasz przy włączaniu komputera.",
         "FurrOS se instala junto a Windows: eliges el sistema al encender el equipo."),
    "Graphics drivers install themselves, even for older NVIDIA GTX 10xx cards.":
        ("Sterowniki grafiki instalują się same, nawet dla starszych NVIDIA GTX 10xx.",
         "Los drivers gráficos se instalan solos, incluso para las NVIDIA GTX 10xx más antiguas."),
    "The installer speaks 4 languages, and the system itself comes in any of 51 — with phonetic layouts too.":
        ("Instalator mówi w 4 językach, a sam system możesz zainstalować w jednym z 51 — także z układami fonetycznymi.",
         "El instalador habla 4 idiomas, y el sistema en sí puede ir en cualquiera de 51, también con teclados fonéticos."),
    "FurrOS has its own boot menu, FurrBoot: with a mouse, themes and system snapshots. And with me!":
        ("FurrOS ma własne menu rozruchowe, FurrBoot: z myszką, motywami i migawkami systemu. I ze mną!",
         "FurrOS tiene su propio menú de arranque, FurrBoot: con ratón, temas e instantáneas del sistema. ¡Y conmigo!"),
    "A handy way to write the stick: Rufus (DD mode) or Ventoy.":
        ("Pendrive wygodnie zapiszesz Rufusem (tryb DD) lub Ventoyem.", "Una forma cómoda de grabar el USB: Rufus (modo DD) o Ventoy."),
    "If the internet drops — no worries, the download resumes from the same point.":
        ("Jeśli internet się zerwie — spokojnie, pobieranie wznowi się w tym samym miejscu.",
         "Si se corta internet — tranquilo, la descarga continúa desde el mismo punto."),
    "Hi! I'm Lapa 🐾 We're going to download FurrOS together — it's quicker than it looks!":
        ("Cześć! Jestem Łapa 🐾 Razem pobierzemy FurrOS — to szybsze, niż się wydaje!",
         "¡Hola! Soy Lapa 🐾 Vamos a descargar FurrOS juntos — ¡es más rápido de lo que parece!"),
    "And I'm Velvet. While it downloads I'll tell you cool stuff. Or just hang out here.":
        ("A ja jestem Velvet. Gdy się pobiera, opowiem ci ciekawostki. Albo po prostu posiedzę obok.",
         "Y yo soy Velvet. Mientras se descarga te contaré cosas chulas. O simplemente me quedo por aquí."),
    "And I'll glue the image pieces into one. It's faster with a lemon, tested 🍋":
        ("A ja skleję kawałki obrazu w jeden. Z cytryną idzie szybciej, sprawdzone 🍋",
         "Y yo pegaré los trozos de la imagen en uno. Con limón va más rápido, comprobado 🍋"),
    "So, shall we? Click when you're ready!": ("No to co, ruszamy? Kliknij, gdy będziesz gotowy!",
                                               "¿Vamos? ¡Haz clic cuando estés listo!"),
    "Stopped. Start again — the download resumes from the same point":
        ("Zatrzymano. Uruchom ponownie — pobieranie wznowi się w tym samym miejscu",
         "Detenido. Empieza de nuevo — la descarga continúa desde el mismo punto"),
    "Can't reach GitHub. Check the internet": ("Brak połączenia z GitHubem. Sprawdź internet", "No se puede conectar con GitHub. Revisa internet"),
    "Build not found. It may not be published yet": ("Nie znaleziono wersji. Może jeszcze nie jest opublikowana",
                                                     "No se encontró la versión. Puede que aún no esté publicada"),
}

# with numbers in them: "{0}" placeholders
FMT = {
    "size": {"ru": "Размер: {0} · частей: {1}", "en": "Size: {0} · parts: {1}",
             "pl": "Rozmiar: {0} · części: {1}", "es": "Tamaño: {0} · partes: {1}"},
    "eta": {"ru": " · осталось ~{0} мин {1:02d} с", "en": " · ~{0} min {1:02d} s left",
            "pl": " · zostało ~{0} min {1:02d} s", "es": " · quedan ~{0} min {1:02d} s"},
    "sec": {"ru": "с", "en": "s", "pl": "s", "es": "s"},
}

TITLE = "Выбери язык · Choose language · Wybierz język · Elige idioma"
