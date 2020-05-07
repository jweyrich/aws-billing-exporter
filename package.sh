#!/bin/sh
zip -r9 deploy.zip *.py

for pythondir in $(echo venv/lib/*); do
  cd "${pythondir}/site-packages"
  zip -g "${OLDPWD}/deploy.zip" *
  cd "${OLDPWD}"
done
