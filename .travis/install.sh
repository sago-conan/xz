#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    brew update || brew update
    brew outdated pyenv || brew upgrade pyenv
    brew install pyenv-virtualenv

    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi

    pyenv install 3.7.3
    pyenv virtualenv 3.7.3 conan
    pyenv rehash
    pyenv activate conan
fi

pip install conan conan-package-tools --upgrade
conan user
