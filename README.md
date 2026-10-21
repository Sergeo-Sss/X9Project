# X9 Project

Инструменты и приложение-читалка документов для умных часов **X9-CALL**
(Android 8.1, экран 320×385, скруглённый прямоугольник, Unisoc, Wi-Fi).

Часы читаются по Wi-Fi: это полноценный Android, но ADB по сети на Android 8 без
кабеля недоступен, поэтому файлы передаются по FTP (CX File Explorer → «Доступ с
компьютера»).

## X9 Reader — приложение

WebView-читалка, которая показывает документ крупным шрифтом, тёмной темой,
с оглавлением и настройкой размера шрифта — то, чего не хватает при открытии
документов в Word на мелком экране.

Конвейер: `.docx` → чистый HTML (заголовки, таблицы, **математика** через
`<sub>`/`<sup>`) → WebView в APK. Собирается только утилитами Android SDK, без
Android Studio и Gradle.

### Как добавить/обновить документ на часах

```bash
# 1. документ -> HTML-читалка
python reader/tools/docx2html.py путь/к.docx reader/app/assets/doc.html "Заголовок"
# 2. собрать и подписать APK
python reader/tools/build_apk.py
# 3. залить на часы (нужен включённый FTP в CX File Explorer)
python ftp_put.py reader/build/X9Reader.apk /device/Download
```

На часах: CX File Explorer → `Download` → `X9Reader.apk` → установить.

### Управление в приложении

- прокрутка — палец; колёсико/кнопки обрабатываются, но их поведение зависит от
  часов (см. ниже про диагностику);
- тап у верха экрана — панель `A− ☰ A+` (размер шрифта и оглавление);
- оглавление также встроено в начало страницы;
- тап по **левому нижнему углу** — панель диагностики ввода (показывает код
  события от колёсика/кнопок; нужна, чтобы подобрать обработку крутилки).

## Структура

| Путь | Что это |
|---|---|
| `reader/app/` | исходники Android-приложения (манифест, `MainActivity.java`, `assets/`) |
| `reader/tools/docx2html.py` | конвертер документа в HTML-читалку |
| `reader/tools/build_apk.py` | ручная сборка и подпись APK |
| `reader/tools/watch.py` | подключение к часам по FTP (читает `watch.local.json`) |
| `reader/tools/inspect_docx.py` | разбор структуры .docx |
| `ftp_ls.py`, `ftp_put.py` | просмотр и загрузка файлов на часы |
| `ble_scan.py`, `ble_dump.py`, `lan_scan.py`, `port_scan.py` | сетевая разведка, как искали часы |
| `.claude/skills/` | локальные скиллы проекта (workflow для будущих сессий) |

## Доступ к часам

Скопируйте шаблон и впишите данные, которые показывает CX File Explorer:

```bash
cp watch.local.example.json watch.local.json
```

`watch.local.json` и ключ подписи не попадают в git (см. `.gitignore`). Адрес и
пароль FTP в CX меняются при каждом запуске сервера — обновляйте файл.

## Требования

- Python 3.12+ (стандартная библиотека; `bleak` только для BLE-разведки)
- JDK 17 (`JAVA_HOME`)
- Android SDK: `build-tools/36.0.0`, `platforms/android-34`
