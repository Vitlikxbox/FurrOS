# shellcheck shell=sh
# FurrOS: software rendering in VMs without usable 3D, for Wayland tilers (see
# /usr/lib/systemd/user-environment-generators/60-furros-vm-graphics, which decides)
if [ -e /etc/furros/vm-software-gl ]; then
    for kv in $(/usr/lib/systemd/user-environment-generators/60-furros-vm-graphics); do
        # shellcheck disable=SC2163  # kv is KEY=VALUE, exported as is
        export "$kv"
    done
    unset kv
fi
