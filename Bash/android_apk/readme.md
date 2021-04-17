### get && install apk

* `get_apk.sh` - получаем файлы apk со смартфона №1
* `install_apk.sh` - устанавливаем apk на смартфон №2
* `packages` - список приложений для обработки (имя, id)
****

#### ADB: `community/android-tools`
* sudo adb start-server
* adb connect 192.168.1.XXX    -    *for network*
* adb device    -    *for check*
* 
* **run script**
*
* adb kill-server

