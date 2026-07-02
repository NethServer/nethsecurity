# NethSecurity deploy

Basic OpenTofu config: create DO droplets (each with a public network and a private VPC network), point DNS at them.

## SSH keys

`sshkeys` (SSH key names already registered in your DO account) get attached to every droplet. This is required by the DO API whenever the image has no cloud-init/agent support — as with a custom OpenWrt/NethSecurity image — DO otherwise refuses to create the droplet, since it has no other way to hand you access to it. The image itself never reads or installs the key (no cloud-init to do so); log in with its own baked-in credentials instead.

## Usage

1.  Create `tofu.auto.tfvars` (see `tofu.auto.tfvars.example`):

        do_token = "secret"
        project  = "Aldo"
        domain   = "al.nethserver.net"
        sshkeys  = ["yourkey"]
        nodes = {
          "ns1" = {
            hostname = "ns1"
            region   = "ams3"
            size     = "s-1vcpu-2gb"
            custom_image = {
              name = "nethsecurity-8.7.2"
              url  = "https://updates.nethsecurity.nethserver.org/stable/8.7.2/targets/x86/64/nethsecurity-8.7.2-x86-64-generic-squashfs-combined-efi.img.gz"
            }
          }
        }

    `nodes` is a map of node key => droplet spec. Each entry creates one droplet (named `<hostname>.<domain>`), an A record for it, and (per region used) a VPC providing its private network. `size` is optional, default `s-1vcpu-2gb`; do not go below 2GB RAM.

2.  Init and apply:

    tofu init
    tofu apply

Outputs the IP and FQDN of every droplet in `nodes`, keyed by node key.

## Image

Each node sets exactly one of:

- `image`: an existing marketplace/snapshot image slug or ID.
- `custom_image`: import a custom image and use it — scoped to that node's own `region` only, even if another node shares the same region.

### Custom image

Imported from a URL (the DO image-import API only accepts a URL, no local upload):

    custom_image = {
      name = "nethsecurity-8.7.2"
      url  = "https://updates.nethsecurity.nethserver.org/stable/8.7.2/targets/x86/64/nethsecurity-8.7.2-x86-64-generic-squashfs-combined-efi.img.gz"
    }

Default images (x86/64, generic, squashfs-combined-efi):

| Version | URL |
|---|---|
| 8.7.2 | https://updates.nethsecurity.nethserver.org/stable/8.7.2/targets/x86/64/nethsecurity-8.7.2-x86-64-generic-squashfs-combined-efi.img.gz |
| 8.7.1 | https://updates.nethsecurity.nethserver.org/stable/8.7.1/targets/x86/64/nethsecurity-8.7.1-x86-64-generic-squashfs-combined-efi.img.gz |
