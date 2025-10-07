#!/bin/bash -e

install -m 0755 -d /etc/apt/keyrings
install -m 0755 files/docker.asc "${ROOTFS_DIR}/etc/apt/keyrings/"
install -m 644 files/docker.list "${ROOTFS_DIR}/etc/apt/sources.list.d/"
sed -i "s/RELEASE/${RELEASE}/g" "${ROOTFS_DIR}/etc/apt/sources.list.d/docker.list"
sed -i "s/ARCH/$(dpkg --print-architecture)/g" "${ROOTFS_DIR}/etc/apt/sources.list.d/docker.list"

on_chroot << EOF
apt-get update
EOF
