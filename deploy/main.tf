data "digitalocean_project" "default" {
  name = var.project
}

data "digitalocean_domain" "default" {
  name = var.domain
}

data "digitalocean_ssh_key" "keys" {
  for_each = toset(var.sshkeys)
  name     = each.value
}

locals {
  custom_image_nodes = { for k, n in var.nodes : k => n if n.custom_image != null }
}

# Imported into the node's own region only -- not shared across nodes,
# even if two nodes happen to use the same region.
resource "digitalocean_custom_image" "this" {
  for_each     = local.custom_image_nodes
  name         = "${each.value.custom_image.name}-${each.key}"
  url          = each.value.custom_image.url
  regions      = [each.value.region]
  distribution = "Unknown"
}

locals {
  image = {
    for k, n in var.nodes : k => n.custom_image != null ? digitalocean_custom_image.this[k].id : n.image
  }
}

resource "digitalocean_vpc" "private_network" {
  for_each = toset([for n in var.nodes : n.region])
  name     = "${terraform.workspace}-${each.key}-net"
  region   = each.key
}

# Prevent errors during vpc destroy: wait a few seconds after all
# droplets are destroyed before destroying the private networks.
resource "time_sleep" "vpc_destroy_delay" {
  depends_on       = [digitalocean_vpc.private_network]
  destroy_duration = "10s"
}

resource "digitalocean_droplet" "vps" {
  depends_on = [time_sleep.vpc_destroy_delay]
  for_each   = var.nodes
  name       = "${each.value.hostname}.${var.domain}"
  region     = each.value.region
  size       = each.value.size
  image      = local.image[each.key]
  vpc_uuid   = digitalocean_vpc.private_network[each.value.region].id
  ssh_keys = [
    for k in var.sshkeys : data.digitalocean_ssh_key.keys[k].id
  ]
}

resource "digitalocean_project_resources" "vps" {
  project   = data.digitalocean_project.default.id
  resources = [for k in keys(var.nodes) : digitalocean_droplet.vps[k].urn]
}

resource "digitalocean_record" "vps" {
  for_each = var.nodes
  domain   = data.digitalocean_domain.default.name
  type     = "A"
  name     = each.value.hostname
  value    = digitalocean_droplet.vps[each.key].ipv4_address
  ttl      = 300
}

output "droplet_ips" {
  description = "Public IPv4 address of each droplet, keyed by node key"
  value       = { for k, d in digitalocean_droplet.vps : k => d.ipv4_address }
}

output "fqdns" {
  description = "FQDN of each droplet, keyed by node key"
  value       = { for k, n in var.nodes : k => "${n.hostname}.${var.domain}" }
}
