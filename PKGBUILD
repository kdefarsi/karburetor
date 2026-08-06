# Maintainer: KDE Farsi Community
# Contributor: Sohrab Behdani <behdanisohrab@gmail.com>

pkgname=karburetor-git
pkgver=0.1
pkgrel=1
pkgdesc="A KDE Plasma Tor client — KDE port of Carburetor"
arch=('x86_64')
url="https://github.com/kdefarsi/karburetor"
license=('GPL-3.0-or-later')

depends=(
    'python'
    'pyside6'
    'kstatusnotifieritem'
    'python-stem'
    'python-pycountry'
    'python-pysocks'
    'kirigami'
    'kirigami-addons'
    'ki18n'
    'qt6-svg'
    'tor'
)

makedepends=(
    'git'
    'uv'
    'python-build'
    'python-installer'
)

provides=('karburetor')
conflicts=('karburetor')

source=("${pkgname}::git+https://github.com/kdefarsi/karburetor.git")
sha256sums=('SKIP')

build() {
    cd "${pkgname}"
    uv build --wheel --out-dir dist/
}

package() {
    cd "${pkgname}"
    python -m installer --destdir="${pkgdir}" dist/*.whl

    if [ -f "data/io.frama.tractor.karburetor.desktop" ]; then
        install -Dm644 "data/io.frama.tractor.karburetor.desktop" \
            "${pkgdir}/usr/share/applications/io.frama.tractor.karburetor.desktop"
    fi

    install -Dm644 \
        "src/karburetor/icons/hicolor/scalable/apps/karburetor.svg" \
        "${pkgdir}/usr/share/icons/hicolor/scalable/apps/karburetor.svg"

    install -Dm644 \
        "src/karburetor/icons/hicolor/scalable/apps/karburetor-symbolic.svg" \
        "${pkgdir}/usr/share/icons/hicolor/scalable/apps/karburetor-symbolic.svg"

    install -Dm644 LICENSE \
        "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
