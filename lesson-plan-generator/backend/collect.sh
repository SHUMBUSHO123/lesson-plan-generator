#!/bin/bash
DJANGO_PATH="C:/Users/T/AppData/Local/Programs/Python/Python313/Lib/site-packages"
cp -rf static/css staticfiles/
cp -rf static/js staticfiles/
cp -rf static/icons staticfiles/
cp -rf static/images staticfiles/
cp -f static/manifest.json staticfiles/
cp -f static/sw.js staticfiles/
cp -rf "$DJANGO_PATH/django/contrib/admin/static/admin" staticfiles/
cp -rf "$DJANGO_PATH/rest_framework/static/rest_framework" staticfiles/
echo "All static files copied including admin and rest_framework!"
