[app]
title = Perfume Lab
package.name = perfumelab
package.domain = org.bsaad

# projet courant
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,txt
# on démarre sur main.py
source.main = main.py

# versionnage
version = 0.1.0
android.numeric_version = 1

# dépendances
requirements = python3,kivy==2.3.0,kivymd==1.1.1,sqlite3

orientation = portrait
fullscreen = 0

# Android
android.api = 33
android.minapi = 24
android.ndk = 25c
