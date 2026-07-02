variable "project" {
  description = "DigitalOcean project name to attach the droplets to"
  type        = string
}

variable "domain" {
  description = "DNS domain to associate with the droplets"
  type        = string
}

variable "sshkeys" {
  description = <<-EOT
    DigitalOcean SSH key names (already registered in your account) to
    attach to every droplet. Required by the DO API when the image has no
    cloud-init/agent support (e.g. a custom OpenWrt/NethSecurity image) --
    DO refuses to create the droplet otherwise, since it has no other way
    to hand you access. OpenWrt itself never reads this key (no cloud-init
    to inject it); log in with the image's own baked-in credentials.
  EOT
  type        = list(string)
  default     = []
}

variable "nodes" {
  description = <<-EOT
    Map of node key => droplet spec. size must be 2GB RAM or more.
    Set exactly one of `image` / `custom_image`:
      - `image`: an existing marketplace/snapshot image slug or ID.
      - `custom_image`: import a custom image from a URL into this node's
        region only, and use it.
  EOT
  type = map(object({
    hostname = string
    region   = string
    size     = optional(string, "s-1vcpu-2gb")
    image    = optional(string)
    custom_image = optional(object({
      name = string
      url  = string
    }))
  }))
  default = {}
}
