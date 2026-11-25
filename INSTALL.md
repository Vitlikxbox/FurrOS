# 🐾 Как установить FurrOS 1.0 (бета)

[English version below](#-how-to-install-furros-10-beta)

> ⚠️ Это бета. Перед установкой **сохрани важные файлы** на другой диск или в облако.

## Что нужно

| | Минимум | Лучше |
|---|---|---|
| Компьютер | 64-битный (x86_64), UEFI или старый BIOS | UEFI |
| Оперативная память | 2 ГБ | 4 ГБ и больше (на 2–4 ГБ бери лёгкую оболочку: Xfce, LXQt) |
| Место на диске | 20 ГБ | 50 ГБ и больше |
| Флешка | 4 ГБ (всё на ней сотрётся) | — |
| Интернет | нужен во время установки (Wi-Fi или кабель) | кабель |

## 1. Скачай образ

**Проще всего — FurrOS Downloader**: на странице релиза файл `FurrOS-Downloader.exe` для Windows или `FurrOS-Downloader-x86_64.AppImage` для Linux (сделай его исполняемым: `chmod +x FurrOS-Downloader-x86_64.AppImage`). Он сам скачает и проверит образ. На Linux он ещё и запишет флешку — тогда сразу переходи к шагу 3; на Windows флешку запиши по шагу 2.

**Вручную:** на странице релиза скачай **все 6 частей** (`FurrOS-1.0-x86_64.iso.part1` … `part6`) и файл `FurrOS-1.0-x86_64.iso.sha256` в одну папку и склей их:

- Windows (командная строка, `cmd`, в этой папке):
  ```
  copy /b FurrOS-1.0-x86_64.iso.part1 + FurrOS-1.0-x86_64.iso.part2 + FurrOS-1.0-x86_64.iso.part3 + FurrOS-1.0-x86_64.iso.part4 + FurrOS-1.0-x86_64.iso.part5 + FurrOS-1.0-x86_64.iso.part6 FurrOS-1.0-x86_64.iso
  ```
- Linux / macOS:
  ```
  cat FurrOS-1.0-x86_64.iso.part{1..6} > FurrOS-1.0-x86_64.iso
  ```

Проверь, что образ скачался целым: число должно совпасть с тем, что в файле `.sha256`.

- Windows: `certutil -hashfile FurrOS-1.0-x86_64.iso SHA256`
- Linux: `sha256sum FurrOS-1.0-x86_64.iso`

## 2. Запиши флешку

Подойдёт любая из программ: **FurrOS Downloader** (только на Linux), **Rufus** (когда спросит — выбери режим **DD**), **Ventoy** или **balenaEtcher**. Всё, что было на флешке, сотрётся.

## 3. Подготовь компьютер

- **Secure Boot выключи** в настройках UEFI (обычно клавиша Del, F2 или F10 при включении): FurrOS с ним не загрузится.
- **Если хочешь оставить Windows** (только в режиме UEFI), сначала загрузи Windows и:
  1. Выключи гибернацию и «Быстрый запуск»: командная строка **от администратора** → `powercfg /h off`, затем «Завершение работы» (не перезагрузка).
  2. Если диск C: зашифрован **BitLocker** (часто на ноутбуках с Windows 11): сохрани ключ восстановления (aka.ms/myrecoverykey), освободи место сам: Win+X → «Управление дисками» → правой кнопкой по C: → «Сжать том», хотя бы 20 ГБ. Приостанови защиту BitLocker прямо перед отключением Secure Boot.
  3. Без BitLocker ничего сжимать не надо — установщик сам возьмёт у Windows столько места, сколько скажешь.

## 4. Загрузись с флешки

Вставь флешку, включи компьютер и сразу нажимай клавишу загрузочного меню — обычно **F12**, **F11**, **F8** или **Esc** (зависит от производителя). Выбери флешку. Если экран остался чёрным — перезагрузись и выбери в меню пункт **«безопасная графика»** (safe graphics). Если флешка не появилась в списке — проверь, что Secure Boot выключен, и попробуй другой USB-порт.

## 5. Установи

На рабочем столе живой системы открой **«Установить FurrOS»**. Лапа проведёт по шагам и подскажет, если навести мышку на любой пункт:

1. **Привет** — язык установщика (русский, English, polski, español) и язык самой системы (любой из 51).
2. **Условия** — прочитай и прими.
3. **Проверка готовности** — интернет, режим загрузки, память, диск. Красный пункт останавливает установку, жёлтый только предупреждает. Нет интернета — подключись через значок сети в углу экрана.
4. **Регион** — часовой пояс и раскладки клавиатуры.
5. **Диск** — **«Весь диск»** (всё на нём сотрётся), **«Рядом с Windows»** или **«Свои разделы»**: размечаешь диск сам (кнопка «Открыть менеджер разделов») и выбираешь раздел для FurrOS и существующий раздел EFI — так удобно ставить рядом с Arch или другим Linux. Тут же можно выбрать Btrfs (рекомендуем: снимки системы и откат), шифрование и подкачку.
6. **Рабочий стол** — если сомневаешься, бери **KDE Plasma**. Xfce, MATE и Deepin пока помечены «Экспериментальная».
7. **Программы** — браузер, наборы программ и ядро. Обычное ядро подходит всем; если выберешь Zen или LTS, обычное ядро и ядро FurrOS поставятся рядом как запасные.
8. **Оформление** — обои (есть анимированные) и мелочи вроде «Школы Лапы» при первом входе.
9. **Аккаунт** — имя, имя пользователя латиницей и пароль. Пароль нужен для входа и для `sudo`, не забудь его.
10. **Итог** — проверь всё, особенно диск, и нажми **«Установить»**. После этого назад дороги нет.

Установка занимает от 10 до 40 минут — зависит от интернета и компьютера. Когда Лапа скажет «Готово!», вытащи флешку и перезагрузись.

## 6. После установки

- Тебя встретит Пикси, а потом Лапа покажет, где что, в **«Школе Лапы»**.
- Обновлять систему: `furros-update` в терминале.
- Если что-то сломалось после обновления — в меню загрузки FurrBoot можно загрузиться из снимка системы (на Btrfs).

## Если что-то пошло не так

- **Чёрный экран после установки** — в меню загрузки выбери «Безопасная графика», войди и выполни `sudo furros-drivers --install`.
- **Windows просит ключ BitLocker**, когда выбираешь её в меню FurrOS — введи ключ или запускай Windows через загрузочное меню компьютера (F8, F11 или F12).
- **Нет нужного пункта в меню загрузки / не грузится** — заходи в [Discord](https://discord.gg/ZA3GuBYKwG): там отвечают Лапа и команда.

---

# 🐾 How to install FurrOS 1.0 (beta)

> ⚠️ This is a beta. **Back up your important files** to another drive or the cloud before installing.

## What you need

| | Minimum | Better |
|---|---|---|
| Computer | 64-bit (x86_64), UEFI or old BIOS | UEFI |
| Memory (RAM) | 2 GB | 4 GB or more (with 2–4 GB pick a light desktop: Xfce, LXQt) |
| Disk space | 20 GB | 50 GB or more |
| USB stick | 4 GB (everything on it is erased) | — |
| Internet | needed during the install (Wi-Fi or cable) | cable |

## 1. Download the image

**Easiest: FurrOS Downloader**: on the release page, `FurrOS-Downloader.exe` for Windows or `FurrOS-Downloader-x86_64.AppImage` for Linux (make it executable: `chmod +x FurrOS-Downloader-x86_64.AppImage`). It downloads and verifies the image. On Linux it also writes the USB stick — then skip to step 3; on Windows write the stick as in step 2.

**By hand:** on the release page download **all 6 parts** (`FurrOS-1.0-x86_64.iso.part1` … `part6`) and `FurrOS-1.0-x86_64.iso.sha256` into one folder and join them:

- Windows (Command Prompt, `cmd`, in that folder):
  ```
  copy /b FurrOS-1.0-x86_64.iso.part1 + FurrOS-1.0-x86_64.iso.part2 + FurrOS-1.0-x86_64.iso.part3 + FurrOS-1.0-x86_64.iso.part4 + FurrOS-1.0-x86_64.iso.part5 + FurrOS-1.0-x86_64.iso.part6 FurrOS-1.0-x86_64.iso
  ```
- Linux / macOS:
  ```
  cat FurrOS-1.0-x86_64.iso.part{1..6} > FurrOS-1.0-x86_64.iso
  ```

Check that the image is intact: the number must match the one in the `.sha256` file.

- Windows: `certutil -hashfile FurrOS-1.0-x86_64.iso SHA256`
- Linux: `sha256sum FurrOS-1.0-x86_64.iso`

## 2. Write the USB stick

Any of these works: **FurrOS Downloader** (Linux only), **Rufus** (pick **DD** mode when asked), **Ventoy** or **balenaEtcher**. Everything on the stick is erased.

## 3. Prepare the computer

- **Turn Secure Boot off** in the UEFI settings (usually Del, F2 or F10 at power-on): FurrOS won't boot with it on.
- **To keep Windows** (UEFI mode only), boot Windows first and:
  1. Turn off hibernation and «Fast startup»: Command Prompt **as administrator** → `powercfg /h off`, then «Shut down» (not restart).
  2. If drive C: is encrypted with **BitLocker** (common on Windows 11 laptops): save the recovery key (aka.ms/myrecoverykey) and free up space yourself: Win+X → «Disk Management» → right-click C: → «Shrink Volume», at least 20 GB. Suspend BitLocker protection right before turning off Secure Boot.
  3. Without BitLocker there's nothing to shrink: the installer takes as much space from Windows as you tell it.

## 4. Boot from the USB stick

Plug in the stick, turn the computer on and keep pressing the boot menu key — usually **F12**, **F11**, **F8** or **Esc** (depends on the maker). Pick the stick. If the screen stays black, reboot and pick the **safe graphics** entry in the menu. If the stick isn't in the list, check that Secure Boot is off and try another USB port.

## 5. Install

On the live desktop open **«Install FurrOS»**. Lapa guides you through each step and explains any item you hover with the mouse:

1. **Welcome** — the installer language (Русский, English, polski, español) and the system language (any of 51).
2. **Terms** — read and accept.
3. **Readiness check** — internet, boot mode, memory, disk. A red item stops the install, a yellow one only warns. No internet? Connect with the network icon in the screen corner.
4. **Region** — time zone and keyboard layouts.
5. **Disk** — **«Whole disk»** (everything on it is erased), **«Next to Windows»** or **«Your own partitions»**: you partition the disk yourself (the «Open the partition manager» button) and pick a partition for FurrOS and an existing EFI partition — handy next to Arch or another Linux. Here you also choose Btrfs (recommended: system snapshots and rollback), encryption and swap.
6. **Desktop** — if unsure, take **KDE Plasma**. Xfce, MATE and Deepin are still marked «Experimental».
7. **Apps** — a browser, app bundles and the kernel. The standard kernel suits everyone; pick Zen or LTS and the standard and FurrOS kernels are installed next to it as spares.
8. **Look** — wallpapers (animated ones too) and small things like opening Lapa's School at first login.
9. **Account** — your name, a Latin-letters user name and a password. You need the password to log in and for `sudo`, don't forget it.
10. **Summary** — check everything, especially the disk, and press **«Install»**. There's no way back after that.

The install takes 10 to 40 minutes, depending on your internet and computer. When Lapa says «Done!», remove the stick and reboot.

## 6. After installing

- Pixie greets you, then Lapa shows you around in **Lapa's School**.
- To update the system: `furros-update` in a terminal.
- If an update broke something, the FurrBoot boot menu can start the system from a snapshot (on Btrfs).

## If something goes wrong

- **Black screen after installing** — pick «Safe graphics» in the boot menu, log in and run `sudo furros-drivers --install`.
- **Windows asks for the BitLocker key** when you pick it in the FurrOS menu — enter the key, or start Windows from the computer's boot menu (F8, F11 or F12).
- **A boot menu entry is missing / it won't boot** — join our [Discord](https://discord.gg/ZA3GuBYKwG): Lapa and the team answer there.
